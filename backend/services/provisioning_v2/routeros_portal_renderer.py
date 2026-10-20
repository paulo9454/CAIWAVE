"""
RouterOS Portal Renderer for CAIWAVE Provisioning Engine v2.
"""

from __future__ import annotations

import hashlib

from backend.services.provisioning_v2.provisioning_bundle import ProvisioningBundle
from backend.services.provisioning_v2.routeros_command_builder import (
    build_command,
    build_comment,
    build_section,
    quote_routeros_value,
)
from backend.services.provisioning_v2.routeros_renderer_contracts import (
    RenderStatus,
    RouterOSRenderedSection,
    RouterOSSectionName,
)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def _ensure_safe_portal_public_url(value: str) -> None:
    # This check is intentionally repeated at the rendering boundary:
    # callers must not be able to bypass production-input validation.
    if any(
        ord(character) <= 0x20
        or 0x7F <= ord(character) <= 0x9F
        or character in {'"', "\\", "$"}
        for character in value
    ):
        raise ValueError(
            "portal_public_url contains characters unsafe for RouterOS embedding"
        )


def _quote_routeros_preserving_backslashes(value: str) -> str:
    # Renderer-generated HTML contains deliberate escapes such as \\" and
    # \\$ (HotSpot variables). Preserve those, but reject unescaped quotes
    # or dollar expansions that could change RouterOS command interpretation.
    if any(
        ord(character) < 0x20 or 0x7F <= ord(character) <= 0x9F
        for character in value
    ):
        raise ValueError("RouterOS file contents must not contain control characters")

    backslash_count = 0
    for character in value:
        if character == "\\":
            backslash_count += 1
            continue

        if character == '"' and backslash_count % 2 == 0:
            raise ValueError("Embedded double quotes must be escaped for RouterOS")

        if character == "$" and backslash_count % 2 == 0:
            raise ValueError("RouterOS variable references must be escaped")

        backslash_count = 0

    if backslash_count % 2:
        raise ValueError(
            "RouterOS file contents must not end with an unescaped backslash"
        )

    return f'"{value}"'

def render_portal_section(bundle: ProvisioningBundle) -> RouterOSRenderedSection:
    portal = bundle.portal
    _ensure_safe_portal_public_url(portal.portal_public_url)

    login_redirect_url = (
        f"{portal.portal_public_url.rstrip('/')}/portal/{bundle.hotspot_id}"
        "?mac=\\$(mac)"
        "&ip=\\$(ip)"
        "&dst=\\$(link-orig-esc)"
        "&login_url=\\$(link-login-only)"
    )

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

        redirect_html = (
            '\\$(if http-status == 302)Hotspot login required\\$(endif)'
            '\\$(if http-header == \\"Location\\")\\$(link-redirect)\\$(endif)'
        )

        commands.extend(
            [
                '/file remove [find name="hotspot/login.html"]',
                f'/file add name="hotspot/login.html" contents={_quote_routeros_preserving_backslashes(login_html)}',
                '/file remove [find name="hotspot/redirect.html"]',
                f'/file add name="hotspot/redirect.html" contents={_quote_routeros_preserving_backslashes(redirect_html)}',
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
