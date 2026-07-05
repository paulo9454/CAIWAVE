"""
Address Planner for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no route wiring
- no legacy provisioning changes

This planner validates IP addressing intent for the hotspot/client segment.
"""

from __future__ import annotations

from ipaddress import ip_address, ip_network
from typing import Optional

from pydantic import BaseModel, ConfigDict

from backend.schemas.provisioning_v2 import ProvisioningSnapshot
from backend.services.provisioning_v2.bridge_planner import BridgePlan


class AddressPlannerError(ValueError):
    """Raised when address intent cannot be safely planned."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class AddressPlan(StrictModel):
    cidr: str
    gateway_ip: str
    target_interface: str
    dhcp_pool_start: str
    dhcp_pool_end: str
    network_address: str
    prefix_length: int
    warnings: list[str] = []


def plan_addressing(
    *,
    snapshot: ProvisioningSnapshot,
    bridge_plan: BridgePlan,
    target_interface: Optional[str] = None,
) -> AddressPlan:
    """
    Build addressing intent from snapshot networking data and bridge intent.

    Does not configure RouterOS.
    """

    cidr = snapshot.networking.hotspot_cidr
    gateway = snapshot.networking.hotspot_gateway
    pool_start = snapshot.networking.dhcp_pool_start
    pool_end = snapshot.networking.dhcp_pool_end

    try:
        network = ip_network(cidr, strict=False)
        gateway_ip = ip_address(gateway)
        start_ip = ip_address(pool_start)
        end_ip = ip_address(pool_end)
    except ValueError as exc:
        raise AddressPlannerError(f"Invalid IP addressing data: {exc}") from exc

    if gateway_ip not in network:
        raise AddressPlannerError("Gateway IP must be inside hotspot CIDR")

    if start_ip not in network or end_ip not in network:
        raise AddressPlannerError("DHCP pool must be inside hotspot CIDR")

    if int(start_ip) > int(end_ip):
        raise AddressPlannerError("DHCP pool start must be before or equal to end")

    if gateway_ip == start_ip or gateway_ip == end_ip:
        raise AddressPlannerError("Gateway IP must not equal DHCP pool boundary")

    if int(start_ip) <= int(gateway_ip) <= int(end_ip):
        raise AddressPlannerError("Gateway IP must not be inside DHCP pool")

    selected_interface = target_interface or bridge_plan.bridge_name or (
        bridge_plan.members[0] if bridge_plan.members else None
    )

    if not selected_interface:
        raise AddressPlannerError("Address target interface could not be determined")

    warnings: list[str] = []
    if network.prefixlen > 29:
        warnings.append("Hotspot CIDR is very small for client DHCP usage")

    return AddressPlan(
        cidr=str(network),
        gateway_ip=str(gateway_ip),
        target_interface=selected_interface,
        dhcp_pool_start=str(start_ip),
        dhcp_pool_end=str(end_ip),
        network_address=str(network.network_address),
        prefix_length=network.prefixlen,
        warnings=warnings,
    )
