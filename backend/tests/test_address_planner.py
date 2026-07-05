import pytest

from backend.services.provisioning_v2.address_planner import (
    AddressPlannerError,
    plan_addressing,
)
from backend.services.provisioning_v2.bridge_planner import plan_bridge
from backend.services.provisioning_v2.interface_classification import classify_interface_inventory
from backend.services.provisioning_v2.interface_inventory import build_interface_inventory
from backend.services.provisioning_v2.snapshot_builder import build_provisioning_snapshot
from backend.services.provisioning_v2.topology_planner import plan_topology


def build_snapshot(cidr="10.10.0.0/24", gateway="10.10.0.1", pool="10.10.0.10-10.10.0.254"):
    router = {
        "id": "router-1",
        "name": "GOODlife",
        "owner_id": "owner-1",
        "hotspot_id": "hotspot-1",
        "nas_identifier": "CAIWAVE-GOODLIFE",
        "wan_interface": "ether1",
        "lan_interfaces": ["ether2", "wlan1"],
        "create_bridge": True,
        "bridge_name": "bridge-hotspot",
        "effective_lan_interface": "bridge-hotspot",
        "mode": "fresh",
        "hotspot_cidr": cidr,
        "hotspot_gateway": gateway,
        "dhcp_pool": pool,
        "dns_name": "wifi.caiwave.com",
    }
    hotspot = {"id": "hotspot-1", "owner_id": "owner-1"}
    config = {
        "radius_host": "radius.caiwave.com",
        "portal_public_url": "https://caiwave.com/portal",
        "api_public_url": "https://caiwave.com/api",
        "heartbeat_url": "https://caiwave.com/api/mikrotik-onboard/heartbeat",
    }
    return build_provisioning_snapshot(router, hotspot, config)


def bridge_plan(snapshot):
    inventory = build_interface_inventory(
        router_id=snapshot.router_id,
        interfaces=[
            {"name": "ether1"},
            {"name": "ether2"},
            {"name": "wlan1"},
        ],
    )
    classified = classify_interface_inventory(inventory)
    topology = plan_topology(
        classified_interfaces=classified,
        requested_wan_interface=snapshot.topology.wan_interface,
        requested_lan_interfaces=snapshot.topology.lan_interfaces,
        create_bridge=snapshot.topology.create_bridge,
        bridge_name=snapshot.topology.bridge_name,
    )
    return plan_bridge(topology)


def test_plans_addressing():
    snapshot = build_snapshot()
    plan = plan_addressing(snapshot=snapshot, bridge_plan=bridge_plan(snapshot))

    assert plan.cidr == "10.10.0.0/24"
    assert plan.gateway_ip == "10.10.0.1"
    assert plan.target_interface == "bridge-hotspot"
    assert plan.dhcp_pool_start == "10.10.0.10"
    assert plan.dhcp_pool_end == "10.10.0.254"
    assert plan.network_address == "10.10.0.0"
    assert plan.prefix_length == 24


def test_rejects_gateway_outside_cidr():
    snapshot = build_snapshot(gateway="10.20.0.1")

    with pytest.raises(AddressPlannerError):
        plan_addressing(snapshot=snapshot, bridge_plan=bridge_plan(snapshot))


def test_rejects_pool_outside_cidr():
    snapshot = build_snapshot(pool="10.20.0.10-10.20.0.254")

    with pytest.raises(AddressPlannerError):
        plan_addressing(snapshot=snapshot, bridge_plan=bridge_plan(snapshot))


def test_rejects_pool_start_after_end():
    snapshot = build_snapshot(pool="10.10.0.200-10.10.0.10")

    with pytest.raises(AddressPlannerError):
        plan_addressing(snapshot=snapshot, bridge_plan=bridge_plan(snapshot))


def test_rejects_gateway_inside_pool():
    snapshot = build_snapshot(pool="10.10.0.1-10.10.0.254")

    with pytest.raises(AddressPlannerError):
        plan_addressing(snapshot=snapshot, bridge_plan=bridge_plan(snapshot))


def test_allows_explicit_target_interface():
    snapshot = build_snapshot()
    plan = plan_addressing(
        snapshot=snapshot,
        bridge_plan=bridge_plan(snapshot),
        target_interface="custom-client-interface",
    )

    assert plan.target_interface == "custom-client-interface"


def test_warns_for_very_small_network():
    snapshot = build_snapshot(
        cidr="10.10.0.0/30",
        gateway="10.10.0.1",
        pool="10.10.0.2-10.10.0.2",
    )

    plan = plan_addressing(snapshot=snapshot, bridge_plan=bridge_plan(snapshot))

    assert plan.warnings == ["Hotspot CIDR is very small for client DHCP usage"]
