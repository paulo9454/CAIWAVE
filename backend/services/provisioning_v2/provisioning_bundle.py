"""
Provisioning Bundle Builder for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no route wiring
- no legacy provisioning changes

This module assembles snapshot + all validated plans into one immutable bundle.
The bundle is the input contract for future validation and RouterOS rendering.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.provisioning_v2 import ProvisioningSnapshot
from backend.services.provisioning_v2.address_planner import AddressPlan
from backend.services.provisioning_v2.bridge_planner import BridgePlan
from backend.services.provisioning_v2.dhcp_planner import DHCPPlan
from backend.services.provisioning_v2.dns_planner import DNSPlan
from backend.services.provisioning_v2.firewall_planner import FirewallPlan
from backend.services.provisioning_v2.hotspot_planner import HotspotPlan
from backend.services.provisioning_v2.nat_planner import NATPlan
from backend.services.provisioning_v2.portal_planner import PortalPlan
from backend.services.provisioning_v2.radius_planner import RadiusPlan
from backend.services.provisioning_v2.topology_planner import TopologyPlan


class ProvisioningBundleError(ValueError):
    """Raised when a provisioning bundle cannot be safely assembled."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ProvisioningBundle(StrictModel):
    bundle_id: str
    snapshot_id: str
    router_id: str
    hotspot_id: str
    generated_at: datetime
    engine_version: str
    checksum: str
    snapshot: ProvisioningSnapshot
    topology: TopologyPlan
    bridge: BridgePlan
    address: AddressPlan
    dhcp: DHCPPlan
    dns: DNSPlan
    nat: NATPlan
    hotspot: HotspotPlan
    portal: PortalPlan
    radius: RadiusPlan
    firewall: FirewallPlan
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def _checksum(data: Any) -> str:
    return hashlib.sha256(_stable_json(data).encode("utf-8")).hexdigest()


def build_provisioning_bundle(
    *,
    snapshot: ProvisioningSnapshot,
    topology: TopologyPlan,
    bridge: BridgePlan,
    address: AddressPlan,
    dhcp: DHCPPlan,
    dns: DNSPlan,
    nat: NATPlan,
    hotspot: HotspotPlan,
    portal: PortalPlan,
    radius: RadiusPlan,
    firewall: FirewallPlan,
) -> ProvisioningBundle:
    """
    Assemble an immutable provisioning bundle from validated plans.

    Does not render RouterOS.
    """

    if topology.upstream_interface in topology.client_interfaces:
        raise ProvisioningBundleError("WAN interface must not be a client interface")

    if address.target_interface != dhcp.target_interface:
        raise ProvisioningBundleError("Address and DHCP target interfaces must match")

    if hotspot.target_interface != address.target_interface:
        raise ProvisioningBundleError("Hotspot and address target interfaces must match")

    if hotspot.dns_name != dns.captive_dns_name:
        raise ProvisioningBundleError("Hotspot and DNS captive names must match")

    if portal.captive_dns_name != dns.captive_dns_name:
        raise ProvisioningBundleError("Portal and DNS captive names must match")

    if radius.enabled and not hotspot.use_radius:
        raise ProvisioningBundleError("RADIUS enabled while hotspot is not using RADIUS")

    if firewall.wan_interface != topology.upstream_interface:
        raise ProvisioningBundleError("Firewall WAN interface must match topology upstream")

    if address.cidr not in firewall.client_networks:
        raise ProvisioningBundleError("Firewall client networks must include address CIDR")

    warnings: List[str] = []
    for plan in [address, dhcp, dns, nat, hotspot, portal, radius, firewall]:
        warnings.extend(getattr(plan, "warnings", []))

    bundle_id = f"bundle:{snapshot.snapshot_id}"

    checksum_payload = {
        "snapshot_id": snapshot.snapshot_id,
        "router_id": snapshot.router_id,
        "topology": topology.model_dump(mode="json"),
        "bridge": bridge.model_dump(mode="json"),
        "address": address.model_dump(mode="json"),
        "dhcp": dhcp.model_dump(mode="json"),
        "dns": dns.model_dump(mode="json"),
        "nat": nat.model_dump(mode="json"),
        "hotspot": hotspot.model_dump(mode="json"),
        "portal": portal.model_dump(mode="json"),
        "radius": radius.model_dump(mode="json"),
        "firewall": firewall.model_dump(mode="json"),
    }

    return ProvisioningBundle(
        bundle_id=bundle_id,
        snapshot_id=snapshot.snapshot_id,
        router_id=snapshot.router_id,
        hotspot_id=snapshot.hotspot_id,
        generated_at=datetime.now(timezone.utc),
        engine_version=snapshot.versioning.engine_version,
        checksum=_checksum(checksum_payload),
        snapshot=snapshot,
        topology=topology,
        bridge=bridge,
        address=address,
        dhcp=dhcp,
        dns=dns,
        nat=nat,
        hotspot=hotspot,
        portal=portal,
        radius=radius,
        firewall=firewall,
        warnings=warnings,
        metadata={
            "bundle_contract_version": "1.0",
            "routeros_rendered": False,
        },
    )
