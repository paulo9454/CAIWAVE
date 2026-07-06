"""
RouterOS Render Orchestrator for CAIWAVE Provisioning Engine v2.

Safety:
- skeleton only
- no real RouterOS section rendering yet
- no database access
- no route wiring
- no legacy provisioning changes

This orchestrator validates the bundle, builds a render manifest, and creates
planned sections in deterministic order. Future section renderers will replace
the placeholder section content.
"""

from __future__ import annotations

import hashlib

from backend.services.provisioning_v2.bundle_validator import validate_provisioning_bundle
from backend.services.provisioning_v2.provisioning_bundle import ProvisioningBundle
from backend.services.provisioning_v2.routeros_command_builder import join_script
from backend.services.provisioning_v2.routeros_renderer_contracts import (
    RenderStatus,
    RouterOSRenderedArtifact,
    RouterOSRenderedSection,
    RouterOSRenderContext,
    build_render_context,
    build_render_manifest,
)


class RouterOSRenderOrchestratorError(ValueError):
    """Raised when a bundle cannot be rendered safely."""


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def render_routeros_bundle_skeleton(
    *,
    bundle: ProvisioningBundle,
    context: RouterOSRenderContext | None = None,
) -> RouterOSRenderedArtifact:
    """
    Build a deterministic skeleton rendered artifact from a valid bundle.

    This does not render real RouterOS configuration yet.
    """

    validation = validate_provisioning_bundle(bundle)
    if not validation.valid:
        raise RouterOSRenderOrchestratorError(
            "Provisioning bundle is invalid: " + "; ".join(validation.errors)
        )

    render_context = context or build_render_context()
    manifest = build_render_manifest(bundle=bundle, context=render_context)

    sections = [
        RouterOSRenderedSection(
            name=section_name,
            status=RenderStatus.PLANNED,
            content=f"# section planned: {section_name.value}",
            checksum=_sha256(f"# section planned: {section_name.value}"),
        )
        for section_name in render_context.section_order
    ]

    content = join_script([section.content for section in sections])

    return RouterOSRenderedArtifact(
        artifact_id=f"routeros-artifact:{bundle.snapshot_id}",
        bundle_id=bundle.bundle_id,
        router_id=bundle.router_id,
        filename=f"{bundle.router_id}-provisioning-v2.rsc",
        status=RenderStatus.PLANNED,
        manifest=manifest,
        sections=sections,
        content=content,
        checksum=_sha256(content),
    )
