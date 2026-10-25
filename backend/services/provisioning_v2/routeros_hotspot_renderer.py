"""
RouterOS Hotspot Renderer for CAIWAVE Provisioning Engine v2.
"""

from __future__ import annotations

import hashlib

from backend.services.provisioning_v2.provisioning_bundle import ProvisioningBundle
from backend.services.provisioning_v2.routeros_command_builder import (
    RawRouterOSValue,
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


def render_hotspot_section(bundle: ProvisioningBundle) -> RouterOSRenderedSection:
    hotspot = bundle.hotspot

    commands = [
        build_comment(f"Hotspot auth mode: {hotspot.auth_mode.value}"),
    ]

    if not hotspot.enabled:
        commands.append(build_comment("Hotspot disabled by provisioning plan"))
    else:
        profile_name_value = quote_routeros_value(hotspot.profile_name)
        profile_add = build_command(
            "/ip hotspot profile",
            "add",
            {
                "name": hotspot.profile_name,
                "hotspot-address": bundle.address.gateway_ip,
                "dns-name": hotspot.dns_name,
                "use-radius": hotspot.use_radius,
                "radius-accounting": hotspot.accounting_enabled,
                "radius-interim-update": (
                    RawRouterOSValue("5m")
                    if hotspot.accounting_enabled
                    else RawRouterOSValue("received")
                ),
                "login-by": RawRouterOSValue(
                    ",".join(hotspot.login_methods)
                ),
            },
        )
        commands.append(
            f':if ([:len [/ip hotspot profile find where name={profile_name_value}]] = 0) '
            f'do={{ {profile_add}; }}'
        )

        server_name_value = quote_routeros_value(hotspot.server_name)
        server_add = build_command(
            "/ip hotspot",
            "add",
            {
                "name": hotspot.server_name,
                "interface": hotspot.target_interface,
                "address-pool": hotspot.address_pool_name,
                "profile": hotspot.profile_name,
                "disabled": False,
            },
        )
        commands.append(
            f':if ([:len [/ip hotspot find where name={server_name_value}]] = 0) '
            f'do={{ {server_add}; }}'
        )

    content = build_section("CAIWAVE Hotspot", commands)

    return RouterOSRenderedSection(
        name=RouterOSSectionName.HOTSPOT,
        status=RenderStatus.RENDERED,
        content=content,
        checksum=_sha256(content),
        warnings=list(hotspot.warnings),
    )
