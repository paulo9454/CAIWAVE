"""
RouterOS Identity Renderer for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no route wiring
- no legacy provisioning changes

This renderer translates validated bundle identity metadata into RouterOS
identity section commands only.
"""

from __future__ import annotations

import hashlib

from backend.services.provisioning_v2.provisioning_bundle import ProvisioningBundle
from backend.services.provisioning_v2.routeros_command_builder import (
    build_command,
    build_comment,
    build_section,
)
from backend.services.provisioning_v2.routeros_renderer_contracts import (
    RenderStatus,
    RouterOSRenderedSection,
    RouterOSSectionName,
)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def render_identity_section(bundle: ProvisioningBundle) -> RouterOSRenderedSection:
    commands = [
        build_comment(f"CAIWAVE Provisioning Bundle: {bundle.bundle_id}"),
        build_comment(f"Snapshot: {bundle.snapshot_id}"),
        build_comment(f"Router ID: {bundle.router_id}"),
        build_comment(f"Hotspot ID: {bundle.hotspot_id}"),
        build_command(
            "/system identity",
            "set",
            {"name": bundle.snapshot.identity.router_name},
        ),
    ]

    content = build_section("CAIWAVE Identity", commands)

    return RouterOSRenderedSection(
        name=RouterOSSectionName.IDENTITY,
        status=RenderStatus.RENDERED,
        content=content,
        checksum=_sha256(content),
        warnings=[],
    )
