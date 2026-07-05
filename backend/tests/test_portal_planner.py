import pytest

from backend.services.provisioning_v2.address_planner import plan_addressing
from backend.services.provisioning_v2.bridge_planner import plan_bridge
from backend.services.provisioning_v2.dhcp_planner import plan_dhcp
from backend.services.provisioning_v2.dns_planner import plan_dns
from backend.services.provisioning_v2.hotspot_planner import plan_hotspot
from backend.services.provisioning_v2.interface_classification import classify_interface_inventory
from backend.services.provisioning_v2.interface_inventory import build_interface_inventory
from backend.services.provisioning_v2.nat_planner import plan_nat
from backend.services.provisioning_v2.portal_planner import (
    PortalPlannerError,
    PortalStrategy,
    plan_portal,
)
from backend.services.provisioning_v2.snapshot_builder import build_provisioning_snapshot
from backend.services.provisioning_v2.topology_planner import plan_topology


def build_plans(portal_strategy="redirect", portal_url="https://caiwave.com/portal", api_url="https://caiwave.com/api"):
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
        "portal_public_url": portal_url,
        "api_public_url": api_url,
        "heartbeat_url": "https://caiwave.com/api/mikrotik-onboard/heartbeat",
        "router_dns_upstreams": ["1.1.1.1"],
        "client_dns_servers": ["10.10.0.1"],
        "portal_strategy": portal_strategy,
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
    )
    return snapshot, hotspot_plan, dns


def test_plans_redirect_portal():
    snapshot, hotspot_plan, dns = build_plans()

    plan = plan_portal(snapshot=snapshot, hotspot_plan=hotspot_plan, dns_plan=dns)

    assert plan.enabled is True
    assert plan.strategy == PortalStrategy.REDIRECT
    assert plan.portal_public_url == "https://caiwave.com/portal"
    assert plan.api_public_url == "https://caiwave.com/api"
    assert plan.login_redirect_url == "https://caiwave.com/portal/login"
    assert plan.success_url == "https://caiwave.com/portal/success"
    assert plan.failure_url == "https://caiwave.com/portal/failed"
    assert plan.captive_dns_name == "wifi.caiwave.com"


def test_includes_required_walled_garden_hosts():
    snapshot, hotspot_plan, dns = build_plans()

    plan = plan_portal(
        snapshot=snapshot,
        hotspot_plan=hotspot_plan,
        dns_plan=dns,
        payment_provider_hosts=["checkout.paystack.com"],
        asset_hosts=["static.caiwave.com"],
    )

    assert plan.required_hosts == [
        "caiwave.com",
        "checkout.paystack.com",
        "static.caiwave.com",
    ]
    assert plan.walled_garden_hosts == plan.required_hosts


def test_deduplicates_required_hosts():
    snapshot, hotspot_plan, dns = build_plans(
        portal_url="https://caiwave.com/portal",
        api_url="https://caiwave.com/api",
    )

    plan = plan_portal(
        snapshot=snapshot,
        hotspot_plan=hotspot_plan,
        dns_plan=dns,
        payment_provider_hosts=["caiwave.com"],
    )

    assert plan.required_hosts == ["caiwave.com"]


def test_embedded_strategy_warns():
    snapshot, hotspot_plan, dns = build_plans(portal_strategy="embedded")

    plan = plan_portal(snapshot=snapshot, hotspot_plan=hotspot_plan, dns_plan=dns)

    assert plan.strategy == PortalStrategy.EMBEDDED
    assert any("Embedded portal strategy" in warning for warning in plan.warnings)


def test_disabled_strategy_disables_portal():
    snapshot, hotspot_plan, dns = build_plans(portal_strategy="disabled")

    plan = plan_portal(snapshot=snapshot, hotspot_plan=hotspot_plan, dns_plan=dns)

    assert plan.enabled is False


def test_rejects_bad_portal_url():
    snapshot, hotspot_plan, dns = build_plans(portal_url="not-a-url")

    with pytest.raises(PortalPlannerError):
        plan_portal(snapshot=snapshot, hotspot_plan=hotspot_plan, dns_plan=dns)


def test_rejects_dns_hotspot_name_mismatch():
    snapshot, hotspot_plan, dns = build_plans()
    bad_dns = dns.model_copy(update={"captive_dns_name": "wrong.example.com"})

    with pytest.raises(PortalPlannerError):
        plan_portal(snapshot=snapshot, hotspot_plan=hotspot_plan, dns_plan=bad_dns)
