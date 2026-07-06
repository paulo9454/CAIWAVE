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
from backend.services.provisioning_v2.routeros_address_renderer import render_address_section
from backend.services.provisioning_v2.routeros_bridge_renderer import render_bridge_section
from backend.services.provisioning_v2.routeros_command_builder import join_script
from backend.services.provisioning_v2.routeros_dhcp_renderer import render_dhcp_section
from backend.services.provisioning_v2.routeros_dns_renderer import render_dns_section
from backend.services.provisioning_v2.routeros_firewall_renderer import render_firewall_section
from backend.services.provisioning_v2.routeros_hotspot_renderer import render_hotspot_section
from backend.services.provisioning_v2.routeros_identity_renderer import render_identity_section
from backend.services.provisioning_v2.routeros_nat_renderer import render_nat_section
from backend.services.provisioning_v2.routeros_portal_renderer import render_portal_section
from backend.services.provisioning_v2.routeros_radius_renderer import render_radius_section
from backend.services.provisioning_v2.routeros_renderer_contracts import (
    RenderStatus,
    RouterOSRenderedArtifact,
    RouterOSRenderedSection,
    RouterOSRenderContext,
    RouterOSSectionName,
    build_render_context,
    build_render_manifest,
)


class RouterOSRenderOrchestratorError(ValueError):
    """Raised when a bundle cannot be rendered safely."""


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _planned_placeholder(section_name: RouterOSSectionName) -> RouterOSRenderedSection:
    content = f"# section planned: {section_name.value}"
    return RouterOSRenderedSection(
        name=section_name,
        status=RenderStatus.PLANNED,
        content=content,
        checksum=_sha256(content),
    )


def _render_section(bundle: ProvisioningBundle, section_name: RouterOSSectionName) -> RouterOSRenderedSection:
    renderers = {
        RouterOSSectionName.IDENTITY: render_identity_section,
        RouterOSSectionName.BRIDGE: render_bridge_section,
        RouterOSSectionName.ADDRESSING: render_address_section,
        RouterOSSectionName.DHCP: render_dhcp_section,
        RouterOSSectionName.DNS: render_dns_section,
        RouterOSSectionName.NAT: render_nat_section,
        RouterOSSectionName.HOTSPOT: render_hotspot_section,
        RouterOSSectionName.PORTAL: render_portal_section,
        RouterOSSectionName.RADIUS: render_radius_section,
        RouterOSSectionName.FIREWALL: render_firewall_section,
    }

    renderer = renderers.get(section_name)
    if renderer is None:
        return _planned_placeholder(section_name)
    return renderer(bundle)


def render_routeros_bundle(
    *,
    bundle: ProvisioningBundle,
    context: RouterOSRenderContext | None = None,
) -> RouterOSRenderedArtifact:
    """
    Render a deterministic RouterOS artifact from a valid provisioning bundle.

    Sections without production renderers remain planned placeholders.
    """

    validation = validate_provisioning_bundle(bundle)
    if not validation.valid:
        raise RouterOSRenderOrchestratorError(
            "Provisioning bundle is invalid: " + "; ".join(validation.errors)
        )

    render_context = context or build_render_context()
    manifest = build_render_manifest(bundle=bundle, context=render_context)

    sections = [
        _render_section(bundle, section_name)
        for section_name in render_context.section_order
    ]

    content = join_script([section.content for section in sections])

    return RouterOSRenderedArtifact(
        artifact_id=f"routeros-artifact:{bundle.snapshot_id}",
        bundle_id=bundle.bundle_id,
        router_id=bundle.router_id,
        filename=f"{bundle.router_id}-provisioning-v2.rsc",
        status=RenderStatus.RENDERED,
        manifest=manifest,
        sections=sections,
        content=content,
        checksum=_sha256(content),
    )


def render_routeros_bundle_skeleton(
    *,
    bundle: ProvisioningBundle,
    context: RouterOSRenderContext | None = None,
) -> RouterOSRenderedArtifact:
    """
    Backward-compatible alias for the first orchestrator contract.
    """

    return render_routeros_bundle(bundle=bundle, context=context)
