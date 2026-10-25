"""
RouterOS RADIUS Renderer for CAIWAVE Provisioning Engine v2.
"""

from __future__ import annotations

import hashlib
import socket
from ipaddress import ip_address

from backend.services.provisioning_v2.provisioning_bundle import ProvisioningBundle
from backend.services.provisioning_v2.routeros_command_builder import (
    RawRouterOSValue,
    build_command,
    build_guarded_add,
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


def _resolve_radius_host(host: str) -> str:
    """
    RouterOS 7.21.4 on some target hardware accepts an IP address for
    /radius add address= but rejects a hostname.

    Keep IP configuration unchanged. Resolve configured hostnames during
    artifact generation so RouterOS receives a concrete IP address.
    """
    try:
        ip_address(host)
        return host
    except ValueError:
        pass

    try:
        addresses = socket.getaddrinfo(
            host,
            None,
            family=socket.AF_INET,
            type=socket.SOCK_DGRAM,
        )
    except socket.gaierror as exc:
        raise ValueError(
            f"Unable to resolve RADIUS host '{host}': {exc}"
        ) from exc

    resolved = []
    for address in addresses:
        ip = address[4][0]
        if ip not in resolved:
            resolved.append(ip)

    if not resolved:
        raise ValueError(
            f"Unable to resolve RADIUS host '{host}': no IPv4 address found"
        )

    return resolved[0]


def render_radius_section(bundle: ProvisioningBundle) -> RouterOSRenderedSection:
    radius = bundle.radius

    commands = [
        build_comment(f"NAS identifier: {radius.nas_identifier}"),
    ]

    if not radius.enabled:
        commands.append(build_comment("RADIUS disabled by provisioning plan"))
    else:
        radius_address = _resolve_radius_host(radius.auth_host)

        commands.append(
            build_comment(
                f"RADIUS host: {radius.auth_host} -> {radius_address}"
            )
        )

        commands.append(
            build_guarded_add(
                "/radius",
                "add",
                {
                    "service": RawRouterOSValue(
                        ",".join(service.value for service in radius.services)
                    ),
                    "address": radius_address,
                    "authentication-port": radius.auth_port,
                    "accounting-port": radius.accounting_port,
                    "secret": radius.secret_ref,
                    "timeout": "3s",
                    "require-message-auth": False,
                    "comment": "CAIWAVE managed RADIUS server",
                },
            )
        )

        commands.append(
            build_command(
                "/radius incoming",
                "set",
                {
                    "accept": radius.coa_enabled,
                },
            )
        )

    content = build_section("CAIWAVE RADIUS", commands)

    return RouterOSRenderedSection(
        name=RouterOSSectionName.RADIUS,
        status=RenderStatus.RENDERED,
        content=content,
        checksum=_sha256(content),
        warnings=list(radius.warnings),
    )
