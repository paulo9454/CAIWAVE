"""
RouterOS DNS Renderer for CAIWAVE Provisioning Engine v2.
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


def render_dns_section(bundle: ProvisioningBundle) -> RouterOSRenderedSection:
    dns = bundle.dns

    commands = [
        build_comment(f"Captive DNS name: {dns.captive_dns_name}"),
        build_command(
            "/ip dns",
            "set",
            {
                "allow-remote-requests": dns.router_resolver_enabled,
                "servers": ",".join(dns.upstream_dns_servers),
            },
        ),
    ]

    for hostname, address in sorted(dns.static_records.items()):
        commands.append(
            build_command(
                "/ip dns static",
                "add",
                {
                    "name": hostname,
                    "address": address,
                    "comment": "CAIWAVE managed captive portal DNS record",
                },
            )
        )

    content = build_section("CAIWAVE DNS", commands)

    return RouterOSRenderedSection(
        name=RouterOSSectionName.DNS,
        status=RenderStatus.RENDERED,
        content=content,
        checksum=_sha256(content),
        warnings=list(dns.warnings),
    )
