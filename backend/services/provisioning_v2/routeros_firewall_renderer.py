"""
RouterOS Firewall Renderer for CAIWAVE Provisioning Engine v2.
"""

from __future__ import annotations

import hashlib

from backend.services.provisioning_v2.firewall_planner import FirewallAction
from backend.services.provisioning_v2.provisioning_bundle import ProvisioningBundle
from backend.services.provisioning_v2.routeros_command_builder import build_command, build_comment, build_section
from backend.services.provisioning_v2.routeros_renderer_contracts import (
    RenderStatus,
    RouterOSRenderedSection,
    RouterOSSectionName,
)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def render_firewall_section(bundle: ProvisioningBundle) -> RouterOSRenderedSection:
    firewall = bundle.firewall

    commands = [
        build_comment(f"WAN interface: {firewall.wan_interface}"),
        build_comment(f"Default input policy: {firewall.default_input_policy.value}"),
        build_comment(f"Default forward policy: {firewall.default_forward_policy.value}"),
    ]

    for rule in firewall.rules:
        args = {
            "chain": rule.chain.value,
            "action": rule.action.value,
            "comment": f"CAIWAVE: {rule.purpose}",
            "src-address": rule.source_network,
            "dst-address": rule.destination_host,
            "protocol": rule.protocol,
            "dst-port": rule.destination_port,
        }
        commands.append(build_command("/ip firewall filter", "add", args))

    if firewall.default_input_policy == FirewallAction.DROP:
        commands.append(
            build_command(
                "/ip firewall filter",
                "add",
                {
                    "chain": "input",
                    "action": "drop",
                    "in-interface": firewall.wan_interface,
                    "comment": "CAIWAVE default drop WAN input",
                },
            )
        )

    if firewall.default_forward_policy == FirewallAction.DROP:
        commands.append(
            build_command(
                "/ip firewall filter",
                "add",
                {
                    "chain": "forward",
                    "action": "drop",
                    "comment": "CAIWAVE default drop unmatched forward",
                },
            )
        )

    content = build_section("CAIWAVE Firewall", commands)

    return RouterOSRenderedSection(
        name=RouterOSSectionName.FIREWALL,
        status=RenderStatus.RENDERED,
        content=content,
        checksum=_sha256(content),
        warnings=list(firewall.warnings),
    )
