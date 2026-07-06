"""
RouterOS Bridge Renderer for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no route wiring
- no legacy provisioning changes

This renderer translates validated BridgePlan intent into RouterOS bridge
section commands only.
"""

from __future__ import annotations

import hashlib

from backend.services.provisioning_v2.bridge_planner import BridgeAction
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


def render_bridge_section(bundle: ProvisioningBundle) -> RouterOSRenderedSection:
    bridge = bundle.bridge
    commands: list[str] = [
        build_comment(f"Bridge action: {bridge.action.value}"),
    ]

    if bridge.action == BridgeAction.NONE:
        commands.append(build_comment("No bridge required by topology plan"))
    else:
        commands.append(
            build_command(
                "/interface bridge",
                "add",
                {
                    "name": bridge.bridge_name,
                    "comment": "CAIWAVE managed hotspot bridge",
                },
            )
        )

        for member in bridge.members:
            commands.append(
                build_command(
                    "/interface bridge port",
                    "add",
                    {
                        "bridge": bridge.bridge_name,
                        "interface": member,
                        "comment": "CAIWAVE managed bridge member",
                    },
                )
            )

    content = build_section("CAIWAVE Bridge", commands)

    return RouterOSRenderedSection(
        name=RouterOSSectionName.BRIDGE,
        status=RenderStatus.RENDERED,
        content=content,
        checksum=_sha256(content),
        warnings=list(bridge.warnings),
    )
