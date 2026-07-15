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
from backend.services.provisioning_v2.routeros_script_linter import (
    ProductionRouterOSLintContext,
    lint_production_routeros_script,
)
from backend.services.provisioning_v2.snapshot_builder import build_provisioning_snapshot
from backend.services.provisioning_v2.topology_planner import plan_topology


@dataclass(frozen=True)
class ProvisioningV2BuilderOutput:
    filename: str
    content: str
    content_type: str = "text/plain"


def _safe(name: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in str(name)).strip("-") or "router"


def _router_interfaces(router: dict) -> list[dict]:
    names = []
    wan = router.get("wan_interface", "ether1")
    if wan:
        names.append(wan)

    for item in router.get("lan_interfaces") or ["ether2"]:
        if item:
            names.append(item)

    unique = []
    for name in names:
        if name not in unique:
            unique.append(name)

    return [{"name": name} for name in unique]


def build_provisioning_v2_rsc_from_router(router: dict) -> ProvisioningV2BuilderOutput:
    validated = validate_production_router_input(router)

    router = {
        **router,
        "id": validated.router_id,
        "name": validated.router_name,
        "owner_id": validated.owner_id,
        "hotspot_id": validated.hotspot_id,
        "nas_identifier": validated.nas_identifier,
        "wan_interface": validated.wan_interface,
        "lan_interfaces": list(validated.lan_interfaces),
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
    hotspot_id = router.get("hotspot_id") or "hotspot-1"
    owner_id = router.get("owner_id") or "owner-1"

    router_input = {
        "id": router_id,
        "name": router.get("name", "CAIWAVE-Router"),
        "owner_id": owner_id,
        "hotspot_id": hotspot_id,
        "nas_identifier": router.get("nas_identifier", f"CAIWAVE-{router_id}"),
        "wan_interface": router.get("wan_interface", "ether1"),
        "lan_interfaces": router.get("lan_interfaces") or ["ether2"],
        "create_bridge": router.get("create_bridge", True),
        "bridge_name": router.get("bridge_name", "bridge-hotspot"),
        "effective_lan_interface": router.get("effective_lan_interface", router.get("bridge_name", "bridge-hotspot")),
        "mode": router.get("mode", "fresh"),
        "hotspot_cidr": router.get("hotspot_cidr", "10.10.0.0/24"),
        "hotspot_gateway": router.get("hotspot_gateway", "10.10.0.1"),
        "dhcp_pool": router.get("dhcp_pool", "10.10.0.10-10.10.0.254"),
        "dns_name": router.get("dns_name", "wifi.caiwave.com"),
    }
    hotspot_input = {
        "id": hotspot_id,
        "owner_id": owner_id,
    }
    config = {
        "radius_host": router.get(
            "radius_host",
            os.environ.get("RADIUS_HOST", "radius.caiwave.com"),
        ),
        "radius_secret_ref": router["radius_secret"],
        "portal_public_url": router.get("portal_public_url", os.environ.get("PUBLIC_URL", "https://caiwave.com")),
        "api_public_url": router.get("api_public_url", os.environ.get("API_PUBLIC_URL", "https://caiwave.com/api")),
        "heartbeat_url": router.get("heartbeat_url", os.environ.get("HEARTBEAT_URL", "https://caiwave.com/api/mikrotik-onboard/heartbeat")),
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
    bridge = plan_bridge(topology)
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
    )
    artifact = render_routeros_bundle(bundle=bundle)
    lint = lint_production_routeros_script(
        artifact.content,
        context=ProductionRouterOSLintContext(
            router_id=validated.router_id,
            hotspot_id=validated.hotspot_id,
            nas_identifier=validated.nas_identifier,
            captive_dns_name=validated.captive_dns_name,
            portal_public_url=validated.portal_public_url,
            radius_host=validated.radius_host,
            heartbeat_url=validated.heartbeat_url,
        ),
    )

    if not lint.valid:
        raise ValueError(
            "Provisioning Engine v2 generated an unsafe production "
            "RouterOS script: "
            + "; ".join(lint.errors)
        )

    return ProvisioningV2BuilderOutput(
        filename=f"{_safe(router_input['name'])}-{_safe(router_input['nas_identifier'])}.rsc",
        content=artifact.content,
    )
