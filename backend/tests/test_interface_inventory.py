import pytest

from backend.services.provisioning_v2.interface_capabilities import InterfaceKind
from backend.services.provisioning_v2.interface_inventory import (
    InterfaceInventoryError,
    build_interface_inventory,
)


def test_builds_inventory_preserving_order():
    inventory = build_interface_inventory(
        router_id="router-1",
        interfaces=[
            {"name": "ether1"},
            {"name": "ether2"},
            {"name": "wlan1"},
        ],
    )

    assert inventory.router_id == "router-1"
    assert inventory.names == ["ether1", "ether2", "wlan1"]
    assert inventory.interfaces[0].index == 0
    assert inventory.interfaces[2].capability.kind == InterfaceKind.WIRELESS


def test_get_interface_by_name():
    inventory = build_interface_inventory(
        router_id="router-1",
        interfaces=[{"name": "ether1"}, {"name": "bridge-hotspot"}],
    )

    assert inventory.get("bridge-hotspot").name == "bridge-hotspot"
    assert inventory.get("missing") is None


def test_rejects_missing_router_id():
    with pytest.raises(InterfaceInventoryError):
        build_interface_inventory(router_id="", interfaces=[{"name": "ether1"}])


def test_rejects_empty_interfaces():
    with pytest.raises(InterfaceInventoryError):
        build_interface_inventory(router_id="router-1", interfaces=[])


def test_rejects_duplicate_interface_names():
    with pytest.raises(InterfaceInventoryError):
        build_interface_inventory(
            router_id="router-1",
            interfaces=[{"name": "ether1"}, {"name": "ether1"}],
        )


def test_inventory_is_immutable():
    inventory = build_interface_inventory(
        router_id="router-1",
        interfaces=[{"name": "ether1"}],
    )

    with pytest.raises(Exception):
        inventory.router_id = "changed"


def test_preserves_comment_and_metadata():
    inventory = build_interface_inventory(
        router_id="router-1",
        interfaces=[
            {
                "name": "ether1",
                "comment": "WAN uplink",
                "mac_address": "AA:BB:CC:DD:EE:FF",
                "disabled": False,
            }
        ],
        source="router_reported",
    )

    item = inventory.get("ether1")
    assert item.comment == "WAN uplink"
    assert item.source == "router_reported"
    assert item.metadata["mac_address"] == "AA:BB:CC:DD:EE:FF"
