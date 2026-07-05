import pytest

from backend.services.provisioning_v2.interface_capabilities import InterfaceKind
from backend.services.provisioning_v2.interface_classification import (
    InterfaceClassificationError,
    InterfaceClassificationLabel,
    InterfaceLayer,
    classify_interface_inventory,
)
from backend.services.provisioning_v2.interface_inventory import (
    InterfaceInventory,
    build_interface_inventory,
)


def inventory():
    return build_interface_inventory(
        router_id="router-1",
        interfaces=[
            {"name": "ether1"},
            {"name": "wlan1"},
            {"name": "bridge-hotspot"},
            {"name": "vlan20", "parent": "ether2", "vlan_id": 20},
            {"name": "pppoe-out1"},
            {"name": "lte1"},
            {"name": "mystery0"},
        ],
    )


def test_classifies_common_interfaces():
    classified = {item.name: item for item in classify_interface_inventory(inventory())}

    assert classified["ether1"].classification == InterfaceClassificationLabel.PHYSICAL_ETHERNET
    assert classified["ether1"].layer == InterfaceLayer.PHYSICAL
    assert classified["ether1"].physical is True

    assert classified["wlan1"].classification == InterfaceClassificationLabel.PHYSICAL_WIRELESS
    assert classified["bridge-hotspot"].classification == InterfaceClassificationLabel.LOGICAL_BRIDGE
    assert classified["vlan20"].classification == InterfaceClassificationLabel.LOGICAL_VLAN
    assert classified["pppoe-out1"].classification == InterfaceClassificationLabel.LOGICAL_PPP
    assert classified["lte1"].classification == InterfaceClassificationLabel.LOGICAL_LTE
    assert classified["mystery0"].classification == InterfaceClassificationLabel.UNKNOWN


def test_preserves_order_and_index():
    classified = classify_interface_inventory(inventory())

    assert [item.name for item in classified] == [
        "ether1",
        "wlan1",
        "bridge-hotspot",
        "vlan20",
        "pppoe-out1",
        "lte1",
        "mystery0",
    ]
    assert [item.index for item in classified] == list(range(7))


def test_classification_is_descriptive_not_prescriptive():
    classified = classify_interface_inventory(inventory())

    for item in classified:
        dumped = item.model_dump()
        assert "wan_interface" not in dumped
        assert "lan_interface" not in dumped
        assert "client_interface" not in dumped
        assert "hotspot_interface" not in dumped


def test_dynamic_and_disabled_flags_are_preserved():
    inv = build_interface_inventory(
        router_id="router-1",
        interfaces=[
            {"name": "ether1", "dynamic": True, "disabled": True},
        ],
    )

    item = classify_interface_inventory(inv)[0]

    assert item.dynamic is True
    assert item.disabled is True


def test_parent_is_preserved_for_vlan():
    classified = {item.name: item for item in classify_interface_inventory(inventory())}

    assert classified["vlan20"].parent == "ether2"


def test_empty_inventory_is_rejected():
    empty = InterfaceInventory(router_id="router-1", interfaces=[])

    with pytest.raises(InterfaceClassificationError):
        classify_interface_inventory(empty)


def test_kind_is_preserved():
    classified = {item.name: item for item in classify_interface_inventory(inventory())}

    assert classified["ether1"].kind == InterfaceKind.ETHERNET
    assert classified["bridge-hotspot"].kind == InterfaceKind.BRIDGE
