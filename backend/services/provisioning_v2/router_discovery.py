"""
Router Discovery Builder for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no topology planning
- no provisioning mutation

This module validates and normalizes discovery snapshots.
"""

from __future__ import annotations

from backend.services.provisioning_v2.router_discovery_models import (
    RouterDiscoverySnapshot,
)


class RouterDiscoveryError(ValueError):
    """Raised when discovery data is invalid."""


def build_router_discovery_snapshot(
    snapshot: RouterDiscoverySnapshot,
) -> RouterDiscoverySnapshot:
    interface_names = [
        item.name
        for item in snapshot.interfaces
    ]

    if len(interface_names) != len(set(interface_names)):
        raise RouterDiscoveryError(
            "Duplicate discovered interface names"
        )

    bridge_names = [
        item.name
        for item in snapshot.bridges
    ]

    if len(bridge_names) != len(set(bridge_names)):
        raise RouterDiscoveryError(
            "Duplicate discovered bridge names"
        )

    return snapshot
