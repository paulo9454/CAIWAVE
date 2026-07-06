"""
RouterOS RADIUS Renderer for CAIWAVE Provisioning Engine v2.
"""

from __future__ import annotations

import hashlib

from backend.services.provisioning_v2.provisioning_bundle import ProvisioningBundle
from backend.services.provisioning_v2.routeros_command_builder import (
    RawRouterOSValue,
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


def render_radius_section(bundle: ProvisioningBundle) -> RouterOSRenderedSection:
    radius = bundle.radius

    commands = [
        build_comment(f"NAS identifier: {radius.nas_identifier}"),
    ]

    if not radius.enabled:
        commands.append(build_comment("RADIUS disabled by provisioning plan"))
    else:
        commands.append(
            build_command(
                "/radius",
                "add",
                {
                    "service": RawRouterOSValue(",".join(service.value for service in radius.services)),
                    "address": radius.auth_host,
                    "authentication-port": radius.auth_port,
                    "accounting-port": radius.accounting_port,
                    "secret": radius.secret_ref,
                    "timeout": "3s",
                    "comment": "CAIWAVE managed RADIUS server",
                },
            )
        )
        commands.append(
            build_command(
                "/radius incoming",
                "set",
                {
                    "accept": radius.coa_enabled,
                },
            )
        )

    content = build_section("CAIWAVE RADIUS", commands)

    return RouterOSRenderedSection(
        name=RouterOSSectionName.RADIUS,
        status=RenderStatus.RENDERED,
        content=content,
        checksum=_sha256(content),
        warnings=list(radius.warnings),
    )
