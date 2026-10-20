"""
Interface Classification for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no route wiring
- no legacy provisioning changes

Classification is descriptive only. It describes what an interface is; it
does not assign WAN/LAN/client roles or plan topology.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from backend.services.provisioning_v2.interface_capabilities import InterfaceKind
from backend.services.provisioning_v2.interface_inventory import (
    InterfaceInventory,
    InterfaceInventoryItem,
)


class InterfaceClassificationError(ValueError):
    """Raised when interface classification cannot be completed."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class InterfaceLayer(str, Enum):
    PHYSICAL = "physical"
    LOGICAL = "logical"
    VIRTUAL = "virtual"
    UNKNOWN = "unknown"


class InterfaceClassificationLabel(str, Enum):
    PHYSICAL_ETHERNET = "physical_ethernet"
    PHYSICAL_WIRELESS = "physical_wireless"
    LOGICAL_BRIDGE = "logical_bridge"
    LOGICAL_VLAN = "logical_vlan"
    LOGICAL_BONDING = "logical_bonding"
    LOGICAL_LTE = "logical_lte"
    LOGICAL_PPP = "logical_ppp"
    VIRTUAL_INTERFACE = "virtual_interface"
    UNKNOWN = "unknown"


class ClassifiedInterface(StrictModel):
    name: str
    index: int
    kind: InterfaceKind
    layer: InterfaceLayer
    classification: InterfaceClassificationLabel
    physical: bool
    logical: bool
    dynamic: bool
    disabled: bool
    parent: Optional[str] = None
    source: str


def classify_inventory_item(item: InterfaceInventoryItem) -> ClassifiedInterface:
    capability = item.capability
    kind = capability.kind

    if kind == InterfaceKind.ETHERNET:
        layer = InterfaceLayer.PHYSICAL
        label = InterfaceClassificationLabel.PHYSICAL_ETHERNET
    elif kind == InterfaceKind.WIRELESS:
        layer = InterfaceLayer.PHYSICAL
        label = InterfaceClassificationLabel.PHYSICAL_WIRELESS
    elif kind == InterfaceKind.BRIDGE:
        layer = InterfaceLayer.LOGICAL
        label = InterfaceClassificationLabel.LOGICAL_BRIDGE
    elif kind == InterfaceKind.VLAN:
        layer = InterfaceLayer.LOGICAL
        label = InterfaceClassificationLabel.LOGICAL_VLAN
    elif kind == InterfaceKind.BONDING:
        layer = InterfaceLayer.LOGICAL
        label = InterfaceClassificationLabel.LOGICAL_BONDING
    elif kind == InterfaceKind.LTE:
        layer = InterfaceLayer.LOGICAL
        label = InterfaceClassificationLabel.LOGICAL_LTE
    elif kind == InterfaceKind.PPP:
        layer = InterfaceLayer.LOGICAL
        label = InterfaceClassificationLabel.LOGICAL_PPP
    elif kind == InterfaceKind.VIRTUAL:
        layer = InterfaceLayer.VIRTUAL
        label = InterfaceClassificationLabel.VIRTUAL_INTERFACE
    else:
        layer = InterfaceLayer.UNKNOWN
        label = InterfaceClassificationLabel.UNKNOWN

    return ClassifiedInterface(
        name=item.name,
        index=item.index,
        kind=kind,
        layer=layer,
        classification=label,
        physical=layer == InterfaceLayer.PHYSICAL,
        logical=layer in {InterfaceLayer.LOGICAL, InterfaceLayer.VIRTUAL},
        dynamic=capability.is_dynamic,
        disabled=capability.is_disabled,
        parent=capability.parent,
        source=item.source,
    )


def classify_interface_inventory(
    inventory: InterfaceInventory,
) -> List[ClassifiedInterface]:
    """
    Classify inventory interfaces descriptively.

    This does not assign WAN/LAN/client roles.
    """

    if not inventory.interfaces:
        raise InterfaceClassificationError("inventory contains no interfaces")

    return [classify_inventory_item(item) for item in inventory.interfaces]
