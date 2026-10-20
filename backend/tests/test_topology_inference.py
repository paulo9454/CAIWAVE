from backend.services.provisioning_v2.router_discovery_models import (
    DiscoveredAddress,
    DiscoveredBridge,
    DiscoveredBridgePort,
    DiscoveredDHCPClient,
    DiscoveredDHCPServer,
    DiscoveredHotspot,
    DiscoveredInterface,
    DiscoveredRoute,
    RouterDiscoverySnapshot,
)
from backend.services.provisioning_v2.topology_inference import (
    infer_topology,
)


def make_ns_jdoo_snapshot() -> RouterDiscoverySnapshot:
    return RouterDiscoverySnapshot(
        router_id="nsjdoo",
        board_name="test-router",
        routeros_version="7.x",
        architecture="unknown",
        interfaces=[
            DiscoveredInterface(name="ether1", type="ethernet"),
            DiscoveredInterface(name="ether2", type="ethernet"),
            DiscoveredInterface(name="ether3", type="ethernet"),
            DiscoveredInterface(name="bridge-hotspot", type="bridge"),
        ],
        bridges=[
            DiscoveredBridge(name="bridge-hotspot"),
        ],
        bridge_ports=[
            DiscoveredBridgePort(
                interface_name="ether2",
                bridge_name="bridge-hotspot",
            ),
            DiscoveredBridgePort(
                interface_name="ether3",
                bridge_name="bridge-hotspot",
            ),
        ],
        addresses=[
            DiscoveredAddress(
                address="192.168.150.107/24",
                interface="ether1",
            ),
            DiscoveredAddress(
                address="10.10.0.1/24",
                interface="bridge-hotspot",
            ),
        ],
        routes=[
            DiscoveredRoute(
                destination="0.0.0.0/0",
                gateway="192.168.150.1",
                interface="ether1",
            ),
            DiscoveredRoute(
                destination="192.168.150.0/24",
                gateway="",
                interface="ether1",
            ),
            DiscoveredRoute(
                destination="10.10.0.0/24",
                gateway="",
                interface="bridge-hotspot",
            ),
        ],
        dhcp_servers=[
            DiscoveredDHCPServer(
                name="caiwave-dhcp",
                address_pool="caiwave-pool-hotspot",
                interface="bridge-hotspot",
            ),
        ],
        hotspots=[
            DiscoveredHotspot(
                name="caiwave-hotspot",
                profile="caiwave-profile",
                interface="bridge-hotspot",
            ),
        ],
        dhcp_clients=[
            DiscoveredDHCPClient(
                interface="ether1",
                address="192.168.150.107/24",
                gateway="192.168.150.1",
                status="bound",
            ),
        ],
    )


def test_static_default_route_uses_gateway_subnet_without_dhcp_client():
    snapshot = make_ns_jdoo_snapshot().model_copy(
        update={
            "dhcp_clients": [],
            "routes": [
                DiscoveredRoute(
                    destination="0.0.0.0/0",
                    gateway="192.168.150.1",
                    interface=None,
                )
            ],
        }
    )

    result = infer_topology(snapshot)

    assert result.status == "INFERRED"
    assert result.wan_interface == "ether1"
    assert result.confidence == "MEDIUM"


def test_static_default_route_uses_discovered_routeros_gateway_interface():
    snapshot = make_ns_jdoo_snapshot().model_copy(
        update={
            "addresses": [],
            "dhcp_clients": [],
            "routes": [
                DiscoveredRoute(
                    destination="0.0.0.0/0",
                    gateway="203.0.113.1%ether1",
                    interface=None,
                )
            ],
        }
    )

    result = infer_topology(snapshot)

    assert result.status == "INFERRED"
    assert result.wan_interface == "ether1"
    assert result.confidence == "MEDIUM"


def test_ns_jdoo_topology_is_high_confidence():
    result = infer_topology(make_ns_jdoo_snapshot())

    assert result.status == "INFERRED"
    assert result.confidence == "HIGH"
    assert result.wan_interface == "ether1"

    assert result.client_bridge_interfaces == ["bridge-hotspot"]

    assert "ether2" in result.client_interfaces
    assert "ether3" in result.client_interfaces


