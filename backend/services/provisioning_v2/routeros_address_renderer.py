"""
RouterOS Address Renderer for CAIWAVE Provisioning Engine v2.
"""

from __future__ import annotations

import hashlib

from backend.services.provisioning_v2.provisioning_bundle import ProvisioningBundle
from backend.services.provisioning_v2.routeros_command_builder import build_command, build_comment, build_section, quote_routeros_value
from backend.services.provisioning_v2.routeros_renderer_contracts import (
    RenderStatus,
    RouterOSRenderedSection,
    RouterOSSectionName,
)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def render_address_section(bundle: ProvisioningBundle) -> RouterOSRenderedSection:
    address = bundle.address

    gateway_address = f"{address.gateway_ip}/{address.prefix_length}"
    gateway_address_value = quote_routeros_value(gateway_address)
    target_interface_value = quote_routeros_value(address.target_interface)
    address_add = build_command(
        "/ip address",
        "add",
        {
            "address": gateway_address,
            "interface": address.target_interface,
            "comment": "CAIWAVE managed hotspot gateway",
        },
    )

    commands = [
        build_comment(f"Client network: {address.cidr}"),
        f':if ([:len [/ip address find where address={gateway_address_value} '
        f'and interface={target_interface_value}]] = 0) do={{ {address_add}; }}',
    ]

    content = build_section("CAIWAVE Addressing", commands)

    return RouterOSRenderedSection(
        name=RouterOSSectionName.ADDRESSING,
        status=RenderStatus.RENDERED,
        content=content,
        checksum=_sha256(content),
        warnings=list(address.warnings),
    )
