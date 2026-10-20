"""
Hotspot Planner for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no route wiring
- no legacy provisioning changes

This planner produces Hotspot service intent for captive access.
"""

from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.provisioning_v2 import ProvisioningSnapshot
from backend.services.provisioning_v2.address_planner import AddressPlan
from backend.services.provisioning_v2.bridge_planner import BridgePlan
from backend.services.provisioning_v2.dhcp_planner import DHCPPlan
from backend.services.provisioning_v2.dns_planner import DNSPlan
from backend.services.provisioning_v2.nat_planner import NATPlan


class HotspotPlannerError(ValueError):
    """Raised when Hotspot intent cannot be safely planned."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class HotspotAuthMode(str, Enum):
    RADIUS = "radius"
    LOCAL = "local"
    DISABLED = "disabled"


class HotspotPlan(StrictModel):
    enabled: bool = True
    server_name: str
    profile_name: str
    target_interface: str
    address_pool_name: str
    dns_name: str
    auth_mode: HotspotAuthMode = HotspotAuthMode.RADIUS
    login_methods: List[str] = Field(default_factory=list)
    use_radius: bool = True
    accounting_enabled: bool = True
    warnings: List[str] = Field(default_factory=list)


def plan_hotspot(
    *,
    snapshot: ProvisioningSnapshot,
    bridge_plan: BridgePlan,
    address_plan: AddressPlan,
    dhcp_plan: DHCPPlan,
    dns_plan: DNSPlan,
    nat_plan: NATPlan,
    auth_mode: HotspotAuthMode = HotspotAuthMode.RADIUS,
) -> HotspotPlan:
    """
    Build Hotspot service intent from prior planning outputs.

    Does not configure RouterOS or generate login pages.
    """

    if not snapshot.hotspot.server_name:
        raise HotspotPlannerError("hotspot server_name is required")
    if not snapshot.hotspot.profile_name:
        raise HotspotPlannerError("hotspot profile_name is required")
    if not address_plan.target_interface:
        raise HotspotPlannerError("address target interface is required")
    if not dhcp_plan.pool_name:
        raise HotspotPlannerError("DHCP pool name is required")
    if not dns_plan.captive_dns_name:
        raise HotspotPlannerError("captive DNS name is required")

    if address_plan.target_interface != dhcp_plan.target_interface:
        raise HotspotPlannerError("address and DHCP target interfaces must match")

    if dns_plan.captive_dns_name != snapshot.hotspot.dns_name:
        raise HotspotPlannerError("DNS plan captive name must match snapshot hotspot DNS name")

    warnings: List[str] = []
    warnings.extend(address_plan.warnings)
    warnings.extend(dhcp_plan.warnings)
    warnings.extend(dns_plan.warnings)
    warnings.extend(nat_plan.warnings)

    if not nat_plan.enabled:
        warnings.append("NAT is disabled; authenticated clients may not reach internet")

    use_radius = auth_mode == HotspotAuthMode.RADIUS
    accounting_enabled = use_radius

    if auth_mode == HotspotAuthMode.DISABLED:
        warnings.append("Hotspot authentication is disabled")

    login_methods = list(snapshot.hotspot.login_methods or [])
    if not login_methods and auth_mode != HotspotAuthMode.DISABLED:
        login_methods = ["http-pap"]

    return HotspotPlan(
        enabled=auth_mode != HotspotAuthMode.DISABLED,
        server_name=snapshot.hotspot.server_name,
        profile_name=snapshot.hotspot.profile_name,
        target_interface=address_plan.target_interface,
        address_pool_name=dhcp_plan.pool_name,
        dns_name=dns_plan.captive_dns_name,
        auth_mode=auth_mode,
        login_methods=login_methods,
        use_radius=use_radius,
        accounting_enabled=accounting_enabled,
        warnings=warnings,
    )
