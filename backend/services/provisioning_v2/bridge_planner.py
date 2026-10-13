"""
Bridge Planner for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no route wiring
- no legacy provisioning changes

This planner converts a TopologyPlan into bridge intent only.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.services.provisioning_v2.topology_planner import (
    BridgeStrategy,
    TopologyPlan,
)


class BridgePlannerError(ValueError):
    """Raised when bridge intent cannot be safely planned."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class BridgeAction(str, Enum):
    CREATE = "create"
    REUSE = "reuse"
    NONE = "none"


class BridgePlan(StrictModel):
    action: BridgeAction
    bridge_name: Optional[str] = None
    members: List[str] = Field(default_factory=list)
    existing_members: List[str] = Field(default_factory=list)
    excluded_interfaces: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


def plan_bridge(
    topology: TopologyPlan,
    existing_bridge_members: Optional[Dict[str, List[str]]] = None,
) -> BridgePlan:
    """
    Convert topology intent into bridge intent.

    REUSE requires an explicit snapshot of existing bridge membership.
    This function does not generate RouterOS commands.
    """

    if not topology.upstream_interface:
        raise BridgePlannerError("topology upstream_interface is required")

    if topology.upstream_interface in topology.client_interfaces:
        raise BridgePlannerError("upstream interface must not be a bridge member")

    members = []
    for item in topology.client_interfaces:
        if item and item not in members:
            members.append(item)

    if topology.bridge_strategy in {BridgeStrategy.CREATE, BridgeStrategy.REUSE}:
        if not topology.bridge_name:
            raise BridgePlannerError("bridge_name is required when bridge is used")
        if not members:
            raise BridgePlannerError("at least one bridge member is required")

        action = (
            BridgeAction.CREATE
            if topology.bridge_strategy == BridgeStrategy.CREATE
            else BridgeAction.REUSE
        )

        existing_members: List[str] = []
        normalized_membership = None

        if existing_bridge_members is not None:
            normalized_membership = {
                str(bridge): list(interfaces)
                for bridge, interfaces in existing_bridge_members.items()
            }

            if action == BridgeAction.CREATE and topology.bridge_name in normalized_membership:
                raise BridgePlannerError(
                    f"cannot create bridge that already exists: {topology.bridge_name}"
                )

            for member in members:
                owners = [
                    bridge
                    for bridge, interfaces in normalized_membership.items()
                    if member in interfaces
                ]
                if len(owners) > 1:
                    raise BridgePlannerError(
                        f"interface {member} belongs to multiple bridges"
                    )
                if owners and (
                    action == BridgeAction.CREATE
                    or topology.bridge_name not in owners
                ):
                    raise BridgePlannerError(
                        f"interface {member} belongs to another bridge: "
                        f"{', '.join(owners)}"
                    )

        if action == BridgeAction.REUSE:
            if normalized_membership is None:
                raise BridgePlannerError(
                    "verified existing bridge membership is required for REUSE"
                )

            target_members = normalized_membership.get(topology.bridge_name)
            if target_members is None:
                raise BridgePlannerError(
                    f"target bridge membership was not discovered: {topology.bridge_name}"
                )

            existing_members = [
                member for member in members if member in target_members
            ]

        return BridgePlan(
            action=action,
            bridge_name=topology.bridge_name,
            members=members,
            existing_members=existing_members,
            excluded_interfaces=[topology.upstream_interface],
            warnings=list(topology.warnings),
        )

    if topology.bridge_strategy == BridgeStrategy.NONE:
        if len(members) > 1:
            raise BridgePlannerError("bridge strategy none cannot have multiple members")
        return BridgePlan(
            action=BridgeAction.NONE,
            bridge_name=None,
            members=members,
            excluded_interfaces=[topology.upstream_interface],
            warnings=list(topology.warnings),
        )

    raise BridgePlannerError(f"unsupported bridge strategy: {topology.bridge_strategy}")
