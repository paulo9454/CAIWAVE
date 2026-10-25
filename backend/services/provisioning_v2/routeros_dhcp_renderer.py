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
    quote_routeros_value,
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

    pool_name_value = quote_routeros_value(dhcp.pool_name)
    server_name_value = quote_routeros_value(dhcp.server_name)
    network_cidr_value = quote_routeros_value(dhcp.network_cidr)

    pool_add = build_command(
        "/ip pool",
        "add",
        {
            "name": dhcp.pool_name,
            "ranges": f"{dhcp.pool_start}-{dhcp.pool_end}",
            "comment": "CAIWAVE managed hotspot DHCP pool",
        },
    )
    server_add = build_command(
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
    )
    network_add = build_command(
        "/ip dhcp-server network",
        "add",
        {
            "address": dhcp.network_cidr,
            "gateway": dhcp.gateway_ip,
            "dns-server": ",".join(dhcp.dns_servers),
            "comment": "CAIWAVE managed hotspot DHCP network",
        },
    )

    commands = [
        build_comment(f"DHCP pool: {dhcp.pool_start}-{dhcp.pool_end}"),
        f':if ([:len [/ip pool find where name={pool_name_value}]] = 0) do={{ {pool_add}; }}',
        f':if ([:len [/ip dhcp-server find where name={server_name_value}]] = 0) do={{ {server_add}; }}',
        f':if ([:len [/ip dhcp-server network find where address={network_cidr_value}]] = 0) do={{ {network_add}; }}',
    ]
    content = build_section("CAIWAVE DHCP", commands)

    return RouterOSRenderedSection(
        name=RouterOSSectionName.DHCP,
        status=RenderStatus.RENDERED,
        content=content,
        checksum=_sha256(content),
        warnings=list(dhcp.warnings),
    )
