from backend.services.provisioning_v2.address_planner import plan_addressing
from backend.services.provisioning_v2.bridge_planner import plan_bridge
from backend.services.provisioning_v2.dhcp_planner import plan_dhcp
from backend.services.provisioning_v2.dns_planner import plan_dns
from backend.services.provisioning_v2.firewall_planner import (
    FirewallAction,
    FirewallChain,
    plan_firewall,
)
from backend.services.provisioning_v2.hotspot_planner import plan_hotspot
from backend.services.provisioning_v2.interface_classification import classify_interface_inventory
from backend.services.provisioning_v2.interface_inventory import build_interface_inventory
from backend.services.provisioning_v2.nat_planner import plan_nat
from backend.services.provisioning_v2.portal_planner import plan_portal
from backend.services.provisioning_v2.radius_planner import plan_radius
from backend.services.provisioning_v2.snapshot_builder import build_provisioning_snapshot
from backend.services.provisioning_v2.topology_planner import plan_topology


def build_all_plans(nat_enabled=True):
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
    hotspot_plan = plan_hotspot(
        snapshot=snapshot,
        bridge_plan=bridge,
        address_plan=address,
        dhcp_plan=dhcp,
        dns_plan=dns,
        nat_plan=nat,
    )
    portal = plan_portal(
        snapshot=snapshot,
        hotspot_plan=hotspot_plan,
        dns_plan=dns,
        payment_provider_hosts=["checkout.paystack.com"],
    )
    radius = plan_radius(snapshot=snapshot, hotspot_plan=hotspot_plan)
    return topology, address, dns, nat, hotspot_plan, portal, radius


def test_plans_firewall_policy():
    topology, address, dns, nat, hotspot, portal, radius = build_all_plans()

    plan = plan_firewall(
        topology_plan=topology,
        address_plan=address,
        dns_plan=dns,
        nat_plan=nat,
        hotspot_plan=hotspot,
        portal_plan=portal,
        radius_plan=radius,
    )

    assert plan.default_input_policy == FirewallAction.DROP
    assert plan.default_forward_policy == FirewallAction.DROP
    assert plan.wan_interface == "ether1"
    assert plan.client_networks == ["10.10.0.0/24"]
    assert "caiwave.com" in plan.portal_hosts
    assert "radius.caiwave.com" in plan.radius_hosts


def test_includes_core_input_rules():
    topology, address, dns, nat, hotspot, portal, radius = build_all_plans()

    plan = plan_firewall(
        topology_plan=topology,
        address_plan=address,
        dns_plan=dns,
        nat_plan=nat,
        hotspot_plan=hotspot,
        portal_plan=portal,
        radius_plan=radius,
    )

    rule_names = [rule.name for rule in plan.rules]

    assert "allow-established-related" in rule_names
    assert "drop-invalid" in rule_names
    assert "allow-client-dns" in rule_names
    assert "allow-client-dhcp" in rule_names


def test_includes_portal_walled_garden_rules():
    topology, address, dns, nat, hotspot, portal, radius = build_all_plans()

    plan = plan_firewall(
        topology_plan=topology,
        address_plan=address,
        dns_plan=dns,
        nat_plan=nat,
        hotspot_plan=hotspot,
        portal_plan=portal,
        radius_plan=radius,
    )

    portal_rules = [rule for rule in plan.rules if rule.destination_host == "checkout.paystack.com"]

    assert portal_rules
    assert portal_rules[0].chain == FirewallChain.FORWARD


def test_includes_radius_rules():
    topology, address, dns, nat, hotspot, portal, radius = build_all_plans()

    plan = plan_firewall(
        topology_plan=topology,
        address_plan=address,
        dns_plan=dns,
        nat_plan=nat,
        hotspot_plan=hotspot,
        portal_plan=portal,
        radius_plan=radius,
    )

    rule_names = [rule.name for rule in plan.rules]

    assert "allow-radius-auth" in rule_names
    assert "allow-radius-accounting" in rule_names


def test_includes_management_sources():
    topology, address, dns, nat, hotspot, portal, radius = build_all_plans()

    plan = plan_firewall(
        topology_plan=topology,
        address_plan=address,
        dns_plan=dns,
        nat_plan=nat,
        hotspot_plan=hotspot,
        portal_plan=portal,
        radius_plan=radius,
        management_sources=["192.168.88.0/24"],
    )

    assert any(rule.name == "allow-management-192.168.88.0/24" for rule in plan.rules)


def test_warns_when_nat_disabled():
    topology, address, dns, nat, hotspot, portal, radius = build_all_plans(nat_enabled=False)

    plan = plan_firewall(
        topology_plan=topology,
        address_plan=address,
        dns_plan=dns,
        nat_plan=nat,
        hotspot_plan=hotspot,
        portal_plan=portal,
        radius_plan=radius,
    )

    assert any("NAT is disabled" in warning for warning in plan.warnings)
