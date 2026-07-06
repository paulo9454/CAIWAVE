"""
RouterOS Hotspot Renderer for CAIWAVE Provisioning Engine v2.
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


def render_hotspot_section(bundle: ProvisioningBundle) -> RouterOSRenderedSection:
    hotspot = bundle.hotspot

    commands = [
        build_comment(f"Hotspot auth mode: {hotspot.auth_mode.value}"),
    ]

    if not hotspot.enabled:
        commands.append(build_comment("Hotspot disabled by provisioning plan"))
    else:
        commands.append(
            build_command(
                "/ip hotspot profile",
                "add",
                {
                    "name": hotspot.profile_name,
                    "hotspot-address": bundle.address.gateway_ip,
                    "dns-name": hotspot.dns_name,
                    "use-radius": hotspot.use_radius,
                    "login-by": ",".join(hotspot.login_methods),
                    "comment": "CAIWAVE managed hotspot profile",
                },
            )
        )
        commands.append(
            build_command(
                "/ip hotspot",
                "add",
                {
                    "name": hotspot.server_name,
                    "interface": hotspot.target_interface,
                    "address-pool": hotspot.address_pool_name,
                    "profile": hotspot.profile_name,
                    "disabled": False,
                    "comment": "CAIWAVE managed hotspot server",
                },
            )
        )

    content = build_section("CAIWAVE Hotspot", commands)

    return RouterOSRenderedSection(
        name=RouterOSSectionName.HOTSPOT,
        status=RenderStatus.RENDERED,
        content=content,
        checksum=_sha256(content),
        warnings=list(hotspot.warnings),
    )
