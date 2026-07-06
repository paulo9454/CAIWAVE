import pytest

from backend.services.provisioning_v2.address_planner import plan_addressing
from backend.services.provisioning_v2.bridge_planner import plan_bridge
from backend.services.provisioning_v2.dhcp_planner import plan_dhcp
from backend.services.provisioning_v2.dns_planner import plan_dns
from backend.services.provisioning_v2.firewall_planner import plan_firewall
from backend.services.provisioning_v2.hotspot_planner import plan_hotspot
from backend.services.provisioning_v2.interface_classification import classify_interface_inventory
from backend.services.provisioning_v2.interface_inventory import build_interface_inventory
from backend.services.provisioning_v2.nat_planner import plan_nat
from backend.services.provisioning_v2.portal_planner import plan_portal
from backend.services.provisioning_v2.provisioning_bundle import (
    ProvisioningBundleError,
    build_provisioning_bundle,
)
from backend.services.provisioning_v2.radius_planner import plan_radius
from backend.services.provisioning_v2.snapshot_builder import build_provisioning_snapshot
from backend.services.provisioning_v2.topology_planner import plan_topology


def build_all():
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
    nat = plan_nat(topology_plan=topology, address_plan=address)
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
    firewall = plan_firewall(
        topology_plan=topology,
        address_plan=address,
        dns_plan=dns,
        nat_plan=nat,
        hotspot_plan=hotspot_plan,
        portal_plan=portal,
        radius_plan=radius,
    )
    return snapshot, topology, bridge, address, dhcp, dns, nat, hotspot_plan, portal, radius, firewall


def test_builds_bundle():
    plans = build_all()

    bundle = build_provisioning_bundle(
        snapshot=plans[0],
        topology=plans[1],
        bridge=plans[2],
        address=plans[3],
        dhcp=plans[4],
        dns=plans[5],
        nat=plans[6],
        hotspot=plans[7],
        portal=plans[8],
        radius=plans[9],
        firewall=plans[10],
    )

    assert bundle.bundle_id == "bundle:snapshot:router-1"
    assert bundle.router_id == "router-1"
    assert bundle.hotspot_id == "hotspot-1"
    assert bundle.metadata["routeros_rendered"] is False
    assert bundle.checksum


def test_checksum_is_deterministic_except_timestamp():
    plans = build_all()

    first = build_provisioning_bundle(
        snapshot=plans[0], topology=plans[1], bridge=plans[2], address=plans[3],
        dhcp=plans[4], dns=plans[5], nat=plans[6], hotspot=plans[7],
        portal=plans[8], radius=plans[9], firewall=plans[10],
    )
    second = build_provisioning_bundle(
        snapshot=plans[0], topology=plans[1], bridge=plans[2], address=plans[3],
        dhcp=plans[4], dns=plans[5], nat=plans[6], hotspot=plans[7],
        portal=plans[8], radius=plans[9], firewall=plans[10],
    )

    assert first.checksum == second.checksum


def test_rejects_address_dhcp_mismatch():
    plans = build_all()
    bad_dhcp = plans[4].model_copy(update={"target_interface": "wrong"})

    with pytest.raises(ProvisioningBundleError):
        build_provisioning_bundle(
            snapshot=plans[0], topology=plans[1], bridge=plans[2], address=plans[3],
            dhcp=bad_dhcp, dns=plans[5], nat=plans[6], hotspot=plans[7],
            portal=plans[8], radius=plans[9], firewall=plans[10],
        )


def test_rejects_hotspot_dns_mismatch():
    plans = build_all()
    bad_hotspot = plans[7].model_copy(update={"dns_name": "wrong.example.com"})

    with pytest.raises(ProvisioningBundleError):
        build_provisioning_bundle(
            snapshot=plans[0], topology=plans[1], bridge=plans[2], address=plans[3],
            dhcp=plans[4], dns=plans[5], nat=plans[6], hotspot=bad_hotspot,
            portal=plans[8], radius=plans[9], firewall=plans[10],
        )


def test_rejects_firewall_wan_mismatch():
    plans = build_all()
    bad_firewall = plans[10].model_copy(update={"wan_interface": "wrong"})

    with pytest.raises(ProvisioningBundleError):
        build_provisioning_bundle(
            snapshot=plans[0], topology=plans[1], bridge=plans[2], address=plans[3],
            dhcp=plans[4], dns=plans[5], nat=plans[6], hotspot=plans[7],
            portal=plans[8], radius=plans[9], firewall=bad_firewall,
        )
