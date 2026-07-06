"""
RouterOS Renderer Contracts for CAIWAVE Provisioning Engine v2.

Safety:
- contracts only
- no RouterOS generation yet
- no database access
- no route wiring
- no legacy provisioning changes

These contracts define how validated provisioning bundles will later be
translated into deterministic RouterOS artifacts.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.services.provisioning_v2.provisioning_bundle import ProvisioningBundle


class RendererContractError(ValueError):
    """Raised when renderer contract data is invalid."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RouterOSSectionName(str, Enum):
    HEADER = "header"
    IDENTITY = "identity"
    INTERFACES = "interfaces"
    BRIDGE = "bridge"
    ADDRESSING = "addressing"
    DHCP = "dhcp"
    DNS = "dns"
    NAT = "nat"
    HOTSPOT = "hotspot"
    PORTAL = "portal"
    RADIUS = "radius"
    FIREWALL = "firewall"
    SCHEDULERS = "schedulers"
    VALIDATION = "validation"
    FOOTER = "footer"


class RenderStatus(str, Enum):
    PLANNED = "planned"
    RENDERED = "rendered"
    FAILED = "failed"


class RouterOSRenderContext(StrictModel):
    routeros_major_version: int = 7
    target_platform: str = "routeros"
    safe_mode_required: bool = True
    idempotent: bool = True
    include_comments: bool = True
    section_order: List[RouterOSSectionName]


class RouterOSRenderedSection(StrictModel):
    name: RouterOSSectionName
    status: RenderStatus = RenderStatus.PLANNED
    content: str = ""
    checksum: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class RouterOSRenderManifest(StrictModel):
    renderer_version: str = "1.0.0"
    bundle_id: str
    snapshot_id: str
    router_id: str
    sections: List[RouterOSSectionName]
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, str] = Field(default_factory=dict)


class RouterOSRenderedArtifact(StrictModel):
    artifact_id: str
    bundle_id: str
    router_id: str
    content_type: str = "text/routeros-script"
    filename: str
    status: RenderStatus
    manifest: RouterOSRenderManifest
    sections: List[RouterOSRenderedSection]
    content: str = ""
    checksum: Optional[str] = None


def default_routeros_section_order() -> List[RouterOSSectionName]:
    return [
        RouterOSSectionName.HEADER,
        RouterOSSectionName.IDENTITY,
        RouterOSSectionName.INTERFACES,
        RouterOSSectionName.BRIDGE,
        RouterOSSectionName.ADDRESSING,
        RouterOSSectionName.DHCP,
        RouterOSSectionName.DNS,
        RouterOSSectionName.NAT,
        RouterOSSectionName.HOTSPOT,
        RouterOSSectionName.PORTAL,
        RouterOSSectionName.RADIUS,
        RouterOSSectionName.FIREWALL,
        RouterOSSectionName.SCHEDULERS,
        RouterOSSectionName.VALIDATION,
        RouterOSSectionName.FOOTER,
    ]


def build_render_context(
    *,
    routeros_major_version: int = 7,
    section_order: Optional[List[RouterOSSectionName]] = None,
) -> RouterOSRenderContext:
    if routeros_major_version < 7:
        raise RendererContractError("RouterOS v7 or newer is required for renderer v2")

    return RouterOSRenderContext(
        routeros_major_version=routeros_major_version,
        section_order=section_order or default_routeros_section_order(),
    )


def build_render_manifest(
    *,
    bundle: ProvisioningBundle,
    context: RouterOSRenderContext,
) -> RouterOSRenderManifest:
    return RouterOSRenderManifest(
        bundle_id=bundle.bundle_id,
        snapshot_id=bundle.snapshot_id,
        router_id=bundle.router_id,
        sections=context.section_order,
        warnings=list(bundle.warnings),
        metadata={
            "engine_version": bundle.engine_version,
            "routeros_major_version": str(context.routeros_major_version),
            "safe_mode_required": str(context.safe_mode_required).lower(),
            "idempotent": str(context.idempotent).lower(),
        },
    )
