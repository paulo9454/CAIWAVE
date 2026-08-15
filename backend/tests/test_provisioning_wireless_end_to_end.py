from backend.services.provisioning_v2.address_planner import plan_addressing
from backend.services.provisioning_v2.bridge_planner import plan_bridge
from backend.services.provisioning_v2.dhcp_planner import plan_dhcp
from backend.services.provisioning_v2.dns_planner import plan_dns
from backend.services.provisioning_v2.firewall_planner import plan_firewall
from backend.services.provisioning_v2.hotspot_planner import plan_hotspot
from backend.services.provisioning_v2.interface_classification import (
    classify_interface_inventory,
)
from backend.services.provisioning_v2.nat_planner import plan_nat
from backend.services.provisioning_v2.portal_planner import plan_portal
from backend.services.provisioning_v2.provisioning_bundle import (
    build_provisioning_bundle,
)
from backend.services.provisioning_v2.radius_planner import plan_radius
from backend.services.provisioning_v2.router_capabilities import (
    detect_router_capabilities,
)
from backend.services.provisioning_v2.router_discovery_inventory_adapter import (
    build_inventory_from_discovery,
)
from backend.services.provisioning_v2.router_discovery_models import (
    DiscoveredInterface,
    RouterDiscoverySnapshot,
)
from backend.services.provisioning_v2.routeros_render_orchestrator import (
    render_routeros_bundle,
)
from backend.services.provisioning_v2.routeros_renderer_contracts import (
    RouterOSSectionName,
    build_render_context,
)
from backend.services.provisioning_v2.snapshot_builder import (
    build_provisioning_snapshot,
)
from backend.services.provisioning_v2.topology_planner import plan_topology
from backend.services.provisioning_v2.wireless_planner import plan_wireless


def test_discovery_to_wireless_routeros_artifact():
    router = {
        "id": "router-wireless-1",
        "name": "WIRELESS-TEST",
        "owner_id": "owner-1",
        "hotspot_id": "hotspot-1",
        "nas_identifier": "CAIWAVE-WIRELESS-TEST",
        "wan_interface": "ether1",
        "lan_interfaces": ["ether2", "wlan1"],
        "create_bridge": True,
        "bridge_name": "bridge-hotspot",
        "effective_lan_interface": "bridge-hotspot",
        "mode": "fresh",
        "hotspot_cidr": "10.20.0.0/24",
        "hotspot_gateway": "10.20.0.1",
        "dhcp_pool": "10.20.0.10-10.20.0.254",
        "dns_name": "wifi.caiwave.com",
    }

    hotspot = {
        "id": "hotspot-1",
        "owner_id": "owner-1",
    }

    config = {
        "radius_host": "radius.caiwave.com",
        "portal_public_url": "https://caiwave.com/portal",
        "api_public_url": "https://caiwave.com/api",
        "heartbeat_url": "https://caiwave.com/api/mikrotik-onboard/heartbeat",
        "router_dns_upstreams": ["1.1.1.1"],
        "client_dns_servers": ["10.20.0.1"],
    }

    snapshot = build_provisioning_snapshot(
        router,
        hotspot,
        config,
    )

    discovery = RouterDiscoverySnapshot(
        router_id=snapshot.router_id,
        board_name="hAP-test",
        routeros_version="7.18",
        architecture="arm",
        interfaces=[
            DiscoveredInterface(
                name="ether1",
                type="ethernet",
                running=True,
            ),
            DiscoveredInterface(
                name="ether2",
                type="ethernet",
                running=True,
            ),
            DiscoveredInterface(
                name="wlan1",
                type="wireless",
                running=True,
            ),
        ],
    )

    inventory = build_inventory_from_discovery(discovery)
    classified = classify_interface_inventory(inventory)

    assert inventory.names == ["ether1", "ether2", "wlan1"]
    assert any(
        item.name == "wlan1"
        and item.classification.value == "physical_wireless"
        for item in classified
    )

    capabilities = detect_router_capabilities(discovery)

    assert capabilities.supports_wireless is True
    assert capabilities.wireless_interfaces == ["wlan1"]

    topology = plan_topology(
        classified_interfaces=classified,
        requested_wan_interface=snapshot.topology.wan_interface,
        requested_lan_interfaces=snapshot.topology.lan_interfaces,
        create_bridge=snapshot.topology.create_bridge,
        bridge_name=snapshot.topology.bridge_name,
    )

    bridge = plan_bridge(topology)
    address = plan_addressing(
        snapshot=snapshot,
        bridge_plan=bridge,
    )
    dhcp = plan_dhcp(
        address_plan=address,
        dns_servers=snapshot.networking.client_dns_servers,
    )
    dns = plan_dns(
        snapshot=snapshot,
        address_plan=address,
        dhcp_plan=dhcp,
    )
    nat = plan_nat(
        topology_plan=topology,
        address_plan=address,
    )
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
    radius = plan_radius(
        snapshot=snapshot,
        hotspot_plan=hotspot_plan,
    )
    firewall = plan_firewall(
        topology_plan=topology,
        address_plan=address,
        dns_plan=dns,
        nat_plan=nat,
        hotspot_plan=hotspot_plan,
        portal_plan=portal,
        radius_plan=radius,
    )

    wireless = plan_wireless(
        capabilities=capabilities,
        ssid="MAIN_caiwave",
    )

    bundle = build_provisioning_bundle(
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
        wireless=wireless,
    )

    context = build_render_context(
        section_order=[
            RouterOSSectionName.HEADER,
            RouterOSSectionName.IDENTITY,
            RouterOSSectionName.INTERFACES,
            RouterOSSectionName.WIRELESS,
            RouterOSSectionName.BRIDGE,
            RouterOSSectionName.ADDRESSING,
            RouterOSSectionName.DHCP,
            RouterOSSectionName.DNS,
            RouterOSSectionName.NAT,
            RouterOSSectionName.HOTSPOT,
            RouterOSSectionName.PORTAL,
            RouterOSSectionName.RADIUS,
            RouterOSSectionName.FIREWALL,
            RouterOSSectionName.SCHEDULERS,
            RouterOSSectionName.VALIDATION,
            RouterOSSectionName.FOOTER,
        ]
    )

    artifact = render_routeros_bundle(
        bundle=bundle,
        context=context,
    )

    assert artifact.status.value == "rendered"
    assert "/interface wireless" in artifact.content
    assert 'mode="ap-bridge"' in artifact.content
    assert 'ssid="MAIN_caiwave"' in artifact.content
    assert 'numbers="wlan1"' in artifact.content

    assert "/ip dhcp-server add" in artifact.content
    assert "/ip hotspot add" in artifact.content
    assert "/radius add" in artifact.content
    assert "/ip firewall nat add" in artifact.content

    wireless_sections = [
        section
        for section in artifact.sections
        if section.name == RouterOSSectionName.WIRELESS
    ]

    assert len(wireless_sections) == 1
    assert wireless_sections[0].status.value == "rendered"
