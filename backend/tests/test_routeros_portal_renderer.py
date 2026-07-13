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
from backend.services.provisioning_v2.routeros_portal_renderer import render_portal_section
from backend.services.provisioning_v2.routeros_renderer_contracts import RenderStatus, RouterOSSectionName
from backend.services.provisioning_v2.snapshot_builder import build_provisioning_snapshot
from backend.services.provisioning_v2.topology_planner import plan_topology


def build_bundle(portal_strategy="redirect"):
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
        "dns_name": "login.caiwave.local",
    }
    hotspot = {"id": "hotspot-1", "owner_id": "owner-1"}
    config = {
        "radius_host": "radius.caiwave.com",
        "portal_public_url": "https://caiwave.com",
        "api_public_url": "https://caiwave.com/api",
        "heartbeat_url": "https://caiwave.com/api/mikrotik-onboard/heartbeat",
        "router_dns_upstreams": ["1.1.1.1"],
        "client_dns_servers": ["10.10.0.1"],
        "portal_strategy": portal_strategy,
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
        asset_hosts=["static.caiwave.com"],
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


def test_renders_portal_section():
    section = render_portal_section(build_bundle())

    assert section.name == RouterOSSectionName.PORTAL
    assert section.status == RenderStatus.RENDERED
    assert section.checksum
    assert "# CAIWAVE Portal" in section.content
    assert "# Portal strategy: redirect" in section.content
    assert "wifi.caiwave.com" not in section.content
    expected_login_url = (
        "https://caiwave.com/portal/hotspot-1"
        "?mac=\\$(mac)"
        "&ip=\\$(ip)"
        "&dst=\\$(link-orig-esc)"
        "&login_url=\\$(link-login-only)"
    )

    assert f"# Login redirect URL: {expected_login_url}" in section.content
    assert 'name="hotspot/login.html"' in section.content
    assert expected_login_url in section.content
    assert "/portal/login?hotspot=" not in section.content
    assert "?hotspot=" not in section.content
    assert '/ip hotspot walled-garden add action="allow" comment="CAIWAVE managed portal walled garden host" dst-host="caiwave.com"' in section.content
    assert '/ip hotspot walled-garden add action="allow" comment="CAIWAVE managed portal walled garden host" dst-host="checkout.paystack.com"' in section.content
    assert '/ip hotspot walled-garden add action="allow" comment="CAIWAVE managed portal walled garden host" dst-host="static.caiwave.com"' in section.content


def test_renders_disabled_portal_comment():
    section = render_portal_section(build_bundle(portal_strategy="disabled"))

    assert "# Portal disabled by provisioning plan" in section.content
    assert "/ip hotspot walled-garden add" not in section.content
