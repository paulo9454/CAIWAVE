"""
RouterOS Address Renderer for CAIWAVE Provisioning Engine v2.
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


def render_address_section(bundle: ProvisioningBundle) -> RouterOSRenderedSection:
    address = bundle.address

    commands = [
        build_comment(f"Client network: {address.cidr}"),
        build_command(
            "/ip address",
            "add",
            {
                "address": f"{address.gateway_ip}/{address.prefix_length}",
                "interface": address.target_interface,
                "comment": "CAIWAVE managed hotspot gateway",
            },
        ),
    ]

    content = build_section("CAIWAVE Addressing", commands)

    return RouterOSRenderedSection(
        name=RouterOSSectionName.ADDRESSING,
        status=RenderStatus.RENDERED,
        content=content,
        checksum=_sha256(content),
        warnings=list(address.warnings),
    )
