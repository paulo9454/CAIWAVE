from backend.services.provisioning_v2.router_discovery_inventory_adapter import (
    build_inventory_from_discovery,
)
from backend.services.provisioning_v2.router_discovery_models import (
    DiscoveredInterface,
    RouterDiscoverySnapshot,
)
from backend.services.provisioning_v2.interface_capabilities import (
    InterfaceKind,
)


def test_discovery_snapshot_builds_inventory():
    snapshot = RouterDiscoverySnapshot(
        router_id="router-1",
        board_name="RB750",
        routeros_version="7.18",
        architecture="arm",
        interfaces=[
            DiscoveredInterface(
                name="ether1",
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

    inventory = build_inventory_from_discovery(snapshot)

    assert inventory.router_id == "router-1"
    assert inventory.source == "discovery"
    assert inventory.names == ["ether1", "wlan1"]

    assert inventory.get("ether1").capability.kind == InterfaceKind.ETHERNET
    assert inventory.get("wlan1").capability.kind == InterfaceKind.WIRELESS


def test_discovery_inventory_rejects_duplicate_interfaces():
    snapshot = RouterDiscoverySnapshot(
        router_id="router-1",
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

    from backend.services.provisioning_v2.router_discovery import (
        RouterDiscoveryError,
    )

    import pytest

    with pytest.raises(RouterDiscoveryError):
        build_inventory_from_discovery(snapshot)
