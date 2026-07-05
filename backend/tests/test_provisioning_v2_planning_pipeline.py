from backend.services.provisioning_v2.bridge_planner import BridgeAction, plan_bridge
from backend.services.provisioning_v2.interface_classification import classify_interface_inventory
from backend.services.provisioning_v2.interface_inventory import build_interface_inventory
from backend.services.provisioning_v2.snapshot_builder import build_provisioning_snapshot
from backend.services.provisioning_v2.topology_planner import BridgeStrategy, plan_topology


def test_snapshot_to_bridge_planning_pipeline():
    router = {
        "id": "router-1",
        "name": "GOODlife",
        "owner_id": "owner-1",
        "hotspot_id": "hotspot-1",
        "nas_identifier": "CAIWAVE-GOODLIFE",
        "wan_interface": "sfp1",
        "lan_interfaces": ["ether5", "wlan1"],
        "create_bridge": True,
        "bridge_name": "client-bridge",
        "effective_lan_interface": "client-bridge",
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
        interfaces=[
            {"name": "sfp1"},
            {"name": "ether5"},
            {"name": "wlan1"},
        ],
        source="declared",
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

    assert topology.upstream_interface == "sfp1"
    assert topology.client_interfaces == ["ether5", "wlan1"]
    assert topology.bridge_strategy == BridgeStrategy.CREATE
    assert bridge.action == BridgeAction.CREATE
    assert bridge.bridge_name == "client-bridge"
    assert bridge.members == ["ether5", "wlan1"]
    assert bridge.excluded_interfaces == ["sfp1"]


def test_planning_pipeline_reuses_existing_bridge():
    router = {
        "id": "router-2",
        "name": "CAINET",
        "owner_id": "owner-1",
        "hotspot_id": "hotspot-2",
        "nas_identifier": "CAIWAVE-CAINET",
        "wan_interface": "ether1",
        "lan_interfaces": ["ether2", "ether3"],
        "create_bridge": True,
        "bridge_name": "bridge-hotspot",
        "effective_lan_interface": "bridge-hotspot",
        "mode": "existing",
        "hotspot_cidr": "10.20.0.0/24",
        "hotspot_gateway": "10.20.0.1",
        "dhcp_pool": "10.20.0.10-10.20.0.254",
        "dns_name": "wifi.caiwave.com",
    }
    hotspot = {"id": "hotspot-2", "owner_id": "owner-1"}
    config = {
        "radius_host": "radius.caiwave.com",
        "portal_public_url": "https://caiwave.com/portal",
        "api_public_url": "https://caiwave.com/api",
        "heartbeat_url": "https://caiwave.com/api/mikrotik-onboard/heartbeat",
    }

    snapshot = build_provisioning_snapshot(router, hotspot, config)

    inventory = build_interface_inventory(
        router_id=snapshot.router_id,
        interfaces=[
            {"name": "ether1"},
            {"name": "ether2"},
            {"name": "ether3"},
            {"name": "bridge-hotspot"},
        ],
        source="declared",
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

    assert topology.bridge_strategy == BridgeStrategy.REUSE
    assert bridge.action == BridgeAction.REUSE
    assert bridge.bridge_name == "bridge-hotspot"
    assert bridge.members == ["ether2", "ether3"]
