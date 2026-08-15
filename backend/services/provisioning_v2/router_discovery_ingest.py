"""
Router Discovery Ingestion for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no provisioning decisions
- no production mutation

This module converts the raw discovery payload produced by the RouterOS
discovery renderer into the strict RouterDiscoverySnapshot contract.
"""

from __future__ import annotations

from typing import Any

from backend.services.provisioning_v2.router_discovery import (
    build_router_discovery_snapshot,
)
from backend.services.provisioning_v2.router_discovery_models import (
    DiscoveredAddress,
    DiscoveredBridge,
    DiscoveredInterface,
    DiscoveredRoute,
    DiscoveredVLAN,
    RouterDiscoverySnapshot,
)


class RouterDiscoveryIngestionError(ValueError):
    """Raised when a raw discovery payload cannot be normalized safely."""


def _required_string(
    data: dict[str, Any],
    field: str,
    path: str,
) -> str:
    value = data.get(field)

    if value is None:
        raise RouterDiscoveryIngestionError(
            f"Missing required discovery field: {path}.{field}"
        )

    value = str(value).strip()

    if not value:
        raise RouterDiscoveryIngestionError(
            f"Blank required discovery field: {path}.{field}"
        )

    return value


def _normalize_interfaces(
    values: Any,
) -> list[DiscoveredInterface]:
    if not isinstance(values, list):
        raise RouterDiscoveryIngestionError(
            "interfaces must be a list"
        )

    result: list[DiscoveredInterface] = []

    for item in values:
        if not isinstance(item, dict):
            raise RouterDiscoveryIngestionError(
                "Each discovered interface must be an object"
            )

        name = str(item.get("name") or "").strip()
        if not name:
            raise RouterDiscoveryIngestionError(
                "Discovered interface name is required"
            )

        interface_type = str(
            item.get("type")
            or item.get("kind")
            or ""
        ).strip()

        if not interface_type:
            raise RouterDiscoveryIngestionError(
                f"Discovered interface type is required: {name}"
            )

        result.append(
            DiscoveredInterface(
                name=name,
                type=interface_type,
                running=bool(item.get("running", False)),
                disabled=bool(item.get("disabled", False)),
                mac_address=(
                    item.get("mac_address")
                    or item.get("mac-address")
                ),
            )
        )

    return result


def _normalize_bridges(
    values: Any,
) -> list[DiscoveredBridge]:
    if not isinstance(values, list):
        raise RouterDiscoveryIngestionError(
            "bridges must be a list"
        )

    result: list[DiscoveredBridge] = []

    for item in values:
        if not isinstance(item, dict):
            raise RouterDiscoveryIngestionError(
                "Each discovered bridge must be an object"
            )

        name = str(item.get("name") or "").strip()
        if not name:
            raise RouterDiscoveryIngestionError(
                "Discovered bridge name is required"
            )

        result.append(
            DiscoveredBridge(
                name=name,
                running=bool(item.get("running", False)),
            )
        )

    return result


def _normalize_vlans(
    values: Any,
) -> list[DiscoveredVLAN]:
    if not isinstance(values, list):
        raise RouterDiscoveryIngestionError(
            "vlans must be a list"
        )

    result: list[DiscoveredVLAN] = []

    for item in values:
        if not isinstance(item, dict):
            raise RouterDiscoveryIngestionError(
                "Each discovered VLAN must be an object"
            )

        name = str(item.get("name") or "").strip()
        parent = str(
            item.get("parent_interface")
            or item.get("interface")
            or ""
        ).strip()

        if not name:
            raise RouterDiscoveryIngestionError(
                "Discovered VLAN name is required"
            )

        if not parent:
            raise RouterDiscoveryIngestionError(
                f"Discovered VLAN parent is required: {name}"
            )

        try:
            vlan_id = int(
                item.get("vlan_id")
                if item.get("vlan_id") is not None
                else item.get("vlan-id")
            )
        except (TypeError, ValueError) as exc:
            raise RouterDiscoveryIngestionError(
                f"Invalid VLAN ID: {name}"
            ) from exc

        result.append(
            DiscoveredVLAN(
                name=name,
                vlan_id=vlan_id,
                parent_interface=parent,
            )
        )

    return result


def _normalize_addresses(
    values: Any,
) -> list[DiscoveredAddress]:
    if not isinstance(values, list):
        raise RouterDiscoveryIngestionError(
            "addresses must be a list"
        )

    result: list[DiscoveredAddress] = []

    for item in values:
        if not isinstance(item, dict):
            raise RouterDiscoveryIngestionError(
                "Each discovered address must be an object"
            )

        interface = str(
            item.get("interface")
            or ""
        ).strip()
        address = str(
            item.get("address")
            or ""
        ).strip()

        if not interface:
            raise RouterDiscoveryIngestionError(
                "Discovered address interface is required"
            )

        if not address:
            raise RouterDiscoveryIngestionError(
                "Discovered address value is required"
            )

        result.append(
            DiscoveredAddress(
                interface=interface,
                address=address,
            )
        )

    return result


def _normalize_routes(
    values: Any,
) -> list[DiscoveredRoute]:
    if not isinstance(values, list):
        raise RouterDiscoveryIngestionError(
            "routes must be a list"
        )

    result: list[DiscoveredRoute] = []

    for item in values:
        if not isinstance(item, dict):
            raise RouterDiscoveryIngestionError(
                "Each discovered route must be an object"
            )

        destination = str(
            item.get("dst-address")
            or item.get("destination")
            or ""
        ).strip()
        gateway = str(
            item.get("gateway")
            or ""
        ).strip()

        if not destination:
            raise RouterDiscoveryIngestionError(
                "Discovered route destination is required"
            )

        if not gateway:
            raise RouterDiscoveryIngestionError(
                f"Discovered route gateway is required: {destination}"
            )

        result.append(
            DiscoveredRoute(
                destination=destination,
                gateway=gateway,
            )
        )

    return result


def build_discovery_snapshot_from_payload(
    payload: dict[str, Any],
    *,
    router_id: str | None = None,
) -> RouterDiscoverySnapshot:
    if not isinstance(payload, dict):
        raise RouterDiscoveryIngestionError(
            "Discovery payload must be an object"
        )

    router = payload.get("router")
    if not isinstance(router, dict):
        raise RouterDiscoveryIngestionError(
            "Discovery payload.router must be an object"
        )

    nas_identifier = _required_string(
        payload,
        "nas_identifier",
        "payload",
    )
    effective_router_id = (
        str(router_id).strip()
        if router_id is not None
        else nas_identifier
    )

    if not effective_router_id:
        raise RouterDiscoveryIngestionError(
            "router_id cannot be blank"
        )

    interfaces = _normalize_interfaces(
        payload.get("interfaces", [])
    )

    bridges = _normalize_bridges(
        payload.get("bridges", [])
    )

    vlans = _normalize_vlans(
        payload.get("vlans", [])
    )

    addresses = _normalize_addresses(
        payload.get("addresses", [])
    )

    routes = _normalize_routes(
        payload.get("routes", [])
    )

    snapshot = RouterDiscoverySnapshot(
        router_id=effective_router_id,
        board_name=_required_string(
            router,
            "board_name",
            "payload.router",
        ),
        routeros_version=_required_string(
            router,
            "routeros_version",
            "payload.router",
        ),
        architecture=_required_string(
            router,
            "architecture",
            "payload.router",
        ),
        interfaces=interfaces,
        bridges=bridges,
        vlans=vlans,
        addresses=addresses,
        routes=routes,
    )

    return build_router_discovery_snapshot(snapshot)
