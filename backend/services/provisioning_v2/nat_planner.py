"""
NAT Planner for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no route wiring
- no legacy provisioning changes

This planner produces NAT intent for client-to-internet connectivity.
"""

from __future__ import annotations

from enum import Enum
from ipaddress import ip_network
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from backend.services.provisioning_v2.address_planner import AddressPlan
from backend.services.provisioning_v2.topology_planner import TopologyPlan


class NATPlannerError(ValueError):
    """Raised when NAT intent cannot be safely planned."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class NATStrategy(str, Enum):
    MASQUERADE = "masquerade"
    SRC_NAT = "src_nat"
    NONE = "none"


class NATPlan(StrictModel):
    enabled: bool
    strategy: NATStrategy
    outbound_interface: str
    source_networks: List[str]
    excluded_networks: List[str] = Field(default_factory=list)
    hairpin_nat: bool = False
    warnings: List[str] = Field(default_factory=list)


def plan_nat(
    *,
    topology_plan: TopologyPlan,
    address_plan: AddressPlan,
    enabled: bool = True,
    strategy: NATStrategy = NATStrategy.MASQUERADE,
    excluded_networks: List[str] | None = None,
    hairpin_nat: bool = False,
) -> NATPlan:
    """
    Build NAT intent from topology and addressing plans.

    Does not generate RouterOS.
    """

    if not topology_plan.upstream_interface:
        raise NATPlannerError("topology upstream_interface is required")

    try:
        source_network = str(ip_network(address_plan.cidr, strict=False))
    except ValueError as exc:
        raise NATPlannerError(f"Invalid source network: {address_plan.cidr}") from exc

    exclusions: List[str] = []
    for network in excluded_networks or []:
        try:
            exclusions.append(str(ip_network(network, strict=False)))
        except ValueError as exc:
            raise NATPlannerError(f"Invalid excluded network: {network}") from exc

    warnings: List[str] = []

    if not enabled:
        return NATPlan(
            enabled=False,
            strategy=NATStrategy.NONE,
            outbound_interface=topology_plan.upstream_interface,
            source_networks=[],
            excluded_networks=exclusions,
            hairpin_nat=False,
            warnings=["NAT is disabled; hotspot clients may not reach the internet"],
        )

    if strategy == NATStrategy.NONE:
        raise NATPlannerError("NAT strategy NONE requires enabled=False")

    if topology_plan.upstream_interface in topology_plan.client_interfaces:
        raise NATPlannerError("Outbound interface must not be a client interface")

    if hairpin_nat:
        warnings.append("Hairpin NAT requested; renderer support must be verified")

    return NATPlan(
        enabled=True,
        strategy=strategy,
        outbound_interface=topology_plan.upstream_interface,
        source_networks=[source_network],
        excluded_networks=exclusions,
        hairpin_nat=hairpin_nat,
        warnings=warnings,
    )
