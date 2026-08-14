import pytest

from backend.services.provisioning_v2.router_capabilities import (
    RouterCapabilityFacts,
    detect_router_capabilities,
)
from backend.services.provisioning_v2.router_discovery_models import (
    DiscoveredInterface,
    RouterDiscoverySnapshot,
)


def test_wireless_capability_is_derived_from_discovered_interface():
    snapshot = RouterDiscoverySnapshot(
        router_id="router-1",
        board_name="hAP",
        routeros_version="7.18",
        architecture="arm",
        interfaces=[
            DiscoveredInterface(
                name="ether1",
                type="ethernet",
            ),
            DiscoveredInterface(
                name="wlan1",
                type="wireless",
            ),
        ],
    )

    capabilities = detect_router_capabilities(snapshot)

    assert isinstance(capabilities, RouterCapabilityFacts)
    assert capabilities.supports_wireless is True
    assert capabilities.ethernet_interfaces == ["ether1"]
    assert capabilities.wireless_interfaces == ["wlan1"]
    assert capabilities.interface_count == 2


def test_router_without_wireless_is_reported_correctly():
    snapshot = RouterDiscoverySnapshot(
        router_id="router-2",
        board_name="hEX",
        routeros_version="7.18",
        architecture="arm",
        interfaces=[
            DiscoveredInterface(
                name="ether1",
                type="ethernet",
            ),
            DiscoveredInterface(
                name="ether2",
                type="ethernet",
            ),
        ],
    )

    capabilities = detect_router_capabilities(snapshot)

    assert capabilities.supports_wireless is False
    assert capabilities.wireless_interfaces == []
    assert capabilities.ethernet_interfaces == [
        "ether1",
        "ether2",
    ]


def test_invalid_discovery_snapshot_is_rejected():
    snapshot = RouterDiscoverySnapshot(
        router_id="router-3",
        board_name="RB750",
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

    with pytest.raises(ValueError):
        detect_router_capabilities(snapshot)
