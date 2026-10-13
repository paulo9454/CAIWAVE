import pytest

from backend.services.provisioning_v2.router_discovery import (
    RouterDiscoveryError,
    build_router_discovery_snapshot,
)
from backend.services.provisioning_v2.router_discovery_models import (
    DiscoveredBridgePort,
    DiscoveredDHCPServer,
    DiscoveredHotspot,
    DiscoveredInterface,
    DiscoveredVLAN,
    RouterDiscoverySnapshot,
)


def test_duplicate_interface_names_rejected():
    snapshot = RouterDiscoverySnapshot(
        router_id="router-1",
        board_name="RB750Gr3",
        routeros_version="7.18",
        architecture="arm",
        interfaces=[
            DiscoveredInterface(
                name="ether1",
                type="ethernet",
            ),
            DiscoveredInterface(
                name="ether1",
                type="ethernet",
            ),
        ],
    )

    with pytest.raises(RouterDiscoveryError):
        build_router_discovery_snapshot(snapshot)

def test_vlan_parent_must_exist():
    snapshot = RouterDiscoverySnapshot(
        router_id="router-1",
        board_name="RB750",
        routeros_version="7.18",
        architecture="arm",
        interfaces=[
            DiscoveredInterface(
                name="ether1",
                type="ethernet",
            )
        ],
        vlans=[
            DiscoveredVLAN(
                name="vlan100",
                vlan_id=100,
                parent_interface="ether9",
            )
        ],
    )

    with pytest.raises(RouterDiscoveryError):
        build_router_discovery_snapshot(snapshot)

def test_bridge_port_bridge_must_exist():
    snapshot = RouterDiscoverySnapshot(
        router_id="router-1",
        board_name="RB750",
        routeros_version="7.18",
        architecture="arm",
        interfaces=[
            DiscoveredInterface(
                name="ether1",
                type="ethernet",
            )
        ],
        bridges=[],
        bridge_ports=[
            DiscoveredBridgePort(
                bridge_name="bridge-hotspot",
                interface_name="ether1",
            )
        ],
    )

    with pytest.raises(RouterDiscoveryError):
        build_router_discovery_snapshot(snapshot)

def test_dhcp_server_interface_must_exist():
    snapshot = RouterDiscoverySnapshot(
        router_id="router-1",
        board_name="RB750",
        routeros_version="7.18",
        architecture="arm",
        interfaces=[
            DiscoveredInterface(
                name="ether1",
                type="ethernet",
            )
        ],
        dhcp_servers=[
            DiscoveredDHCPServer(
                name="dhcp-hotspot",
                interface="bridge-hotspot",
                address_pool="10.10.0.10-10.10.0.254",
            )
        ],
    )

    with pytest.raises(RouterDiscoveryError):
        build_router_discovery_snapshot(snapshot)

def test_hotspot_interface_must_exist():
    snapshot = RouterDiscoverySnapshot(
        router_id="router-1",
        board_name="RB750",
        routeros_version="7.18",
        architecture="arm",
        interfaces=[
            DiscoveredInterface(
                name="ether1",
                type="ethernet",
            )
        ],
        hotspots=[
            DiscoveredHotspot(
                name="hotspot1",
                interface="bridge-hotspot",
                profile="caiwave-profile",
            )
        ],
    )

    with pytest.raises(RouterDiscoveryError):
        build_router_discovery_snapshot(snapshot)
