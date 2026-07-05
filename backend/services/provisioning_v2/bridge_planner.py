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
from typing import List, Optional

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
    excluded_interfaces: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


def plan_bridge(topology: TopologyPlan) -> BridgePlan:
    """
    Convert topology intent into bridge intent.

    Does not generate RouterOS and does not validate physical router state.
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

        return BridgePlan(
            action=action,
            bridge_name=topology.bridge_name,
            members=members,
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
