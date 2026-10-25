"""
Adapter from existing MikroTik builder router dicts to Provisioning Engine v2.

Safety:
- no database access
- no route wiring
- no legacy generator mutation

This lets the existing download flow use the new Provisioning Engine v2 while
preserving the current builder API.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

from backend.services.provisioning_v2.address_planner import plan_addressing
from backend.services.provisioning_v2.bridge_planner import plan_bridge
from backend.services.provisioning_v2.dhcp_planner import plan_dhcp
from backend.services.provisioning_v2.dns_planner import plan_dns
from backend.services.provisioning_v2.firewall_planner import plan_firewall
from backend.services.provisioning_v2.hotspot_planner import plan_hotspot
from backend.services.provisioning_v2.interface_classification import classify_interface_inventory
from backend.services.provisioning_v2.interface_inventory import build_interface_inventory
from backend.services.provisioning_v2.nat_planner import plan_nat
from backend.services.provisioning_v2.portal_planner import plan_portal
from backend.services.provisioning_v2.production_input import (
    validate_production_router_input,
)
from backend.services.provisioning_v2.provisioning_bundle import build_provisioning_bundle
from backend.services.provisioning_v2.radius_planner import plan_radius
from backend.services.provisioning_v2.routeros_render_orchestrator import render_routeros_bundle
from backend.services.provisioning_v2.routeros_renderer_contracts import (
    build_render_context,
    default_routeros_section_order,
    RenderStatus,
    RouterOSRenderedArtifact,
    RouterOSRenderedSection,
    RouterOSSectionName,
)

from backend.services.provisioning_v2.routeros_discovery_renderer import (
    render_discovery_script,
)
from backend.services.provisioning_v2.routeros_control_renderer import (
    render_control_bootstrap,
)
from backend.services.provisioning_v2.routeros_command_builder import (
    join_script,
)
from backend.services.provisioning_v2.routeros_script_linter import (
    ProductionRouterOSLintContext,
    lint_production_routeros_script,
)
from backend.services.provisioning_v2.snapshot_builder import build_provisioning_snapshot
from backend.services.provisioning_v2.topology_planner import plan_topology

from backend.services.provisioning_v2.router_capabilities import (
    RouterCapabilityFacts,
)
from backend.services.provisioning_v2.wireless_planner import plan_wireless

from backend.services.provisioning_v2.provisioning_intent import (
    ProvisioningIntent,
)
from backend.services.provisioning_v2.provisioning_plan import (
    ProvisioningPlan,
    build_provisioning_plan,
)

@dataclass(frozen=True)
class ProvisioningV2BuilderOutput:
    filename: str
    content: str
    content_type: str = "text/plain"


def _safe(name: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in str(name)).strip("-") or "router"

def build_discovery_bootstrap(
    *,
    discovery_url: str,
    nas_identifier: str,
    control_secret: str,
) -> RouterOSRenderedSection:

    """
    Build the observational-only RouterOS discovery bootstrap.

    This path deliberately does not require or infer WAN/LAN topology.
    It only collects router facts and sends them to CAIWAVE discovery.
    """
    return render_discovery_script(
        discovery_url=discovery_url,
        nas_identifier=nas_identifier,
        control_secret=control_secret,
    )

def build_onboarding_bootstrap(
    *,
    discovery_url: str,
    heartbeat_url: str,
    nas_identifier: str,
    control_secret: str,
) -> RouterOSRenderedSection:
    """
    Build the single CAIWAVE installer bootstrap.

    The bootstrap first sends observational router discovery to CAIWAVE,
    then installs and starts the persistent CAIWAVE control agent.

    It does not make WAN/LAN assumptions or perform provisioning itself.
    """
    discovery_section = build_discovery_bootstrap(
        discovery_url=discovery_url,
        nas_identifier=nas_identifier,
        control_secret=control_secret,
    )

    control_section = render_control_bootstrap(
        heartbeat_url=heartbeat_url,
        nas_identifier=nas_identifier,
        control_secret=control_secret,
    )

    content = join_script(
        [
            discovery_section.content,
            control_section.content,
        ]
    )

    checksum = hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()

    return RouterOSRenderedSection(
        name=RouterOSSectionName.SCHEDULERS,
        status=RenderStatus.RENDERED,
        content=content,
        checksum=checksum,
        warnings=[
            *discovery_section.warnings,
            *control_section.warnings,
        ],
    )


def _router_interfaces(router: dict) -> list[dict]:
    """
    Build the interface inventory from verified topology only.

    Production provisioning must never invent physical interface names.
    WAN/LAN topology must already have been established by registration
    input or router discovery before this function is called.
    """
    wan = router.get("wan_interface")
    lan_interfaces = router.get("lan_interfaces")

    if not isinstance(wan, str) or not wan.strip():
        raise ValueError(
            "Verified WAN interface is required before provisioning"
        )

    if not isinstance(lan_interfaces, (list, tuple)) or not lan_interfaces:
        raise ValueError(
            "Verified LAN interfaces are required before provisioning"
        )

    names = [wan.strip()]
    for item in lan_interfaces:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(
                "Verified LAN interfaces must contain non-empty names"
            )
        names.append(item.strip())

    unique = []
    for name in names:
        if name not in unique:
            unique.append(name)

    return [{"name": name} for name in unique]

def _apply_wireless_capability(
    router: dict,
    lan_interfaces: list[str],
) -> tuple[list[str], object | None]:
    """
    Add verified wireless interfaces to the client topology only when
    wireless provisioning has explicitly been requested.
    """

    if not bool(router.get("wifi_enabled", False)):
        return list(lan_interfaces), None

    discovery = router.get("discovery") or {}
    capabilities_data = discovery.get("capabilities")

    if not capabilities_data:
        raise ValueError(
            "Wi-Fi provisioning was requested but verified router discovery "
            "capabilities are unavailable"
        )

    capabilities = RouterCapabilityFacts.model_validate(
        capabilities_data
    )

    if not capabilities.supports_wireless:
        raise ValueError(
            "Wi-Fi provisioning was requested but the discovered router "
            "does not support wireless"
        )

    wireless_interfaces = list(capabilities.wireless_interfaces)

    if not wireless_interfaces:
        raise ValueError(
            "Wi-Fi provisioning was requested but no wireless interfaces "
            "were discovered"
        )

    normalized = list(lan_interfaces)

    for interface_name in wireless_interfaces:
        if interface_name not in normalized:
            normalized.append(interface_name)

    ssid = str(router.get("wifi_ssid") or "CAIWAVE").strip()

    if not ssid:
        raise ValueError("wifi_ssid cannot be blank when Wi-Fi is enabled")

    wireless_plan = plan_wireless(
        capabilities=capabilities,
        ssid=ssid,
    )

    return normalized, wireless_plan

def _prepare_intent_aware_router(
    router: dict,
    intent: ProvisioningIntent,
) -> tuple[dict, ProvisioningPlan]:
    discovery = router.get("discovery") or {}
    capabilities_data = discovery.get("capabilities")
    topology_data = discovery.get("topology")

    if not capabilities_data:
        raise ValueError(
            "Provisioning intent requires verified router discovery capabilities"
        )

    if not topology_data:
        raise ValueError(
            "Provisioning intent requires verified router discovery topology"
        )

    capabilities = RouterCapabilityFacts.model_validate(
        capabilities_data
    )

    discovered_wan = str(
        topology_data.get("wan_interface") or ""
    ).strip()

    discovered_lan = [
        str(item).strip()
        for item in (
            topology_data.get("client_interfaces") or []
        )
        if str(item).strip()
    ]

    if not discovered_wan:
        raise ValueError(
            "Verified discovery topology does not contain a WAN interface"
        )

    if not discovered_lan:
        raise ValueError(
            "Verified discovery topology does not contain client interfaces"
        )

    plan = build_provisioning_plan(
        capabilities=capabilities,
        intent=intent,
        requested_wan_interface=discovered_wan,
        requested_wired_interfaces=discovered_lan,
    )

    prepared = {
        **router,
        "wan_interface": plan.wan_interface,
        "lan_interfaces": list(plan.client_interfaces),
        "wifi_enabled": plan.wifi_enabled,
        "wifi_ssid": plan.wifi_ssid,
    }

    return prepared, plan

def build_provisioning_v2_artifact_from_router(
    router: dict,
    provisioning_intent: ProvisioningIntent | None = None,
    control_secret: str | None = None,
) -> RouterOSRenderedArtifact:

    if provisioning_intent is not None:
        router, provisioning_plan = _prepare_intent_aware_router(
            router,
            provisioning_intent,
        )
    else:
        provisioning_plan = None

    validated = validate_production_router_input(router)

    if provisioning_plan is not None:
        effective_lan_interfaces = list(
            provisioning_plan.client_interfaces
        )

        wireless_plan = None

        if provisioning_plan.wifi_enabled:
            capabilities = RouterCapabilityFacts.model_validate(
                (router.get("discovery") or {}).get("capabilities")
            )

            wireless_plan = plan_wireless(
                capabilities=capabilities,
                ssid=provisioning_plan.wifi_ssid,
            )
    else:
        effective_lan_interfaces, wireless_plan = (
            _apply_wireless_capability(
                router,
                list(validated.lan_interfaces),
            )
        )

    router = {
        **router,
        "id": validated.router_id,
        "name": validated.router_name,
        "owner_id": validated.owner_id,
        "hotspot_id": validated.hotspot_id,
        "nas_identifier": validated.nas_identifier,
        "wan_interface": validated.wan_interface,
        "lan_interfaces": effective_lan_interfaces,
        "create_bridge": validated.create_bridge,
        "bridge_name": validated.bridge_name,
        "hotspot_cidr": validated.hotspot_cidr,
        "hotspot_gateway": validated.hotspot_gateway,
        "dhcp_pool": validated.dhcp_pool,
        "dns_name": validated.captive_dns_name,
        "radius_host": validated.radius_host,
        "radius_secret": validated.radius_secret,
        "portal_public_url": validated.portal_public_url,
        "api_public_url": validated.api_public_url,
        "heartbeat_url": validated.heartbeat_url,
    }

    router_id = validated.router_id
    hotspot_id = router["hotspot_id"]
    owner_id = router["owner_id"]

    router_input = {
        "id": router_id,
        "name": router["name"],
        "owner_id": owner_id,
        "hotspot_id": hotspot_id,
        "nas_identifier": router["nas_identifier"],
        "wan_interface": router["wan_interface"],
        "lan_interfaces": list(router["lan_interfaces"]),
        "create_bridge": router["create_bridge"],
        "bridge_name": router["bridge_name"],
        "effective_lan_interface": router["effective_lan_interface"],
        "mode": router["mode"],
        "hotspot_cidr": router["hotspot_cidr"],
        "hotspot_gateway": router["hotspot_gateway"],
        "dhcp_pool": router["dhcp_pool"],
        "dns_name": router["dns_name"],
    }
    hotspot_input = {
        "id": hotspot_id,
        "owner_id": owner_id,
    }
    config = {
        "radius_host": router["radius_host"],
        "radius_secret_ref": router["radius_secret"],
        "portal_public_url": router["portal_public_url"],
        "api_public_url": router["api_public_url"],
        "heartbeat_url": router["heartbeat_url"],
        "snapshot_id": router.get("snapshot_id"),
        "router_dns_upstreams": router.get("router_dns_upstreams", ["1.1.1.1"]),
        "client_dns_servers": router.get("client_dns_servers", [router_input["hotspot_gateway"]]),
    }

    snapshot = build_provisioning_snapshot(router_input, hotspot_input, config)
    inventory = build_interface_inventory(
        router_id=snapshot.router_id,
        interfaces=_router_interfaces(router_input),
    )
    classified = classify_interface_inventory(inventory)
    topology = plan_topology(
        classified_interfaces=classified,
        requested_wan_interface=snapshot.topology.wan_interface,
        requested_lan_interfaces=snapshot.topology.lan_interfaces,
        create_bridge=snapshot.topology.create_bridge,
        bridge_name=snapshot.topology.bridge_name,
    )
    discovery = router.get("discovery") or {}
    discovery_snapshot = discovery.get("snapshot") or {}
    discovered_bridge_ports = discovery_snapshot.get("bridge_ports")

    existing_bridge_members = None
    if isinstance(discovered_bridge_ports, list):
        membership = {}
        for port in discovered_bridge_ports:
            if not isinstance(port, dict):
                raise ValueError("Invalid discovered bridge-port record")

            bridge_name = str(
                port.get("bridge_name") or port.get("bridge") or ""
            ).strip()
            interface_name = str(
                port.get("interface_name") or port.get("interface") or ""
            ).strip()

            if not bridge_name or not interface_name:
                raise ValueError("Incomplete discovered bridge-port record")

            membership.setdefault(bridge_name, []).append(interface_name)

        existing_bridge_members = membership

    bridge = plan_bridge(
        topology,
        existing_bridge_members=existing_bridge_members,
    )
    address = plan_addressing(snapshot=snapshot, bridge_plan=bridge)
    dhcp = plan_dhcp(address_plan=address, dns_servers=snapshot.networking.client_dns_servers)
    dns = plan_dns(snapshot=snapshot, address_plan=address, dhcp_plan=dhcp)
    nat = plan_nat(topology_plan=topology, address_plan=address)
    hotspot_plan = plan_hotspot(
        snapshot=snapshot,
        bridge_plan=bridge,
        address_plan=address,
        dhcp_plan=dhcp,
        dns_plan=dns,
        nat_plan=nat,
    )
    portal = plan_portal(
        snapshot=snapshot,
        hotspot_plan=hotspot_plan,
        dns_plan=dns,
        payment_provider_hosts=router.get("payment_provider_hosts", ["checkout.paystack.com"]),
        asset_hosts=router.get("asset_hosts", []),
    )
    radius = plan_radius(snapshot=snapshot, hotspot_plan=hotspot_plan)
    firewall = plan_firewall(
        topology_plan=topology,
        address_plan=address,
        dns_plan=dns,
        nat_plan=nat,
        hotspot_plan=hotspot_plan,
        portal_plan=portal,
        radius_plan=radius,
    )
    bundle = build_provisioning_bundle(
        snapshot=snapshot,
        topology=topology,
        bridge=bridge,
        address=address,
        dhcp=dhcp,
        dns=dns,
        nat=nat,
        hotspot=hotspot_plan,
        portal=portal,
        radius=radius,
        firewall=firewall,
        wireless=wireless_plan,
    )

    # Discovery is a separate observational bootstrap artifact.
    # It must never be embedded in the final production provisioning script.
    # Include heartbeat and confirmation scripts, which use the router-local
    # credential initialized by the separate control bootstrap.
    section_order = default_routeros_section_order()
    section_order.insert(
        section_order.index(RouterOSSectionName.VALIDATION),
        RouterOSSectionName.SCHEDULERS,
    )
    render_context = build_render_context(section_order=section_order)

    # The immutable production artifact must not contain the plaintext
    # control secret.
    artifact = render_routeros_bundle(
        bundle=bundle,
        context=render_context,
    )
    lint = lint_production_routeros_script(
        artifact.content,
        context=ProductionRouterOSLintContext(
            router_id=validated.router_id,
            hotspot_id=validated.hotspot_id,
            nas_identifier=validated.nas_identifier,
            captive_dns_name=validated.captive_dns_name,
            portal_public_url=validated.portal_public_url,
            radius_host=validated.radius_host,
        ),
    )

    if not lint.valid:
        raise ValueError(
            "Provisioning Engine v2 generated an unsafe production "
            "RouterOS script: "
            + "; ".join(lint.errors)
        )

    return artifact

def build_provisioning_v2_rsc_from_router(
    router: dict,
    provisioning_intent: ProvisioningIntent | None = None,
    control_secret: str | None = None,
) -> ProvisioningV2BuilderOutput:
    artifact = build_provisioning_v2_artifact_from_router(
        router,
        provisioning_intent=provisioning_intent,
        control_secret=control_secret,
    )

    return ProvisioningV2BuilderOutput(
        filename=f"{_safe(router['name'])}-{_safe(router['nas_identifier'])}.rsc",
        content=artifact.content,
    )
