"""
RouterOS DHCP Renderer for CAIWAVE Provisioning Engine v2.
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


def render_dhcp_section(bundle: ProvisioningBundle) -> RouterOSRenderedSection:
    dhcp = bundle.dhcp

    commands = [
        build_comment(f"DHCP pool: {dhcp.pool_start}-{dhcp.pool_end}"),
        build_command(
            "/ip pool",
            "add",
            {
                "name": dhcp.pool_name,
                "ranges": f"{dhcp.pool_start}-{dhcp.pool_end}",
                "comment": "CAIWAVE managed hotspot DHCP pool",
            },
        ),
        build_command(
            "/ip dhcp-server",
            "add",
            {
                "name": dhcp.server_name,
                "interface": dhcp.target_interface,
                "address-pool": dhcp.pool_name,
                "lease-time": dhcp.lease_time,
                "authoritative": RawRouterOSValue(dhcp.authoritative.value.replace("_", "-")),
                "disabled": False,
                "comment": "CAIWAVE managed hotspot DHCP server",
            },
        ),
        build_command(
            "/ip dhcp-server network",
            "add",
            {
                "address": dhcp.network_cidr,
                "gateway": dhcp.gateway_ip,
                "dns-server": ",".join(dhcp.dns_servers),
                "comment": "CAIWAVE managed hotspot DHCP network",
            },
        ),
    ]

    content = build_section("CAIWAVE DHCP", commands)

    return RouterOSRenderedSection(
        name=RouterOSSectionName.DHCP,
        status=RenderStatus.RENDERED,
        content=content,
        checksum=_sha256(content),
        warnings=list(dhcp.warnings),
    )
