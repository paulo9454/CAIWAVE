import pytest

from backend.services.provisioning_v2.address_planner import plan_addressing
from backend.services.provisioning_v2.bridge_planner import plan_bridge
from backend.services.provisioning_v2.dhcp_planner import plan_dhcp
from backend.services.provisioning_v2.dns_planner import plan_dns
from backend.services.provisioning_v2.hotspot_planner import HotspotAuthMode, plan_hotspot
from backend.services.provisioning_v2.interface_classification import classify_interface_inventory
from backend.services.provisioning_v2.interface_inventory import build_interface_inventory
from backend.services.provisioning_v2.nat_planner import plan_nat
from backend.services.provisioning_v2.radius_planner import (
    RadiusPlannerError,
    RadiusService,
    plan_radius,
)
from backend.services.provisioning_v2.snapshot_builder import build_provisioning_snapshot
from backend.services.provisioning_v2.topology_planner import plan_topology


def build_snapshot_and_hotspot(auth_mode=HotspotAuthMode.RADIUS, radius_host="radius.caiwave.com"):
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
        "radius_host": radius_host,
        "portal_public_url": "https://caiwave.com/portal",
        "api_public_url": "https://caiwave.com/api",
        "heartbeat_url": "https://caiwave.com/api/mikrotik-onboard/heartbeat",
        "router_dns_upstreams": ["1.1.1.1"],
        "client_dns_servers": ["10.10.0.1"],
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
    dns = plan_dns(snapshot=snapshot, address_plan=address, dhcp_plan=dhcp)
    nat = plan_nat(topology_plan=topology, address_plan=address)
    hotspot_plan = plan_hotspot(
        snapshot=snapshot,
        bridge_plan=bridge,
        address_plan=address,
        dhcp_plan=dhcp,
        dns_plan=dns,
        nat_plan=nat,
        auth_mode=auth_mode,
    )
    return snapshot, hotspot_plan


def test_plans_radius():
    snapshot, hotspot_plan = build_snapshot_and_hotspot()

    plan = plan_radius(snapshot=snapshot, hotspot_plan=hotspot_plan)

    assert plan.enabled is True
    assert plan.services == [RadiusService.HOTSPOT]
    assert plan.auth_host == "radius.caiwave.com"
    assert plan.auth_port == 1812
    assert plan.accounting_port == 1813
    assert plan.secret_ref == "router-radius-secret:router-1"
    assert plan.nas_identifier == "CAIWAVE-GOODLIFE"
    assert plan.accounting_enabled is True


def test_allows_custom_services_and_coa():
    snapshot, hotspot_plan = build_snapshot_and_hotspot()

    plan = plan_radius(
        snapshot=snapshot,
        hotspot_plan=hotspot_plan,
        services=[RadiusService.HOTSPOT, RadiusService.LOGIN],
        coa_enabled=True,
        interim_update_seconds=120,
    )

    assert plan.services == [RadiusService.HOTSPOT, RadiusService.LOGIN]
    assert plan.coa_enabled is True
    assert plan.interim_update_seconds == 120


def test_disables_radius_when_hotspot_not_radius():
    snapshot, hotspot_plan = build_snapshot_and_hotspot(auth_mode=HotspotAuthMode.LOCAL)

    plan = plan_radius(snapshot=snapshot, hotspot_plan=hotspot_plan)

    assert plan.enabled is False
    assert plan.accounting_enabled is False
    assert plan.services == []


def test_accepts_ip_radius_host():
    snapshot, hotspot_plan = build_snapshot_and_hotspot(radius_host="10.0.0.10")

    plan = plan_radius(snapshot=snapshot, hotspot_plan=hotspot_plan)

    assert plan.auth_host == "10.0.0.10"


def test_rejects_bad_radius_host():
    snapshot, hotspot_plan = build_snapshot_and_hotspot(radius_host="badhost")

    with pytest.raises(RadiusPlannerError):
        plan_radius(snapshot=snapshot, hotspot_plan=hotspot_plan)


def test_rejects_invalid_interim_update():
    snapshot, hotspot_plan = build_snapshot_and_hotspot()

    with pytest.raises(RadiusPlannerError):
        plan_radius(snapshot=snapshot, hotspot_plan=hotspot_plan, interim_update_seconds=0)


def test_rejects_empty_services():
    snapshot, hotspot_plan = build_snapshot_and_hotspot()

    with pytest.raises(RadiusPlannerError):
        plan_radius(snapshot=snapshot, hotspot_plan=hotspot_plan, services=[])
