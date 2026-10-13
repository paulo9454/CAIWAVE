"""
Topology Planner for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no route wiring
- no legacy provisioning changes

This planner produces topology intent only. It does not create bridges,
configure IPs, assign DHCP, configure Hotspot, or render RouterOS.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.services.provisioning_v2.interface_capabilities import (
    InterfaceRoleHint,
)
from backend.services.provisioning_v2.interface_classification import (
    ClassifiedInterface,
    InterfaceClassificationLabel,
)


class TopologyPlannerError(ValueError):
    """Raised when topology cannot be safely planned."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class BridgeStrategy(str, Enum):
    CREATE = "create"
    REUSE = "reuse"
    NONE = "none"


class TopologyPlan(StrictModel):
    upstream_interface: str
    client_interfaces: List[str]
    bridge_strategy: BridgeStrategy
    bridge_name: Optional[str] = None
    reserved_interfaces: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


def _find_interface(
    interfaces: List[ClassifiedInterface],
    name: str,
) -> ClassifiedInterface | None:
    for interface in interfaces:
        if interface.name == name:
            return interface
    return None


def _is_client_eligible(interface: ClassifiedInterface) -> bool:
    return (
        not interface.disabled
        and interface.classification
        in {
            InterfaceClassificationLabel.PHYSICAL_ETHERNET,
            InterfaceClassificationLabel.PHYSICAL_WIRELESS,
            InterfaceClassificationLabel.LOGICAL_VLAN,
            InterfaceClassificationLabel.LOGICAL_BONDING,
        }
    )


def _is_upstream_eligible(interface: ClassifiedInterface) -> bool:
    return (
        not interface.disabled
        and interface.classification
        in {
            InterfaceClassificationLabel.PHYSICAL_ETHERNET,
            InterfaceClassificationLabel.LOGICAL_VLAN,
            InterfaceClassificationLabel.LOGICAL_BONDING,
            InterfaceClassificationLabel.LOGICAL_LTE,
            InterfaceClassificationLabel.LOGICAL_PPP,
        }
    )


def plan_topology(
    *,
    classified_interfaces: List[ClassifiedInterface],
    requested_wan_interface: str,
    requested_lan_interfaces: List[str],
    create_bridge: bool = True,
    bridge_name: str | None = "bridge-hotspot",
) -> TopologyPlan:
    """
    Plan WAN/client topology from classified interfaces and explicit request.

    The request remains authoritative. This module validates it and produces
    intent; it does not silently guess dangerous topology.
    """

    if not classified_interfaces:
        raise TopologyPlannerError("classified_interfaces is required")
    if not requested_wan_interface:
        raise TopologyPlannerError("requested_wan_interface is required")
    if not requested_lan_interfaces:
        raise TopologyPlannerError("requested_lan_interfaces is required")

    names = [item.name for item in classified_interfaces]
    if len(names) != len(set(names)):
        raise TopologyPlannerError("Duplicate classified interface names")

    wan = _find_interface(classified_interfaces, requested_wan_interface)
    if wan is None:
        raise TopologyPlannerError(
            f"Requested WAN interface not found: {requested_wan_interface}"
        )
    if not _is_upstream_eligible(wan):
        raise TopologyPlannerError(
            f"Requested WAN interface is not upstream eligible: {requested_wan_interface}"
        )

    normalized_lan = []
    for name in requested_lan_interfaces:
        if not name or name in normalized_lan:
            continue
        normalized_lan.append(name)

    if requested_wan_interface in normalized_lan:
        raise TopologyPlannerError("WAN interface must not also be a LAN interface")

    missing_lan = [
        name for name in normalized_lan if _find_interface(classified_interfaces, name) is None
    ]
    if missing_lan:
        raise TopologyPlannerError(
            f"Requested LAN interface(s) not found: {', '.join(missing_lan)}"
        )

    invalid_lan = [
        name
        for name in normalized_lan
        if not _is_client_eligible(_find_interface(classified_interfaces, name))
    ]
    if invalid_lan:
        raise TopologyPlannerError(
            f"Requested LAN interface(s) are not client eligible: {', '.join(invalid_lan)}"
        )

    warnings: List[str] = []
    existing_bridge = None
    if bridge_name:
        existing_bridge = _find_interface(classified_interfaces, bridge_name)

    if create_bridge:
        strategy = BridgeStrategy.REUSE if existing_bridge else BridgeStrategy.CREATE
        planned_bridge_name = bridge_name or "bridge-hotspot"
    else:
        strategy = BridgeStrategy.NONE
        planned_bridge_name = None
        if len(normalized_lan) > 1:
            raise TopologyPlannerError(
                "Multiple LAN interfaces require bridge creation or bridge reuse"
            )

    if existing_bridge and not create_bridge:
        warnings.append(
            f"Existing bridge {existing_bridge.name} detected but bridge creation is disabled"
        )

    reserved = [requested_wan_interface]

    return TopologyPlan(
        upstream_interface=requested_wan_interface,
        client_interfaces=normalized_lan,
        bridge_strategy=strategy,
        bridge_name=planned_bridge_name,
        reserved_interfaces=reserved,
        warnings=warnings,
    )
