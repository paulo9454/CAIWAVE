import pytest

from backend.services.provisioning_v2.address_planner import plan_addressing
from backend.services.provisioning_v2.bridge_planner import plan_bridge
from backend.services.provisioning_v2.dhcp_planner import plan_dhcp
from backend.services.provisioning_v2.dns_planner import plan_dns
from backend.services.provisioning_v2.hotspot_planner import (
    HotspotAuthMode,
    HotspotPlannerError,
    plan_hotspot,
)
from backend.services.provisioning_v2.interface_classification import classify_interface_inventory
from backend.services.provisioning_v2.interface_inventory import build_interface_inventory
from backend.services.provisioning_v2.nat_planner import plan_nat
from backend.services.provisioning_v2.snapshot_builder import build_provisioning_snapshot
from backend.services.provisioning_v2.topology_planner import plan_topology


def build_plans(nat_enabled=True):
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
    nat = plan_nat(topology_plan=topology, address_plan=address, enabled=nat_enabled)
    return snapshot, bridge, address, dhcp, dns, nat


def test_plans_radius_hotspot():
    snapshot, bridge, address, dhcp, dns, nat = build_plans()

    plan = plan_hotspot(
        snapshot=snapshot,
        bridge_plan=bridge,
        address_plan=address,
        dhcp_plan=dhcp,
        dns_plan=dns,
        nat_plan=nat,
    )

    assert plan.enabled is True
    assert plan.server_name == "caiwave-hotspot"
    assert plan.profile_name == "caiwave-profile"
    assert plan.target_interface == "bridge-hotspot"
    assert plan.address_pool_name == "caiwave-pool-hotspot"
    assert plan.dns_name == "wifi.caiwave.com"
    assert plan.auth_mode == HotspotAuthMode.RADIUS
    assert plan.use_radius is True
    assert plan.accounting_enabled is True


def test_local_auth_disables_radius():
    snapshot, bridge, address, dhcp, dns, nat = build_plans()

    plan = plan_hotspot(
        snapshot=snapshot,
        bridge_plan=bridge,
        address_plan=address,
        dhcp_plan=dhcp,
        dns_plan=dns,
        nat_plan=nat,
        auth_mode=HotspotAuthMode.LOCAL,
    )

    assert plan.use_radius is False
    assert plan.accounting_enabled is False


def test_disabled_auth_disables_hotspot():
    snapshot, bridge, address, dhcp, dns, nat = build_plans()

    plan = plan_hotspot(
        snapshot=snapshot,
        bridge_plan=bridge,
        address_plan=address,
        dhcp_plan=dhcp,
        dns_plan=dns,
        nat_plan=nat,
        auth_mode=HotspotAuthMode.DISABLED,
    )

    assert plan.enabled is False
    assert "Hotspot authentication is disabled" in plan.warnings


def test_warns_when_nat_disabled():
    snapshot, bridge, address, dhcp, dns, nat = build_plans(nat_enabled=False)

    plan = plan_hotspot(
        snapshot=snapshot,
        bridge_plan=bridge,
        address_plan=address,
        dhcp_plan=dhcp,
        dns_plan=dns,
        nat_plan=nat,
    )

    assert any("NAT is disabled" in warning for warning in plan.warnings)


def test_rejects_address_dhcp_interface_mismatch():
    snapshot, bridge, address, dhcp, dns, nat = build_plans()
    bad_dhcp = dhcp.model_copy(update={"target_interface": "other-interface"})

    with pytest.raises(HotspotPlannerError):
        plan_hotspot(
            snapshot=snapshot,
            bridge_plan=bridge,
            address_plan=address,
            dhcp_plan=bad_dhcp,
            dns_plan=dns,
            nat_plan=nat,
        )


def test_rejects_dns_name_mismatch():
    snapshot, bridge, address, dhcp, dns, nat = build_plans()
    bad_dns = dns.model_copy(update={"captive_dns_name": "other.example.com"})

    with pytest.raises(HotspotPlannerError):
        plan_hotspot(
            snapshot=snapshot,
            bridge_plan=bridge,
            address_plan=address,
            dhcp_plan=dhcp,
            dns_plan=bad_dns,
            nat_plan=nat,
        )
