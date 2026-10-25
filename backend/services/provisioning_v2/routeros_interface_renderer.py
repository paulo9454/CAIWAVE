"""
RouterOS Interface Renderer for CAIWAVE Provisioning Engine v2.

Renders upstream/WAN interface configuration from validated topology intent.
"""

from __future__ import annotations

import hashlib

from backend.services.provisioning_v2.provisioning_bundle import (
    ProvisioningBundle,
)
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


class RouterOSInterfaceRendererError(ValueError):
    """Raised when the interface section cannot be rendered safely."""


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def render_interface_section(
    bundle: ProvisioningBundle,
) -> RouterOSRenderedSection:
    wan_interface = bundle.topology.upstream_interface

    if not wan_interface:
        raise RouterOSInterfaceRendererError(
            "Topology upstream interface is required"
        )

    if wan_interface in bundle.topology.client_interfaces:
        raise RouterOSInterfaceRendererError(
            "WAN interface cannot also be a client interface"
        )

    add_command = build_command(
        "/ip dhcp-client",
        "add",
        {
            "interface": wan_interface,
            "add-default-route": True,
            "default-route-distance": 1,
            "use-peer-dns": True,
            "use-peer-ntp": True,
            "disabled": False,
            "comment": "CAIWAVE managed WAN DHCP client",
        },
    )
    # Preserve an existing WAN DHCP client and its default route.
    # Only create one when this interface has no DHCP client.
    conditional_command = (
        f':if ([:len $wanDhcpClients] = 0) do={{ {add_command}; }}'
    )

    commands = [
        build_comment(f"WAN interface: {wan_interface}"),
        f':local wanDhcpClients [/ip dhcp-client find where interface="{wan_interface}"]',
        conditional_command,
    ]

    content = build_section("CAIWAVE Interfaces", commands)

    return RouterOSRenderedSection(
        name=RouterOSSectionName.INTERFACES,
        status=RenderStatus.RENDERED,
        content=content,
        checksum=_sha256(content),
        warnings=[],
    )
