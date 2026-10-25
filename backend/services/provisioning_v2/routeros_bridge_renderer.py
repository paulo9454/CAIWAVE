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
    quote_routeros_value,
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
        if bridge.action == BridgeAction.CREATE:
            bridge_name_value = quote_routeros_value(bridge.bridge_name)
            bridge_add = build_command(
                "/interface bridge",
                "add",
                {
                    "name": bridge.bridge_name,
                    "comment": "CAIWAVE managed hotspot bridge",
                },
            )
            commands.append(
                f':if ([:len [/interface bridge find where name={bridge_name_value}]] = 0) '
                f'do={{ {bridge_add}; }}'
            )

        existing_members = set(bridge.existing_members)
        for member in bridge.members:
            if member in existing_members:
                continue

            bridge_name_value = quote_routeros_value(bridge.bridge_name)
            member_value = quote_routeros_value(member)
            member_add = build_command(
                "/interface bridge port",
                "add",
                {
                    "bridge": bridge.bridge_name,
                    "interface": member,
                    "comment": "CAIWAVE managed bridge member",
                },
            )
            commands.append(
                f':if ([:len [/interface bridge port find where bridge={bridge_name_value} '
                f'and interface={member_value}]] = 0) do={{ {member_add}; }}'
            )

    content = build_section("CAIWAVE Bridge", commands)

    return RouterOSRenderedSection(
        name=RouterOSSectionName.BRIDGE,
        status=RenderStatus.RENDERED,
        content=content,
        checksum=_sha256(content),
        warnings=list(bridge.warnings),
    )
