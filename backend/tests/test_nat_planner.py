import pytest

from backend.services.provisioning_v2.address_planner import plan_addressing
from backend.services.provisioning_v2.bridge_planner import plan_bridge
from backend.services.provisioning_v2.interface_classification import classify_interface_inventory
from backend.services.provisioning_v2.interface_inventory import build_interface_inventory
from backend.services.provisioning_v2.nat_planner import (
    NATPlannerError,
    NATStrategy,
    plan_nat,
)
from backend.services.provisioning_v2.snapshot_builder import build_provisioning_snapshot
from backend.services.provisioning_v2.topology_planner import TopologyPlan, plan_topology


def build_topology_and_address():
    router = {
        "id": "router-1",
        "name": "GOODlife",
        "owner_id": "owner-1",
        "hotspot_id": "hotspot-1",
        "nas_identifier": "CAIWAVE-GOODLIFE",
        "wan_interface": "ether1",
        "lan_interfaces": ["ether2"],
        "create_bridge": True,
        "bridge_name": "bridge-hotspot",
        "effective_lan_interface": "bridge-hotspot",
        "mode": "fresh",
        "hotspot_cidr": "10.10.0.0/24",
        "hotspot_gateway": "10.10.0.1",
        "dhcp_pool": "10.10.0.10-10.10.0.254",
        "dns_name": "wifi.caiwave.com",
    }
    hotspot = {"id": "hotspot-1", "owner_id": "owner-1"}
    config = {
        "radius_host": "radius.caiwave.com",
        "portal_public_url": "https://caiwave.com/portal",
        "api_public_url": "https://caiwave.com/api",
        "heartbeat_url": "https://caiwave.com/api/mikrotik-onboard/heartbeat",
    }
    snapshot = build_provisioning_snapshot(router, hotspot, config)
    inventory = build_interface_inventory(
        router_id=snapshot.router_id,
        interfaces=[{"name": "ether1"}, {"name": "ether2"}],
    )
    classified = classify_interface_inventory(inventory)
    topology = plan_topology(
        classified_interfaces=classified,
        requested_wan_interface=snapshot.topology.wan_interface,
        requested_lan_interfaces=snapshot.topology.lan_interfaces,
        create_bridge=snapshot.topology.create_bridge,
        bridge_name=snapshot.topology.bridge_name,
    )
    bridge = plan_bridge(topology)
    address = plan_addressing(snapshot=snapshot, bridge_plan=bridge)
    return topology, address


def test_plans_masquerade_nat():
    topology, address = build_topology_and_address()

    plan = plan_nat(topology_plan=topology, address_plan=address)

    assert plan.enabled is True
    assert plan.strategy == NATStrategy.MASQUERADE
    assert plan.outbound_interface == "ether1"
    assert plan.source_networks == ["10.10.0.0/24"]
    assert plan.excluded_networks == []


def test_allows_excluded_networks():
    topology, address = build_topology_and_address()

    plan = plan_nat(
        topology_plan=topology,
        address_plan=address,
        excluded_networks=["10.0.0.0/8", "192.168.0.0/16"],
    )

    assert plan.excluded_networks == ["10.0.0.0/8", "192.168.0.0/16"]


def test_nat_disabled_returns_none_strategy():
    topology, address = build_topology_and_address()

    plan = plan_nat(topology_plan=topology, address_plan=address, enabled=False)

    assert plan.enabled is False
    assert plan.strategy == NATStrategy.NONE
    assert plan.source_networks == []
    assert "NAT is disabled" in plan.warnings[0]


def test_rejects_none_strategy_when_enabled():
    topology, address = build_topology_and_address()

    with pytest.raises(NATPlannerError):
        plan_nat(
            topology_plan=topology,
            address_plan=address,
            enabled=True,
            strategy=NATStrategy.NONE,
        )


def test_rejects_invalid_excluded_network():
    topology, address = build_topology_and_address()

    with pytest.raises(NATPlannerError):
        plan_nat(
            topology_plan=topology,
            address_plan=address,
            excluded_networks=["bad-network"],
        )


def test_warns_for_hairpin_nat():
    topology, address = build_topology_and_address()

    plan = plan_nat(
        topology_plan=topology,
        address_plan=address,
        hairpin_nat=True,
    )

    assert plan.hairpin_nat is True
    assert "Hairpin NAT requested" in plan.warnings[0]


def test_rejects_upstream_also_client():
    topology, address = build_topology_and_address()
    bad_topology = TopologyPlan(
        upstream_interface="ether1",
        client_interfaces=["ether1"],
        bridge_strategy=topology.bridge_strategy,
        bridge_name=topology.bridge_name,
    )

    with pytest.raises(NATPlannerError):
        plan_nat(topology_plan=bad_topology, address_plan=address)
