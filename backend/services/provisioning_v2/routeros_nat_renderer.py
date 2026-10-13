"""
RouterOS NAT Renderer for CAIWAVE Provisioning Engine v2.
"""

from __future__ import annotations

import hashlib

from backend.services.provisioning_v2.nat_planner import NATStrategy
from backend.services.provisioning_v2.provisioning_bundle import ProvisioningBundle
from backend.services.provisioning_v2.routeros_command_builder import build_command, build_comment, build_section
from backend.services.provisioning_v2.routeros_renderer_contracts import (
    RenderStatus,
    RouterOSRenderedSection,
    RouterOSSectionName,
)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def render_nat_section(bundle: ProvisioningBundle) -> RouterOSRenderedSection:
    nat = bundle.nat

    commands = [
        build_comment(f"NAT strategy: {nat.strategy.value}"),
    ]

    if not nat.enabled or nat.strategy == NATStrategy.NONE:
        commands.append(build_comment("NAT disabled by provisioning plan"))
    elif nat.strategy == NATStrategy.MASQUERADE:
        for source_network in nat.source_networks:
            commands.append(
                build_command(
                    "/ip firewall nat",
                    "add",
                    {
                        "chain": "srcnat",
                        "action": "masquerade",
                        "src-address": source_network,
                        "out-interface": nat.outbound_interface,
                        "comment": "CAIWAVE managed hotspot masquerade",
                    },
                )
            )
    else:
        commands.append(build_comment(f"NAT strategy {nat.strategy.value} planned but not rendered yet"))

    content = build_section("CAIWAVE NAT", commands)

    return RouterOSRenderedSection(
        name=RouterOSSectionName.NAT,
        status=RenderStatus.RENDERED,
        content=content,
        checksum=_sha256(content),
        warnings=list(nat.warnings),
    )
