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
from backend.services.provisioning_v2.provisioning_bundle import build_provisioning_bundle
from backend.services.provisioning_v2.radius_planner import plan_radius
from backend.services.provisioning_v2.routeros_firewall_renderer import render_firewall_section
from backend.services.provisioning_v2.routeros_renderer_contracts import RenderStatus, RouterOSSectionName
from backend.services.provisioning_v2.snapshot_builder import build_provisioning_snapshot
from backend.services.provisioning_v2.topology_planner import plan_topology


def build_bundle():
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
    inventory = build_interface_inventory(router_id=snapshot.router_id, interfaces=[{"name": "ether1"}, {"name": "ether2"}])
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
    hotspot_plan = plan_hotspot(snapshot=snapshot, bridge_plan=bridge, address_plan=address, dhcp_plan=dhcp, dns_plan=dns, nat_plan=nat)
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

    return build_provisioning_bundle(
        snapshot=snapshot,
        topology=topology,
        bridge=bridge,
        address=address,
        dhcp=dhcp,
        dns=dns,
        nat=nat,
        hotspot=hotspot_plan,
        portal=portal,
        radius=radius,
        firewall=firewall,
    )


def test_renders_firewall_section():
    section = render_firewall_section(build_bundle())

    assert section.name == RouterOSSectionName.FIREWALL
    assert section.status == RenderStatus.RENDERED
    assert section.checksum
    assert "# CAIWAVE Firewall" in section.content
    assert "# WAN interface: ether1" in section.content
    assert '/ip firewall filter add action="accept" chain="input" comment="CAIWAVE: Allow hotspot clients to query router DNS" dst-port="53" protocol="udp" src-address="10.10.0.0/24"' in section.content


def test_renders_default_drop_rules():
    section = render_firewall_section(build_bundle())

    assert '/ip firewall filter add action="drop" chain="input" comment="CAIWAVE default drop WAN input" in-interface="ether1"' in section.content
    assert '/ip firewall filter add action="drop" chain="forward" comment="CAIWAVE default drop unmatched forward"' in section.content


def test_renders_established_related_forward_accept_before_drop():
    content = render_firewall_section(build_bundle()).content

    allow = (
        '/ip firewall filter add action="accept" chain="forward" '
        'comment="CAIWAVE: Allow established and related forwarding" '
        'connection-state="established,related"'
    )
    drop = (
        '/ip firewall filter add action="drop" chain="forward" '
        'comment="CAIWAVE default drop unmatched forward"'
    )

    assert allow in content
    assert content.index(allow) < content.index(drop)


def test_renders_authenticated_hotspot_forward_accept_before_drop():
    content = render_firewall_section(build_bundle()).content

    allow = (
        '/ip firewall filter add action="accept" chain="forward" '
        'comment="CAIWAVE: Allow authenticated hotspot clients '
        'to internet" hotspot="auth"'
    )
    drop = (
        '/ip firewall filter add action="drop" chain="forward" '
        'comment="CAIWAVE default drop unmatched forward"'
    )

    assert allow in content
    assert content.index(allow) < content.index(drop)


def test_renders_preauth_portal_address_list_entries():
    content = render_firewall_section(build_bundle()).content

    assert (
        '/ip firewall address-list add '
        'address="caiwave.com" '
        'comment="CAIWAVE pre-auth host" '
        'list="CAIWAVE-PREAUTH"'
    ) in content

    assert (
        '/ip firewall address-list add '
        'address="checkout.paystack.com" '
        'comment="CAIWAVE pre-auth host" '
        'list="CAIWAVE-PREAUTH"'
    ) in content


def test_renders_preauth_forward_allow_before_final_drop():
    content = render_firewall_section(build_bundle()).content

    allow = (
        '/ip firewall filter add action="accept" chain="forward" '
        'comment="CAIWAVE: Allow pre-auth portal and payment traffic" '
        'dst-address-list="CAIWAVE-PREAUTH" dst-port="80,443" '
        'hotspot="from-client,!auth" protocol="tcp"'
    )
    drop = (
        '/ip firewall filter add action="drop" chain="forward" '
        'comment="CAIWAVE default drop unmatched forward"'
    )

    assert allow in content
    assert content.index(allow) < content.index(drop)


def test_deduplicates_preauth_portal_hosts():
    bundle = build_bundle()
    duplicated = bundle.model_copy(
        update={
            "firewall": bundle.firewall.model_copy(
                update={
                    "portal_hosts": [
                        "caiwave.com",
                        "checkout.paystack.com",
                        "caiwave.com",
                    ]
                }
            )
        }
    )

    content = render_firewall_section(duplicated).content

    assert content.count(
        'address="caiwave.com" '
        'comment="CAIWAVE pre-auth host"'
    ) == 1
