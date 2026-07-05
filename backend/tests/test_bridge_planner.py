import pytest

from backend.services.provisioning_v2.bridge_planner import (
    BridgeAction,
    BridgePlannerError,
    plan_bridge,
)
from backend.services.provisioning_v2.topology_planner import BridgeStrategy, TopologyPlan


def topology(strategy=BridgeStrategy.CREATE, members=None, bridge_name="bridge-hotspot"):
    return TopologyPlan(
        upstream_interface="ether1",
        client_interfaces=members or ["ether2", "wlan1"],
        bridge_strategy=strategy,
        bridge_name=bridge_name,
        warnings=[],
    )


def test_plans_bridge_creation():
    plan = plan_bridge(topology(BridgeStrategy.CREATE))

    assert plan.action == BridgeAction.CREATE
    assert plan.bridge_name == "bridge-hotspot"
    assert plan.members == ["ether2", "wlan1"]
    assert plan.excluded_interfaces == ["ether1"]


def test_plans_bridge_reuse():
    plan = plan_bridge(topology(BridgeStrategy.REUSE))

    assert plan.action == BridgeAction.REUSE
    assert plan.bridge_name == "bridge-hotspot"


def test_plans_no_bridge_for_single_member():
    plan = plan_bridge(
        topology(
            strategy=BridgeStrategy.NONE,
            members=["ether2"],
            bridge_name=None,
        )
    )

    assert plan.action == BridgeAction.NONE
    assert plan.bridge_name is None
    assert plan.members == ["ether2"]


def test_rejects_no_bridge_with_multiple_members():
    with pytest.raises(BridgePlannerError):
        plan_bridge(topology(strategy=BridgeStrategy.NONE, members=["ether2", "ether3"]))


def test_rejects_upstream_as_member():
    with pytest.raises(BridgePlannerError):
        plan_bridge(topology(members=["ether1", "ether2"]))


def test_rejects_missing_bridge_name_when_bridge_used():
    with pytest.raises(BridgePlannerError):
        plan_bridge(topology(strategy=BridgeStrategy.CREATE, bridge_name=None))


def test_deduplicates_members_preserving_order():
    plan = plan_bridge(topology(members=["ether2", "ether2", "wlan1"]))

    assert plan.members == ["ether2", "wlan1"]


def test_preserves_warnings():
    topo = topology()
    topo = topo.model_copy(update={"warnings": ["example warning"]})

    plan = plan_bridge(topo)

    assert plan.warnings == ["example warning"]
