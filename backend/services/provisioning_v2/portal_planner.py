"""
Portal Planner for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no route wiring
- no legacy provisioning changes

This planner produces captive portal intent, redirect URLs, and pre-auth
walled garden requirements.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.provisioning_v2 import ProvisioningSnapshot
from backend.services.provisioning_v2.dns_planner import DNSPlan
from backend.services.provisioning_v2.hotspot_planner import HotspotPlan


class PortalPlannerError(ValueError):
    """Raised when portal intent cannot be safely planned."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PortalStrategy(str, Enum):
    REDIRECT = "redirect"
    EMBEDDED = "embedded"
    DISABLED = "disabled"


class PortalPlan(StrictModel):
    enabled: bool = True
    strategy: PortalStrategy
    portal_public_url: str
    api_public_url: str
    login_redirect_url: str
    success_url: str
    failure_url: str
    captive_dns_name: str
    required_hosts: List[str]
    walled_garden_hosts: List[str]
    metadata: Dict[str, str] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


def _host_from_url(url: str, field: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise PortalPlannerError(f"{field} must use http or https")
    if not parsed.netloc:
        raise PortalPlannerError(f"{field} must include a host")
    return parsed.netloc


def _join(base: str, path: str) -> str:
    return base.rstrip("/") + "/" + path.lstrip("/")


def plan_portal(
    *,
    snapshot: ProvisioningSnapshot,
    hotspot_plan: HotspotPlan,
    dns_plan: DNSPlan,
    payment_provider_hosts: List[str] | None = None,
    asset_hosts: List[str] | None = None,
) -> PortalPlan:
    """
    Build captive portal intent.

    Does not generate RouterOS login.html or walled garden commands.
    """

    portal_url = snapshot.portal.portal_public_url.strip()
    api_url = snapshot.portal.api_public_url.strip()

    portal_host = _host_from_url(portal_url, "portal_public_url")
    api_host = _host_from_url(api_url, "api_public_url")

    if dns_plan.captive_dns_name != hotspot_plan.dns_name:
        raise PortalPlannerError("DNS plan and Hotspot plan captive names must match")

    try:
        strategy = PortalStrategy(snapshot.portal.portal_strategy)
    except ValueError as exc:
        raise PortalPlannerError(
            f"Unsupported portal strategy: {snapshot.portal.portal_strategy}"
        ) from exc

    warnings: List[str] = []
    warnings.extend(hotspot_plan.warnings)
    warnings.extend(dns_plan.warnings)

    if strategy == PortalStrategy.EMBEDDED:
        warnings.append("Embedded portal strategy is not implemented for RouterOS rendering yet")

    required_hosts = []
    for host in [portal_host, api_host] + list(payment_provider_hosts or []) + list(asset_hosts or []):
        if host and host not in required_hosts:
            required_hosts.append(host)

    return PortalPlan(
        enabled=strategy != PortalStrategy.DISABLED,
        strategy=strategy,
        portal_public_url=portal_url,
        api_public_url=api_url,
        login_redirect_url=_join(portal_url, "portal"),
        success_url=_join(portal_url, "success"),
        failure_url=_join(portal_url, "failed"),
        captive_dns_name=dns_plan.captive_dns_name,
        required_hosts=required_hosts,
        walled_garden_hosts=required_hosts,
        metadata={
            "portal_contract_version": snapshot.portal.portal_contract_version,
            "hotspot_server": hotspot_plan.server_name,
            "hotspot_profile": hotspot_plan.profile_name,
        },
        warnings=warnings,
    )
