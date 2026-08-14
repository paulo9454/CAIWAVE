"""
Router Capability Facts for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no provisioning mutation

This module derives only capabilities that are directly supported by the
validated RouterDiscoverySnapshot. It does not guess router features.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from backend.services.provisioning_v2.router_discovery import (
    build_router_discovery_snapshot,
)
from backend.services.provisioning_v2.router_discovery_models import (
    RouterDiscoverySnapshot,
)


class RouterCapabilityError(ValueError):
    """Raised when router capability facts cannot be derived safely."""


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class RouterCapabilityFacts(StrictModel):
    router_id: str
    board_name: str
    routeros_version: str
    architecture: str

    interface_count: int = 0
    ethernet_interfaces: list[str] = Field(default_factory=list)
    wireless_interfaces: list[str] = Field(default_factory=list)

    bridge_count: int = 0
    vlan_count: int = 0
    route_count: int = 0
    dhcp_server_count: int = 0
    hotspot_count: int = 0

    supports_wireless: bool = False


def detect_router_capabilities(
    snapshot: RouterDiscoverySnapshot,
) -> RouterCapabilityFacts:
    validated = build_router_discovery_snapshot(snapshot)

    ethernet_interfaces = [
        item.name
        for item in validated.interfaces
        if item.type.strip().lower() in {"ethernet", "ether"}
    ]

    wireless_interfaces = [
        item.name
        for item in validated.interfaces
        if item.type.strip().lower() in {
            "wireless",
            "wifi",
            "wifiwave2",
        }
    ]

    return RouterCapabilityFacts(
        router_id=validated.router_id,
        board_name=validated.board_name,
        routeros_version=validated.routeros_version,
        architecture=validated.architecture,
        interface_count=len(validated.interfaces),
        ethernet_interfaces=ethernet_interfaces,
        wireless_interfaces=wireless_interfaces,
        bridge_count=len(validated.bridges),
        vlan_count=len(validated.vlans),
        route_count=len(validated.routes),
        dhcp_server_count=len(validated.dhcp_servers),
        hotspot_count=len(validated.hotspots),
        supports_wireless=bool(wireless_interfaces),
    )
