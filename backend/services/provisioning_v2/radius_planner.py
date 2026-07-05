"""
RADIUS Planner for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no route wiring
- no legacy provisioning changes

This planner produces RADIUS authentication and accounting intent.
"""

from __future__ import annotations

from enum import Enum
from ipaddress import ip_address
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.provisioning_v2 import ProvisioningSnapshot
from backend.services.provisioning_v2.hotspot_planner import HotspotPlan, HotspotAuthMode


class RadiusPlannerError(ValueError):
    """Raised when RADIUS intent cannot be safely planned."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RadiusService(str, Enum):
    HOTSPOT = "hotspot"
    LOGIN = "login"


class RadiusPlan(StrictModel):
    enabled: bool
    services: List[RadiusService]
    auth_host: str
    auth_port: int
    accounting_host: str
    accounting_port: int
    secret_ref: str
    nas_identifier: str
    accounting_enabled: bool = True
    interim_update_seconds: int = 300
    coa_enabled: bool = False
    warnings: List[str] = Field(default_factory=list)


def _validate_host(value: str, field: str) -> str:
    if not value or not isinstance(value, str):
        raise RadiusPlannerError(f"{field} is required")
    try:
        ip_address(value)
        return value
    except ValueError:
        if "." not in value:
            raise RadiusPlannerError(f"{field} must be an IP address or hostname")
        return value


def _validate_port(value: int, field: str) -> int:
    if not isinstance(value, int) or value <= 0 or value > 65535:
        raise RadiusPlannerError(f"{field} must be a valid TCP/UDP port")
    return value


def plan_radius(
    *,
    snapshot: ProvisioningSnapshot,
    hotspot_plan: HotspotPlan,
    services: Optional[List[RadiusService]] = None,
    interim_update_seconds: int = 300,
    coa_enabled: bool = False,
) -> RadiusPlan:
    """
    Build RADIUS intent from snapshot and hotspot intent.

    Does not configure RouterOS or FreeRADIUS.
    """

    if hotspot_plan.auth_mode != HotspotAuthMode.RADIUS:
        return RadiusPlan(
            enabled=False,
            services=[],
            auth_host="",
            auth_port=0,
            accounting_host="",
            accounting_port=0,
            secret_ref="",
            nas_identifier=snapshot.radius.nas_identifier,
            accounting_enabled=False,
            interim_update_seconds=0,
            coa_enabled=False,
            warnings=["RADIUS disabled because Hotspot auth mode is not RADIUS"],
        )

    auth_host = _validate_host(snapshot.radius.radius_host, "radius_host")
    auth_port = _validate_port(snapshot.radius.radius_auth_port, "radius_auth_port")
    accounting_port = _validate_port(
        snapshot.radius.radius_accounting_port,
        "radius_accounting_port",
    )

    if not snapshot.radius.radius_secret_ref:
        raise RadiusPlannerError("radius_secret_ref is required")
    if not snapshot.radius.nas_identifier:
        raise RadiusPlannerError("nas_identifier is required")
    if interim_update_seconds <= 0:
        raise RadiusPlannerError("interim_update_seconds must be greater than zero")

    planned_services = [RadiusService.HOTSPOT] if services is None else list(services)
    if not planned_services:
        raise RadiusPlannerError("at least one RADIUS service is required")

    warnings: List[str] = []
    warnings.extend(hotspot_plan.warnings)

    if not hotspot_plan.accounting_enabled:
        warnings.append("Hotspot accounting is disabled while RADIUS is enabled")

    return RadiusPlan(
        enabled=True,
        services=planned_services,
        auth_host=auth_host,
        auth_port=auth_port,
        accounting_host=auth_host,
        accounting_port=accounting_port,
        secret_ref=snapshot.radius.radius_secret_ref,
        nas_identifier=snapshot.radius.nas_identifier,
        accounting_enabled=hotspot_plan.accounting_enabled,
        interim_update_seconds=interim_update_seconds,
        coa_enabled=coa_enabled,
        warnings=warnings,
    )
