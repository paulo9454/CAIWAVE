import pytest

from backend.services.provisioning_v2.address_planner import plan_addressing
from backend.services.provisioning_v2.bridge_planner import plan_bridge
from backend.services.provisioning_v2.dhcp_planner import (
    DHCPAuthoritativeMode,
    DHCPPlannerError,
    plan_dhcp,
)
from backend.services.provisioning_v2.interface_classification import classify_interface_inventory
from backend.services.provisioning_v2.interface_inventory import build_interface_inventory
from backend.services.provisioning_v2.snapshot_builder import build_provisioning_snapshot
from backend.services.provisioning_v2.topology_planner import plan_topology


def address_plan():
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
    return plan_addressing(snapshot=snapshot, bridge_plan=bridge)


def test_plans_dhcp_from_address_plan():
    plan = plan_dhcp(address_plan=address_plan())

    assert plan.server_name == "caiwave-dhcp-hotspot"
    assert plan.pool_name == "caiwave-pool-hotspot"
    assert plan.target_interface == "bridge-hotspot"
    assert plan.pool_start == "10.10.0.10"
    assert plan.pool_end == "10.10.0.254"
    assert plan.gateway_ip == "10.10.0.1"
    assert plan.network_cidr == "10.10.0.0/24"
    assert plan.dns_servers == ["10.10.0.1"]


def test_allows_custom_names_and_dns():
    plan = plan_dhcp(
        address_plan=address_plan(),
        server_name="custom-dhcp",
        pool_name="custom-pool",
        dns_servers=["1.1.1.1", "8.8.8.8"],
        lease_time="2h",
        authoritative=DHCPAuthoritativeMode.YES,
    )

    assert plan.server_name == "custom-dhcp"
    assert plan.pool_name == "custom-pool"
    assert plan.dns_servers == ["1.1.1.1", "8.8.8.8"]
    assert plan.lease_time == "2h"
    assert plan.authoritative == DHCPAuthoritativeMode.YES


def test_rejects_missing_server_name():
    with pytest.raises(DHCPPlannerError):
        plan_dhcp(address_plan=address_plan(), server_name="")


def test_rejects_missing_pool_name():
    with pytest.raises(DHCPPlannerError):
        plan_dhcp(address_plan=address_plan(), pool_name="")


def test_preserves_address_warnings():
    small = address_plan().model_copy(
        update={"warnings": ["Hotspot CIDR is very small for client DHCP usage"]}
    )

    plan = plan_dhcp(address_plan=small)

    assert plan.warnings == ["Hotspot CIDR is very small for client DHCP usage"]
