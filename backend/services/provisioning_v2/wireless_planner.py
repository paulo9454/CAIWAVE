"""
Wireless Planner for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no production mutation
- no assumptions about unsupported wireless stacks

This module converts verified router wireless capabilities into a
wireless intent plan.
"""

from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from backend.services.provisioning_v2.router_capabilities import (
    RouterCapabilityFacts,
)


class WirelessPlannerError(ValueError):
    """Raised when wireless intent cannot be planned safely."""


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class WirelessMode(str, Enum):
    AP = "ap"
    DISABLED = "disabled"


class WirelessRadioPlan(StrictModel):
    interface: str
    mode: WirelessMode
    ssid: str
    enabled: bool = True


class WirelessPlan(StrictModel):
    radios: List[WirelessRadioPlan] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


def plan_wireless(
    *,
    capabilities: RouterCapabilityFacts,
    ssid: str,
) -> WirelessPlan:
    """
    Build wireless intent from verified capability facts.

    No RouterOS syntax is generated here.
    """

    normalized_ssid = ssid.strip()

    if not normalized_ssid:
        raise WirelessPlannerError(
            "SSID is required for wireless planning"
        )

    if len(normalized_ssid) > 32:
        raise WirelessPlannerError(
            "SSID must not exceed 32 characters"
        )

    if not capabilities.supports_wireless:
        return WirelessPlan(
            radios=[],
            warnings=[
                "Router has no discovered wireless interfaces"
            ],
        )

    if not capabilities.wireless_interfaces:
        raise WirelessPlannerError(
            "Wireless capability is enabled but no wireless interfaces exist"
        )

    radios = [
        WirelessRadioPlan(
            interface=interface_name,
            mode=WirelessMode.AP,
            ssid=normalized_ssid,
            enabled=True,
        )
        for interface_name in capabilities.wireless_interfaces
    ]

    return WirelessPlan(
        radios=radios,
        warnings=[],
    )
