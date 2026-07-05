"""
Firewall Planner for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no route wiring
- no legacy provisioning changes

This planner produces firewall policy intent from completed network and
service plans. It does not render RouterOS firewall rules.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.services.provisioning_v2.address_planner import AddressPlan
from backend.services.provisioning_v2.dns_planner import DNSPlan
from backend.services.provisioning_v2.hotspot_planner import HotspotPlan
from backend.services.provisioning_v2.nat_planner import NATPlan
from backend.services.provisioning_v2.portal_planner import PortalPlan
from backend.services.provisioning_v2.radius_planner import RadiusPlan
from backend.services.provisioning_v2.topology_planner import TopologyPlan


class FirewallPlannerError(ValueError):
    """Raised when firewall intent cannot be safely planned."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class FirewallChain(str, Enum):
    INPUT = "input"
    FORWARD = "forward"
    OUTPUT = "output"


class FirewallAction(str, Enum):
    ACCEPT = "accept"
    DROP = "drop"
    REJECT = "reject"


class FirewallRuleIntent(StrictModel):
    name: str
    chain: FirewallChain
    action: FirewallAction
    purpose: str
    source_network: Optional[str] = None
    destination_host: Optional[str] = None
    protocol: Optional[str] = None
    destination_port: Optional[int] = None


class FirewallPlan(StrictModel):
    default_input_policy: FirewallAction = FirewallAction.DROP
    default_forward_policy: FirewallAction = FirewallAction.DROP
    allow_established_related: bool = True
    drop_invalid: bool = True
    wan_interface: str
    client_networks: List[str]
    portal_hosts: List[str] = Field(default_factory=list)
    radius_hosts: List[str] = Field(default_factory=list)
    rules: List[FirewallRuleIntent] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


def plan_firewall(
    *,
    topology_plan: TopologyPlan,
    address_plan: AddressPlan,
    dns_plan: DNSPlan,
    nat_plan: NATPlan,
    hotspot_plan: HotspotPlan,
    portal_plan: PortalPlan,
    radius_plan: RadiusPlan,
    management_sources: List[str] | None = None,
) -> FirewallPlan:
    """
    Build firewall policy intent from completed plans.

    Does not generate RouterOS firewall filter/NAT commands.
    """

    if not topology_plan.upstream_interface:
        raise FirewallPlannerError("WAN/upstream interface is required")
    if not address_plan.cidr:
        raise FirewallPlannerError("client network CIDR is required")

    warnings: List[str] = []
    for plan in [dns_plan, nat_plan, hotspot_plan, portal_plan, radius_plan]:
        warnings.extend(getattr(plan, "warnings", []))

    rules: List[FirewallRuleIntent] = [
        FirewallRuleIntent(
            name="allow-established-related",
            chain=FirewallChain.INPUT,
            action=FirewallAction.ACCEPT,
            purpose="Allow established and related traffic",
        ),
        FirewallRuleIntent(
            name="drop-invalid",
            chain=FirewallChain.INPUT,
            action=FirewallAction.DROP,
            purpose="Drop invalid packets",
        ),
        FirewallRuleIntent(
            name="allow-client-dns",
            chain=FirewallChain.INPUT,
            action=FirewallAction.ACCEPT,
            purpose="Allow hotspot clients to query router DNS",
            source_network=address_plan.cidr,
            protocol="udp",
            destination_port=53,
        ),
        FirewallRuleIntent(
            name="allow-client-dhcp",
            chain=FirewallChain.INPUT,
            action=FirewallAction.ACCEPT,
            purpose="Allow DHCP service for hotspot clients",
            source_network=address_plan.cidr,
            protocol="udp",
            destination_port=67,
        ),
    ]

    if portal_plan.enabled:
        for host in portal_plan.walled_garden_hosts:
            rules.append(
                FirewallRuleIntent(
                    name=f"allow-portal-{host}",
                    chain=FirewallChain.FORWARD,
                    action=FirewallAction.ACCEPT,
                    purpose="Allow pre-auth captive portal or payment host",
                    source_network=address_plan.cidr,
                    destination_host=host,
                )
            )

    if radius_plan.enabled:
        rules.append(
            FirewallRuleIntent(
                name="allow-radius-auth",
                chain=FirewallChain.OUTPUT,
                action=FirewallAction.ACCEPT,
                purpose="Allow router to reach RADIUS authentication server",
                destination_host=radius_plan.auth_host,
                protocol="udp",
                destination_port=radius_plan.auth_port,
            )
        )
        if radius_plan.accounting_enabled:
            rules.append(
                FirewallRuleIntent(
                    name="allow-radius-accounting",
                    chain=FirewallChain.OUTPUT,
                    action=FirewallAction.ACCEPT,
                    purpose="Allow router to reach RADIUS accounting server",
                    destination_host=radius_plan.accounting_host,
                    protocol="udp",
                    destination_port=radius_plan.accounting_port,
                )
            )

    for source in management_sources or []:
        rules.append(
            FirewallRuleIntent(
                name=f"allow-management-{source}",
                chain=FirewallChain.INPUT,
                action=FirewallAction.ACCEPT,
                purpose="Allow approved management source",
                source_network=source,
            )
        )

    if not nat_plan.enabled:
        warnings.append("Firewall planned while NAT is disabled")

    return FirewallPlan(
        wan_interface=topology_plan.upstream_interface,
        client_networks=[address_plan.cidr],
        portal_hosts=list(portal_plan.walled_garden_hosts),
        radius_hosts=[radius_plan.auth_host] if radius_plan.enabled else [],
        rules=rules,
        warnings=warnings,
    )
