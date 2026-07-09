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

    login_redirect_url = f"{portal.login_redirect_url}?hotspot={bundle.hotspot_id}"

    commands = [
        build_comment(f"Portal strategy: {portal.strategy.value}"),
        build_comment(f"Login redirect URL: {login_redirect_url}"),
        build_comment(f"Success URL: {portal.success_url}"),
        build_comment(f"Failure URL: {portal.failure_url}"),
    ]

    if not portal.enabled:
        commands.append(build_comment("Portal disabled by provisioning plan"))
    else:
        login_html = (
            "<html><head>"
            f"<meta http-equiv=\\\"refresh\\\" content=\\\"0; url={login_redirect_url}\\\">"
            "</head><body>Redirecting to CAIWAVE..."
            f"<script>window.location.href=\\\"{login_redirect_url}\\\";</script>"
            "</body></html>"
        )

        commands.extend(
            [
                '/file remove [find name="hotspot/login.html"]',
                f'/file add name="hotspot/login.html" contents="{login_html}"',
            ]
        )

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
