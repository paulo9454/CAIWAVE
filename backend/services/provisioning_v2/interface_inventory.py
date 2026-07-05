"""
Interface Inventory for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no route wiring
- no legacy provisioning changes

This module normalizes raw router interface data into an immutable inventory.
It does not assign WAN/LAN/client roles and does not plan topology.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.services.provisioning_v2.interface_capabilities import (
    InterfaceCapability,
    InterfaceCapabilityError,
    build_interface_capabilities,
)


class InterfaceInventoryError(ValueError):
    """Raised when interface inventory data is invalid."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class InterfaceInventoryItem(StrictModel):
    name: str
    index: int
    capability: InterfaceCapability
    source: str = "declared"
    comment: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InterfaceInventory(StrictModel):
    router_id: str
    interfaces: List[InterfaceInventoryItem]
    source: str = "declared"

    @property
    def names(self) -> List[str]:
        return [item.name for item in self.interfaces]

    def get(self, name: str) -> InterfaceInventoryItem | None:
        for item in self.interfaces:
            if item.name == name:
                return item
        return None


def build_interface_inventory(
    *,
    router_id: str,
    interfaces: List[Dict[str, Any]],
    source: str = "declared",
) -> InterfaceInventory:
    """
    Build a validated immutable interface inventory from raw dictionaries.

    This preserves input ordering and delegates capability inference to the
    Interface Capability Model.
    """

    if not isinstance(router_id, str) or not router_id.strip():
        raise InterfaceInventoryError("router_id is required")
    if not isinstance(interfaces, list):
        raise InterfaceInventoryError("interfaces must be a list")
    if not interfaces:
        raise InterfaceInventoryError("at least one interface is required")

    try:
        capabilities = build_interface_capabilities(interfaces)
    except InterfaceCapabilityError as exc:
        raise InterfaceInventoryError(str(exc)) from exc

    items: List[InterfaceInventoryItem] = []
    for index, capability in enumerate(capabilities):
        raw = interfaces[index]
        items.append(
            InterfaceInventoryItem(
                name=capability.name,
                index=index,
                capability=capability,
                source=source,
                comment=raw.get("comment"),
                metadata={
                    key: value
                    for key, value in raw.items()
                    if key not in {"name", "type", "kind", "comment"}
                },
            )
        )

    return InterfaceInventory(
        router_id=router_id.strip(),
        interfaces=items,
        source=source,
    )
