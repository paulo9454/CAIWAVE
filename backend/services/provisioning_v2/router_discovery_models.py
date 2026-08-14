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


class RouterDiscoverySnapshot(StrictModel):
    router_id: str

    board_name: str
    routeros_version: str
    architecture: str

    interfaces: List[DiscoveredInterface] = Field(default_factory=list)
    bridges: List[DiscoveredBridge] = Field(default_factory=list)
    vlans: List[DiscoveredVLAN] = Field(default_factory=list)
    addresses: List[DiscoveredAddress] = Field(default_factory=list)
