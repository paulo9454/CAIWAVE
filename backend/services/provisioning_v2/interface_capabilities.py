"""
Interface Capability Model for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no route wiring
- no legacy provisioning changes

This module models router interfaces and their capabilities. It does not
decide final topology, create bridges, or assign WAN/LAN roles.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class InterfaceCapabilityError(ValueError):
    """Raised when interface capability data is invalid."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class InterfaceKind(str, Enum):
    ETHERNET = "ethernet"
    WIRELESS = "wireless"
    VLAN = "vlan"
    BRIDGE = "bridge"
    BONDING = "bonding"
    LTE = "lte"
    PPP = "ppp"
    VIRTUAL = "virtual"
    UNKNOWN = "unknown"


class InterfaceRoleHint(str, Enum):
    WAN_CANDIDATE = "wan_candidate"
    LAN_CANDIDATE = "lan_candidate"
    CLIENT_CANDIDATE = "client_candidate"
    MANAGEMENT_CANDIDATE = "management_candidate"
    UNKNOWN = "unknown"


class InterfaceCapability(StrictModel):
    name: str
    kind: InterfaceKind
    role_hints: List[InterfaceRoleHint] = Field(default_factory=list)
    mac_address: Optional[str] = None
    parent: Optional[str] = None
    vlan_id: Optional[int] = None
    supports_bridge_port: bool = False
    supports_hotspot_client: bool = False
    supports_wan: bool = False
    is_dynamic: bool = False
    is_disabled: bool = False
    raw: Dict[str, Any] = Field(default_factory=dict)


def infer_interface_kind(name: str, raw_type: str | None = None) -> InterfaceKind:
    text = f"{name} {raw_type or ''}".lower()

    if text.startswith("ether") or "ethernet" in text:
        return InterfaceKind.ETHERNET
    if text.startswith("wlan") or "wireless" in text or "wifi" in text:
        return InterfaceKind.WIRELESS
    if text.startswith("vlan") or "vlan" in text:
        return InterfaceKind.VLAN
    if text.startswith("bridge") or "bridge" in text:
        return InterfaceKind.BRIDGE
    if text.startswith("bond") or "bonding" in text:
        return InterfaceKind.BONDING
    if text.startswith("lte") or "lte" in text:
        return InterfaceKind.LTE
    if text.startswith("ppp") or "pppoe" in text:
        return InterfaceKind.PPP
    if "virtual" in text or "tun" in text or "tap" in text:
        return InterfaceKind.VIRTUAL

    return InterfaceKind.UNKNOWN


def capability_from_dict(item: Dict[str, Any]) -> InterfaceCapability:
    if not isinstance(item, dict):
        raise InterfaceCapabilityError("Interface item must be a dictionary")

    name = str(item.get("name") or "").strip()
    if not name:
        raise InterfaceCapabilityError("Interface name is required")

    raw_type = item.get("type") or item.get("kind")
    kind = infer_interface_kind(name, str(raw_type) if raw_type else None)

    disabled = bool(item.get("disabled", False))
    dynamic = bool(item.get("dynamic", False))

    supports_bridge_port = kind in {
        InterfaceKind.ETHERNET,
        InterfaceKind.WIRELESS,
        InterfaceKind.VLAN,
        InterfaceKind.BONDING,
    }
    supports_hotspot_client = kind in {
        InterfaceKind.ETHERNET,
        InterfaceKind.WIRELESS,
        InterfaceKind.VLAN,
        InterfaceKind.BRIDGE,
        InterfaceKind.BONDING,
    }
    supports_wan = kind in {
        InterfaceKind.ETHERNET,
        InterfaceKind.VLAN,
        InterfaceKind.LTE,
        InterfaceKind.PPP,
        InterfaceKind.BONDING,
    }

    role_hints: List[InterfaceRoleHint] = []
    if supports_wan and not disabled:
        role_hints.append(InterfaceRoleHint.WAN_CANDIDATE)
    if supports_bridge_port and not disabled:
        role_hints.append(InterfaceRoleHint.LAN_CANDIDATE)
    if supports_hotspot_client and not disabled:
        role_hints.append(InterfaceRoleHint.CLIENT_CANDIDATE)
    if not role_hints:
        role_hints.append(InterfaceRoleHint.UNKNOWN)

    return InterfaceCapability(
        name=name,
        kind=kind,
        role_hints=role_hints,
        mac_address=item.get("mac_address") or item.get("mac-address"),
        parent=item.get("parent"),
        vlan_id=item.get("vlan_id"),
        supports_bridge_port=supports_bridge_port,
        supports_hotspot_client=supports_hotspot_client,
        supports_wan=supports_wan,
        is_dynamic=dynamic,
        is_disabled=disabled,
        raw=dict(item),
    )


def build_interface_capabilities(
    interfaces: List[Dict[str, Any]],
) -> List[InterfaceCapability]:
    """
    Build interface capability records from raw interface dictionaries.

    This does not assign final WAN/LAN/hotspot topology.
    """

    if not isinstance(interfaces, list):
        raise InterfaceCapabilityError("interfaces must be a list")

    capabilities = [capability_from_dict(item) for item in interfaces]

    names = [item.name for item in capabilities]
    if len(names) != len(set(names)):
        raise InterfaceCapabilityError("Duplicate interface names are not allowed")

    return capabilities
