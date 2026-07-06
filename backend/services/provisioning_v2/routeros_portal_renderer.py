"""
RouterOS Portal Renderer for CAIWAVE Provisioning Engine v2.
"""

from __future__ import annotations

import hashlib

from backend.services.provisioning_v2.provisioning_bundle import ProvisioningBundle
from backend.services.provisioning_v2.routeros_command_builder import build_command, build_comment, build_section
from backend.services.provisioning_v2.routeros_renderer_contracts import (
    RenderStatus,
    RouterOSRenderedSection,
    RouterOSSectionName,
)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def render_portal_section(bundle: ProvisioningBundle) -> RouterOSRenderedSection:
    portal = bundle.portal

    commands = [
        build_comment(f"Portal strategy: {portal.strategy.value}"),
        build_comment(f"Login redirect URL: {portal.login_redirect_url}"),
        build_comment(f"Success URL: {portal.success_url}"),
        build_comment(f"Failure URL: {portal.failure_url}"),
    ]

    if not portal.enabled:
        commands.append(build_comment("Portal disabled by provisioning plan"))
    else:
        for host in portal.walled_garden_hosts:
            commands.append(
                build_command(
                    "/ip hotspot walled-garden",
                    "add",
                    {
                        "dst-host": host,
                        "action": "allow",
                        "comment": "CAIWAVE managed portal walled garden host",
                    },
                )
            )

    content = build_section("CAIWAVE Portal", commands)

    return RouterOSRenderedSection(
        name=RouterOSSectionName.PORTAL,
        status=RenderStatus.RENDERED,
        content=content,
        checksum=_sha256(content),
        warnings=list(portal.warnings),
    )