def test_inference_does_not_guess_when_wan_evidence_is_ambiguous():
    snapshot = make_ns_jdoo_snapshot()

    snapshot = snapshot.model_copy(
        update={
            "dhcp_clients": [
                DiscoveredDHCPClient(
                    interface="ether1",
                    address="192.168.150.107/24",
                    gateway="192.168.150.1",
                    status="bound",
                ),
                DiscoveredDHCPClient(
                    interface="ether2",
                    address="192.168.151.107/24",
                    gateway="192.168.151.1",
                    status="bound",
                ),
            ],
            "routes": [
                DiscoveredRoute(
                    destination="0.0.0.0/0",
                    gateway="192.168.150.1",
                    interface="ether1",
                ),
                DiscoveredRoute(
                    destination="0.0.0.0/0",
                    gateway="192.168.151.1",
                    interface="ether2",
                ),
            ],
        }
    )

    result = infer_topology(snapshot)

    assert result.status == "AMBIGUOUS"
    assert result.wan_interface is None
    assert result.confidence == "LOW"

def test_fresh_router_uses_enabled_disconnected_ethernet_ports_as_clients():
    snapshot = RouterDiscoverySnapshot(
        router_id="fresh-rb750",
        board_name="RB750",
        routeros_version="7.24.5",
        architecture="mipsbe",
        interfaces=[
            DiscoveredInterface(
                name="ether1",
                type="ethernet",
                running=True,
                disabled=False,
            ),
            DiscoveredInterface(
                name="ether2",
                type="ethernet",
                running=False,
                disabled=False,
            ),
            DiscoveredInterface(
                name="ether3",
                type="ethernet",
                running=False,
                disabled=False,
            ),
            DiscoveredInterface(
                name="ether4",
                type="ethernet",
                running=False,
                disabled=False,
            ),
            DiscoveredInterface(
                name="ether5",
                type="ethernet",
                running=False,
                disabled=False,
            ),
        ],
        dhcp_clients=[
            DiscoveredDHCPClient(
                interface="ether1",
                address="192.168.8.107/24",
                gateway="192.168.8.1",
                status="bound",
            ),
        ],
        routes=[
            DiscoveredRoute(
                destination="0.0.0.0/0",
                gateway="192.168.8.1",
                interface=None,
            ),
        ],
    )

    result = infer_topology(snapshot)

    assert result.status == "INFERRED"
    assert result.wan_interface == "ether1"
    assert result.client_interfaces == [
        "ether2",
        "ether3",
        "ether4",
        "ether5",
    ]
    assert result.client_bridge_interfaces == []

def test_inference_uses_topology_evidence_not_interface_names():
    snapshot = RouterDiscoverySnapshot(
        router_id="router-named-differently",
        board_name="different-router",
        routeros_version="7.x",
        architecture="arm",
        interfaces=[
            DiscoveredInterface(
                name="sfp-sfpplus1",
                type="ethernet",
            ),
            DiscoveredInterface(
                name="ether7",
                type="ethernet",
            ),
            DiscoveredInterface(
                name="ether8",
                type="ethernet",
            ),
            DiscoveredInterface(
                name="hotspot-lan",
                type="bridge",
            ),
        ],
        bridges=[
            DiscoveredBridge(
                name="hotspot-lan",
            ),
        ],
        bridge_ports=[
            DiscoveredBridgePort(
                interface_name="ether7",
                bridge_name="hotspot-lan",
            ),
            DiscoveredBridgePort(
                interface_name="ether8",
                bridge_name="hotspot-lan",
            ),
        ],
        addresses=[
            DiscoveredAddress(
                address="172.16.1.10/24",
                interface="sfp-sfpplus1",
            ),
            DiscoveredAddress(
                address="10.20.0.1/24",
                interface="hotspot-lan",
            ),
        ],
        routes=[
            DiscoveredRoute(
                destination="0.0.0.0/0",
                gateway="172.16.1.1",
                interface="sfp-sfpplus1",
            ),
            DiscoveredRoute(
                destination="10.20.0.0/24",
                gateway="",
                interface="hotspot-lan",
            ),
        ],
        dhcp_servers=[
            DiscoveredDHCPServer(
                name="hotspot-dhcp",
                address_pool="hotspot-pool",
                interface="hotspot-lan",
            ),
        ],
        hotspots=[
            DiscoveredHotspot(
                name="hotspot",
                profile="hotspot-profile",
                interface="hotspot-lan",
            ),
        ],
        dhcp_clients=[
            DiscoveredDHCPClient(
                interface="sfp-sfpplus1",
                address="172.16.1.10/24",
                gateway="172.16.1.1",
                status="bound",
            ),
        ],
    )

    result = infer_topology(snapshot)

    assert result.status == "INFERRED"
    assert result.confidence == "HIGH"
    assert result.wan_interface == "sfp-sfpplus1"
    assert result.client_bridge_interfaces == ["hotspot-lan"]
    assert result.client_interfaces == ["ether7", "ether8"]
