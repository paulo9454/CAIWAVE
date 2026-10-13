"""
Adapter from Router Discovery snapshots to Provisioning Engine v2 inventory.

Safety:
- no database access
- no RouterOS generation
- no topology planning
- no existing inventory mutation

This adapter converts validated discovery facts into the existing
Interface Inventory input contract.
"""

from __future__ import annotations

from backend.services.provisioning_v2.interface_inventory import (
    InterfaceInventory,
    build_interface_inventory,
)
from backend.services.provisioning_v2.router_discovery import (
    build_router_discovery_snapshot,
)
from backend.services.provisioning_v2.router_discovery_models import (
    RouterDiscoverySnapshot,
)


def build_inventory_from_discovery(
    snapshot: RouterDiscoverySnapshot,
) -> InterfaceInventory:
    """
    Convert a validated RouterDiscoverySnapshot into the existing
    InterfaceInventory contract.
    """

    validated = build_router_discovery_snapshot(snapshot)

    interfaces = [
        {
            "name": interface.name,
            "type": interface.type,
            "disabled": interface.disabled,
            "mac_address": interface.mac_address,
            "running": interface.running,
            "source": "discovery",
            **interface.model_dump(
                exclude={
                    "name",
                    "type",
                    "disabled",
                    "mac_address",
                    "running",
                }
            ),
        }
        for interface in validated.interfaces
    ]

    return build_interface_inventory(
        router_id=validated.router_id,
        interfaces=interfaces,
        source="discovery",
    )
