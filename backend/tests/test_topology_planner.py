import pytest

from backend.services.provisioning_v2.interface_classification import (
    classify_interface_inventory,
)
from backend.services.provisioning_v2.interface_inventory import build_interface_inventory
from backend.services.provisioning_v2.topology_planner import (
    BridgeStrategy,
    TopologyPlannerError,
    plan_topology,
)


def classified(interfaces=None):
    inventory = build_interface_inventory(
        router_id="router-1",
        interfaces=interfaces
        or [
            {"name": "ether1"},
            {"name": "ether2"},
            {"name": "wlan1"},
            {"name": "bridge-hotspot"},
        ],
    )
    return classify_interface_inventory(inventory)


def test_plans_topology_with_existing_bridge_reuse():
    plan = plan_topology(
        classified_interfaces=classified(),
        requested_wan_interface="ether1",
        requested_lan_interfaces=["ether2", "wlan1"],
        create_bridge=True,
        bridge_name="bridge-hotspot",
    )

    assert plan.upstream_interface == "ether1"
    assert plan.client_interfaces == ["ether2", "wlan1"]
    assert plan.bridge_strategy == BridgeStrategy.REUSE
    assert plan.bridge_name == "bridge-hotspot"
    assert plan.reserved_interfaces == ["ether1"]


def test_plans_topology_with_bridge_creation():
    plan = plan_topology(
        classified_interfaces=classified([
            {"name": "ether1"},
            {"name": "ether2"},
            {"name": "wlan1"},
        ]),
        requested_wan_interface="ether1",
        requested_lan_interfaces=["ether2", "wlan1"],
        create_bridge=True,
        bridge_name="bridge-hotspot",
    )

    assert plan.bridge_strategy == BridgeStrategy.CREATE
    assert plan.bridge_name == "bridge-hotspot"


def test_single_lan_without_bridge_is_allowed():
    plan = plan_topology(
        classified_interfaces=classified([
            {"name": "ether1"},
            {"name": "ether2"},
        ]),
        requested_wan_interface="ether1",
        requested_lan_interfaces=["ether2"],
        create_bridge=False,
    )

    assert plan.bridge_strategy == BridgeStrategy.NONE
    assert plan.bridge_name is None


def test_multiple_lan_without_bridge_is_rejected():
    with pytest.raises(TopologyPlannerError):
        plan_topology(
            classified_interfaces=classified([
                {"name": "ether1"},
                {"name": "ether2"},
                {"name": "ether3"},
            ]),
            requested_wan_interface="ether1",
            requested_lan_interfaces=["ether2", "ether3"],
            create_bridge=False,
        )


def test_rejects_missing_wan():
    with pytest.raises(TopologyPlannerError):
        plan_topology(
            classified_interfaces=classified(),
            requested_wan_interface="ether9",
            requested_lan_interfaces=["ether2"],
        )


def test_rejects_wan_lan_overlap():
    with pytest.raises(TopologyPlannerError):
        plan_topology(
            classified_interfaces=classified(),
            requested_wan_interface="ether1",
            requested_lan_interfaces=["ether1", "ether2"],
        )


def test_rejects_missing_lan():
    with pytest.raises(TopologyPlannerError):
        plan_topology(
            classified_interfaces=classified(),
            requested_wan_interface="ether1",
            requested_lan_interfaces=["ether9"],
        )


def test_rejects_disabled_lan():
    with pytest.raises(TopologyPlannerError):
        plan_topology(
            classified_interfaces=classified([
                {"name": "ether1"},
                {"name": "ether2", "disabled": True},
            ]),
            requested_wan_interface="ether1",
            requested_lan_interfaces=["ether2"],
        )


def test_does_not_use_hardcoded_interface_names():
    plan = plan_topology(
        classified_interfaces=classified([
            {"name": "sfp1"},
            {"name": "ether5"},
            {"name": "vlan20", "parent": "ether5"},
        ]),
        requested_wan_interface="sfp1",
        requested_lan_interfaces=["ether5", "vlan20"],
        create_bridge=True,
        bridge_name="client-bridge",
    )

    assert plan.upstream_interface == "sfp1"
    assert plan.client_interfaces == ["ether5", "vlan20"]
    assert plan.bridge_name == "client-bridge"
