"""
RouterOS Wireless Renderer for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS execution
- no production mutation
- renders only wireless intent already approved by the planner

Patch 7 scope:
- supports legacy RouterOS /interface wireless rendering
- does not guess WiFiWave2 or /interface wifi support
"""

from __future__ import annotations

import hashlib

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
from backend.services.provisioning_v2.wireless_planner import (
    WirelessMode,
    WirelessPlan,
)


class RouterOSWirelessRendererError(ValueError):
    """Raised when wireless intent cannot be rendered safely."""


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def render_wireless_section(
    plan: WirelessPlan,
) -> RouterOSRenderedSection:
    commands = [
        build_comment("CAIWAVE managed wireless"),
    ]

    for radio in plan.radios:
        if radio.mode == WirelessMode.AP:
            commands.append(
                build_command(
                    "/interface wireless",
                    "set",
                    {
                        "numbers": radio.interface,
                        "mode": "ap-bridge",
                        "ssid": radio.ssid,
                        "disabled": not radio.enabled,
                    },
                )
            )
        elif radio.mode == WirelessMode.DISABLED:
            commands.append(
                build_command(
                    "/interface wireless",
                    "set",
                    {
                        "numbers": radio.interface,
                        "disabled": True,
                    },
                )
            )
        else:
            raise RouterOSWirelessRendererError(
                f"Unsupported wireless mode: {radio.mode}"
            )

    if not plan.radios:
        content = build_section(
            "CAIWAVE Wireless",
            commands,
        )

        return RouterOSRenderedSection(
            name=RouterOSSectionName.WIRELESS,
            status=RenderStatus.PLANNED,
            content=content,
            checksum=_sha256(content),
            warnings=list(plan.warnings),
        )

    content = build_section("CAIWAVE Wireless", commands)

    return RouterOSRenderedSection(
        name=RouterOSSectionName.WIRELESS,
        status=RenderStatus.RENDERED,
        content=content,
        checksum=_sha256(content),
        warnings=list(plan.warnings),
    )
