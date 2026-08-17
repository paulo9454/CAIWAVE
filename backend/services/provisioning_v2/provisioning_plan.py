"""
Provisioning Plan for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no provisioning mutation

This module combines verified router capabilities with explicit provisioning
intent and produces validated service/topology decisions for the existing
v2 planners.
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict, Field

from backend.services.provisioning_v2.provisioning_intent import (
    ProvisioningIntent,
)
from backend.services.provisioning_v2.router_capabilities import (
    RouterCapabilityFacts,
)


class ProvisioningPlanError(ValueError):
    """Raised when requested provisioning cannot be supported safely."""


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class ProvisioningPlan(StrictModel):
    router_id: str

    wan_interface: str
    client_interfaces: List[str] = Field(default_factory=list)

    hotspot_enabled: bool
    wifi_enabled: bool
    wired_enabled: bool

    wifi_interfaces: List[str] = Field(default_factory=list)
    wifi_ssid: str = "CAIWAVE"

    client_isolation: bool = True
    poe_enabled: bool = False

    warnings: List[str] = Field(default_factory=list)


def _select_wan_interface(
    capabilities: RouterCapabilityFacts,
    requested_wan_interface: str | None,
) -> str:
    if requested_wan_interface:
        if requested_wan_interface not in capabilities.ethernet_interfaces:
            raise ProvisioningPlanError(
                f"Requested WAN interface is not a discovered Ethernet "
                f"interface: {requested_wan_interface}"
            )
        return requested_wan_interface

    if not capabilities.ethernet_interfaces:
        raise ProvisioningPlanError(
            "No discovered Ethernet interfaces are available for WAN"
        )

    return capabilities.ethernet_interfaces[0]


def _select_wired_interfaces(
    capabilities: RouterCapabilityFacts,
    *,
    wan_interface: str,
    requested_interfaces: list[str] | None,
) -> list[str]:
    requested = [
        str(item).strip()
        for item in (requested_interfaces or [])
        if str(item).strip()
    ]

    if requested:
        missing = [
            item
            for item in requested
            if item not in capabilities.ethernet_interfaces
        ]

        if missing:
            raise ProvisioningPlanError(
                "Requested wired interface(s) were not discovered: "
                + ", ".join(missing)
            )

        if wan_interface in requested:
            raise ProvisioningPlanError(
                "WAN interface cannot also be a wired client interface"
            )

        return list(dict.fromkeys(requested))

    return [
        interface_name
        for interface_name in capabilities.ethernet_interfaces
        if interface_name != wan_interface
    ]


def build_provisioning_plan(
    *,
    capabilities: RouterCapabilityFacts,
    intent: ProvisioningIntent,
    requested_wan_interface: str | None = None,
    requested_wired_interfaces: list[str] | None = None,
) -> ProvisioningPlan:
    """
    Combine discovered hardware capability facts with explicit service intent.

    This function does not render RouterOS and does not silently invent
    unsupported hardware capabilities.
    """

    wan_interface = _select_wan_interface(
        capabilities,
        requested_wan_interface,
    )

    wired_interfaces: list[str] = []

    if intent.wired_enabled:
        wired_interfaces = _select_wired_interfaces(
            capabilities,
            wan_interface=wan_interface,
            requested_interfaces=requested_wired_interfaces,
        )

    wifi_interfaces: list[str] = []

    if intent.wifi_enabled:
        if not capabilities.supports_wireless:
            raise ProvisioningPlanError(
                "Wi-Fi was requested but the discovered router "
                "does not support wireless"
            )

        if not capabilities.wireless_interfaces:
            raise ProvisioningPlanError(
                "Wi-Fi was requested but no wireless interfaces "
                "were discovered"
            )

        wifi_interfaces = list(capabilities.wireless_interfaces)

    client_interfaces = [
        *wired_interfaces,
        *wifi_interfaces,
    ]

    if not client_interfaces:
        raise ProvisioningPlanError(
            "Provisioning intent produced no client interfaces"
        )

    return ProvisioningPlan(
        router_id=capabilities.router_id,
        wan_interface=wan_interface,
        client_interfaces=list(dict.fromkeys(client_interfaces)),
        hotspot_enabled=intent.hotspot_enabled,
        wifi_enabled=intent.wifi_enabled,
        wired_enabled=intent.wired_enabled,
        wifi_interfaces=wifi_interfaces,
        wifi_ssid=intent.wifi_ssid.strip(),
        client_isolation=intent.client_isolation,
        poe_enabled=intent.poe_enabled,
        warnings=[],
    )
