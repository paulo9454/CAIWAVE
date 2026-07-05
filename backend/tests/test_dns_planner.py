import pytest

from backend.services.provisioning_v2.address_planner import plan_addressing
from backend.services.provisioning_v2.bridge_planner import plan_bridge
from backend.services.provisioning_v2.dhcp_planner import plan_dhcp
from backend.services.provisioning_v2.dns_planner import DNSPlannerError, plan_dns
from backend.services.provisioning_v2.interface_classification import classify_interface_inventory
from backend.services.provisioning_v2.interface_inventory import build_interface_inventory
from backend.services.provisioning_v2.snapshot_builder import build_provisioning_snapshot
from backend.services.provisioning_v2.topology_planner import plan_topology


def build_plans(upstreams=None, client_dns=None, dns_name="wifi.caiwave.com"):
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
        "dns_name": dns_name,
    }
    hotspot = {"id": "hotspot-1", "owner_id": "owner-1"}
    config = {
        "radius_host": "radius.caiwave.com",
        "portal_public_url": "https://caiwave.com/portal",
        "api_public_url": "https://caiwave.com/api",
        "heartbeat_url": "https://caiwave.com/api/mikrotik-onboard/heartbeat",
        "router_dns_upstreams": ["1.1.1.1"] if upstreams is None else upstreams,
        "client_dns_servers": ["10.10.0.1"] if client_dns is None else client_dns,
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
    dhcp = plan_dhcp(address_plan=address, dns_servers=snapshot.networking.client_dns_servers)
    return snapshot, address, dhcp


def test_plans_dns():
    snapshot, address, dhcp = build_plans()

    plan = plan_dns(snapshot=snapshot, address_plan=address, dhcp_plan=dhcp)

    assert plan.router_resolver_enabled is True
    assert plan.client_dns_servers == ["10.10.0.1"]
    assert plan.upstream_dns_servers == ["1.1.1.1"]
    assert plan.captive_dns_name == "wifi.caiwave.com"
    assert plan.static_records == {"wifi.caiwave.com": "10.10.0.1"}


def test_warns_when_gateway_not_client_dns():
    snapshot, address, dhcp = build_plans(client_dns=["8.8.8.8"])

    plan = plan_dns(snapshot=snapshot, address_plan=address, dhcp_plan=dhcp)

    assert "Router resolver enabled but gateway IP is not in DHCP client DNS servers" in plan.warnings


def test_warns_when_no_upstream_with_router_resolver():
    snapshot, address, dhcp = build_plans(upstreams=[])

    plan = plan_dns(snapshot=snapshot, address_plan=address, dhcp_plan=dhcp)

    assert "Router resolver enabled without explicit upstream DNS servers" in plan.warnings


def test_rejects_invalid_client_dns():
    snapshot, address, dhcp = build_plans(client_dns=["not-an-ip"])

    with pytest.raises(DNSPlannerError):
        plan_dns(snapshot=snapshot, address_plan=address, dhcp_plan=dhcp)


def test_rejects_invalid_upstream_dns():
    snapshot, address, dhcp = build_plans(upstreams=["bad-ip"])

    with pytest.raises(DNSPlannerError):
        plan_dns(snapshot=snapshot, address_plan=address, dhcp_plan=dhcp)


def test_rejects_no_client_dns_when_router_resolver_disabled():
    snapshot, address, dhcp = build_plans()
    dhcp = dhcp.model_copy(update={"dns_servers": []})

    with pytest.raises(DNSPlannerError):
        plan_dns(
            snapshot=snapshot,
            address_plan=address,
            dhcp_plan=dhcp,
            router_resolver_enabled=False,
        )
