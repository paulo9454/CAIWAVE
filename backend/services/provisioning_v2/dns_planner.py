"""
DNS Planner for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no route wiring
- no legacy provisioning changes

This planner produces DNS intent for hotspot clients and captive portal support.
"""

from __future__ import annotations

from ipaddress import ip_address
from typing import Dict, List

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.provisioning_v2 import ProvisioningSnapshot
from backend.services.provisioning_v2.address_planner import AddressPlan
from backend.services.provisioning_v2.dhcp_planner import DHCPPlan


class DNSPlannerError(ValueError):
    """Raised when DNS intent cannot be safely planned."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DNSPlan(StrictModel):
    router_resolver_enabled: bool = True
    client_dns_servers: List[str]
    upstream_dns_servers: List[str]
    captive_dns_name: str
    static_records: Dict[str, str] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


def _validate_ip_list(values: List[str], field: str) -> List[str]:
    if not isinstance(values, list):
        raise DNSPlannerError(f"{field} must be a list")

    checked: List[str] = []
    for value in values:
        try:
            checked.append(str(ip_address(value)))
        except ValueError as exc:
            raise DNSPlannerError(f"Invalid DNS IP in {field}: {value}") from exc
    return checked


def plan_dns(
    *,
    snapshot: ProvisioningSnapshot,
    address_plan: AddressPlan,
    dhcp_plan: DHCPPlan,
    router_resolver_enabled: bool = True,
) -> DNSPlan:
    """
    Build DNS intent from snapshot, addressing, and DHCP plans.

    Does not configure RouterOS.
    """

    captive_dns_name = snapshot.hotspot.dns_name.strip()
    if not captive_dns_name:
        raise DNSPlannerError("hotspot DNS name is required")

    upstream = _validate_ip_list(
        snapshot.networking.router_dns_upstreams or [],
        "router_dns_upstreams",
    )

    client_dns_source = dhcp_plan.dns_servers or []
    if router_resolver_enabled and not client_dns_source:
        client_dns_source = snapshot.networking.client_dns_servers or []

    client_dns = _validate_ip_list(
        client_dns_source,
        "client_dns_servers",
    )

    warnings: List[str] = []

    if router_resolver_enabled:
        if address_plan.gateway_ip not in client_dns:
            warnings.append(
                "Router resolver enabled but gateway IP is not in DHCP client DNS servers"
            )
    elif not client_dns:
        raise DNSPlannerError("client DNS servers are required when router resolver is disabled")

    if not upstream and router_resolver_enabled:
        warnings.append("Router resolver enabled without explicit upstream DNS servers")

    static_records = {
        captive_dns_name: address_plan.gateway_ip,
    }

    return DNSPlan(
        router_resolver_enabled=router_resolver_enabled,
        client_dns_servers=client_dns or [address_plan.gateway_ip],
        upstream_dns_servers=upstream,
        captive_dns_name=captive_dns_name,
        static_records=static_records,
        warnings=warnings,
    )
