"""
Router Discovery Models for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no topology planning
- no provisioning mutation

This module only defines immutable discovery contracts.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class DiscoveredInterface(StrictModel):
    name: str
    type: str
    running: bool = False
    disabled: bool = False
    mac_address: Optional[str] = None


class DiscoveredBridge(StrictModel):
    name: str
    running: bool = False


class DiscoveredVLAN(StrictModel):
    name: str
    vlan_id: int
    parent_interface: str


class DiscoveredAddress(StrictModel):
    interface: str
    address: str

class DiscoveredBridgePort(StrictModel):
    bridge_name: str
    interface_name: str


class DiscoveredRoute(StrictModel):
    destination: str
    gateway: str


class DiscoveredDNS(StrictModel):
    servers: List[str] = Field(default_factory=list)


class DiscoveredDHCPServer(StrictModel):
    name: str
    interface: str
    address_pool: str


class DiscoveredHotspot(StrictModel):
    name: str
    interface: str
    profile: str

class RouterDiscoverySnapshot(StrictModel):
    router_id: str

    board_name: str
    routeros_version: str
    architecture: str

    interfaces: List[DiscoveredInterface] = Field(default_factory=list)
    bridges: List[DiscoveredBridge] = Field(default_factory=list)
    vlans: List[DiscoveredVLAN] = Field(default_factory=list)
    addresses: List[DiscoveredAddress] = Field(default_factory=list)

    bridge_ports: List[DiscoveredBridgePort] = Field(default_factory=list)
    routes: List[DiscoveredRoute] = Field(default_factory=list)

    dns: List[DiscoveredDNS] = Field(default_factory=list)

    dhcp_servers: List[DiscoveredDHCPServer] = Field(default_factory=list)

    hotspots: List[DiscoveredHotspot] = Field(default_factory=list)
