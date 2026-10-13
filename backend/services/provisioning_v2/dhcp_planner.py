"""
DHCP Planner for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no route wiring
- no legacy provisioning changes

This planner produces DHCP service intent from an AddressPlan.
"""

from __future__ import annotations

from enum import Enum
from ipaddress import ip_address
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.services.provisioning_v2.address_planner import AddressPlan


class DHCPPlannerError(ValueError):
    """Raised when DHCP intent cannot be safely planned."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DHCPAuthoritativeMode(str, Enum):
    YES = "yes"
    NO = "no"
    AFTER_2SEC_DELAY = "after_2sec_delay"


class DHCPPlan(StrictModel):
    server_name: str
    pool_name: str
    target_interface: str
    pool_start: str
    pool_end: str
    gateway_ip: str
    network_cidr: str
    lease_time: str = "1h"
    authoritative: DHCPAuthoritativeMode = DHCPAuthoritativeMode.AFTER_2SEC_DELAY
    dns_servers: List[str] = Field(default_factory=list)
    reservations: List[dict] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


def plan_dhcp(
    *,
    address_plan: AddressPlan,
    server_name: str = "caiwave-dhcp-hotspot",
    pool_name: str = "caiwave-pool-hotspot",
    lease_time: str = "1h",
    dns_servers: Optional[List[str]] = None,
    authoritative: DHCPAuthoritativeMode = DHCPAuthoritativeMode.AFTER_2SEC_DELAY,
) -> DHCPPlan:
    """
    Build DHCP service intent from an AddressPlan.

    Does not configure RouterOS.
    """

    if not server_name:
        raise DHCPPlannerError("server_name is required")
    if not pool_name:
        raise DHCPPlannerError("pool_name is required")
    if not address_plan.target_interface:
        raise DHCPPlannerError("address_plan target_interface is required")

    start_ip = ip_address(address_plan.dhcp_pool_start)
    end_ip = ip_address(address_plan.dhcp_pool_end)
    gateway_ip = ip_address(address_plan.gateway_ip)

    if int(start_ip) > int(end_ip):
        raise DHCPPlannerError("DHCP pool start must be before or equal to end")

    if int(start_ip) <= int(gateway_ip) <= int(end_ip):
        raise DHCPPlannerError("Gateway IP must not be inside DHCP pool")

    warnings = list(address_plan.warnings)
    planned_dns = list(dns_servers or [address_plan.gateway_ip])

    if not planned_dns:
        warnings.append("No DNS servers defined for DHCP clients")

    return DHCPPlan(
        server_name=server_name,
        pool_name=pool_name,
        target_interface=address_plan.target_interface,
        pool_start=address_plan.dhcp_pool_start,
        pool_end=address_plan.dhcp_pool_end,
        gateway_ip=address_plan.gateway_ip,
        network_cidr=address_plan.cidr,
        lease_time=lease_time,
        authoritative=authoritative,
        dns_servers=planned_dns,
        warnings=warnings,
    )
