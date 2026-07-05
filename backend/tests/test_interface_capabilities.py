import pytest

from backend.services.provisioning_v2.interface_capabilities import (
    InterfaceCapabilityError,
    InterfaceKind,
    InterfaceRoleHint,
    build_interface_capabilities,
    capability_from_dict,
    infer_interface_kind,
)


def test_infers_interface_kind_from_common_names():
    assert infer_interface_kind("ether1") == InterfaceKind.ETHERNET
    assert infer_interface_kind("wlan1") == InterfaceKind.WIRELESS
    assert infer_interface_kind("vlan10") == InterfaceKind.VLAN
    assert infer_interface_kind("bridge-hotspot") == InterfaceKind.BRIDGE
    assert infer_interface_kind("lte1") == InterfaceKind.LTE
    assert infer_interface_kind("pppoe-out1") == InterfaceKind.PPP


def test_builds_capability_from_ethernet():
    cap = capability_from_dict({"name": "ether1", "type": "ether"})

    assert cap.kind == InterfaceKind.ETHERNET
    assert cap.supports_wan is True
    assert cap.supports_bridge_port is True
    assert InterfaceRoleHint.WAN_CANDIDATE in cap.role_hints
    assert InterfaceRoleHint.LAN_CANDIDATE in cap.role_hints


def test_builds_capability_from_wireless():
    cap = capability_from_dict({"name": "wlan1", "type": "wireless"})

    assert cap.kind == InterfaceKind.WIRELESS
    assert cap.supports_hotspot_client is True
    assert cap.supports_bridge_port is True
    assert cap.supports_wan is False


def test_disabled_interface_gets_unknown_role_hint():
    cap = capability_from_dict({"name": "ether2", "disabled": True})

    assert cap.is_disabled is True
    assert cap.role_hints == [InterfaceRoleHint.UNKNOWN]


def test_rejects_missing_name():
    with pytest.raises(InterfaceCapabilityError):
        capability_from_dict({"type": "ether"})


def test_rejects_duplicate_names():
    with pytest.raises(InterfaceCapabilityError):
        build_interface_capabilities([
            {"name": "ether1"},
            {"name": "ether1"},
        ])


def test_builds_multiple_capabilities():
    caps = build_interface_capabilities([
        {"name": "ether1"},
        {"name": "ether2"},
        {"name": "wlan1"},
        {"name": "bridge-hotspot"},
    ])

    assert len(caps) == 4
    assert [cap.name for cap in caps] == [
        "ether1",
        "ether2",
        "wlan1",
        "bridge-hotspot",
    ]


def test_unknown_interface_kind_is_safe():
    cap = capability_from_dict({"name": "mystery0"})

    assert cap.kind == InterfaceKind.UNKNOWN
    assert cap.role_hints == [InterfaceRoleHint.UNKNOWN]
