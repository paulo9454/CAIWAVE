"""
RouterOS Discovery Renderer for CAIWAVE Provisioning Engine v2.

Safety:
- discovery only
- no configuration mutation
- no topology changes
- no provisioning decisions
- not included in the default render order

The generated RouterOS script collects observed router facts and POSTs them
to a CAIWAVE discovery endpoint.
"""

from __future__ import annotations

import hashlib
from urllib.parse import urlparse

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


class RouterOSDiscoveryRendererError(ValueError):
    """Raised when the discovery script cannot be rendered safely."""


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _validate_url(url: str) -> str:
    value = url.strip().rstrip("/")

    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RouterOSDiscoveryRendererError(
            "discovery_url must be an absolute HTTPS URL"
        )

    return value

def render_discovery_script(
    *,
    discovery_url: str,
    nas_identifier: str,
    control_secret: str,
) -> RouterOSRenderedSection:

    discovery_url = _validate_url(discovery_url)

    nas_identifier = nas_identifier.strip()
    if not nas_identifier:
        raise RouterOSDiscoveryRendererError(
            "NAS identifier is required"
        )
    control_secret = control_secret.strip()
    if not control_secret:
        raise RouterOSDiscoveryRendererError(
            "MikroTik control secret is required"
        )

    script_body = (
        ':do { '
        f':local nasid "{nas_identifier}"; '
        ':local interfaces [/interface print as-value]; '
        ':local bridges [/interface bridge print as-value]; '
        ':local bridgeports [/interface bridge port print as-value]; '
        ':local vlans [/interface vlan print as-value]; '
        ':local dhcpservers [/ip dhcp-server print as-value]; '
        ':local dhcpclients [/ip dhcp-client print as-value]; '
        ':local hotspots [/ip hotspot print as-value]; '
        ':local addresses [/ip address print as-value]; '
        ':local routes [/ip route print as-value]; '
        ':local packages [/system package print as-value]; '
        ':local boardname [/system resource get board-name]; '
        ':local rosver [/system resource get version]; '
        ':local arch [/system resource get architecture-name]; '
        ':local payload { '
        '"nas_identifier"=$nasid; '
        '"router"={ '
        '"board_name"=$boardname; '
        '"routeros_version"=$rosver; '
        '"architecture"=$arch '
        '}; '
        '"interfaces"=$interfaces; '
        '"bridges"=$bridges; '
        '"bridge_ports"=$bridgeports; '
        '"vlans"=$vlans; '
        '"dhcp_servers"=$dhcpservers; '
        '"dhcp_clients"=$dhcpclients; '
        '"hotspots"=$hotspots; '
        '"addresses"=$addresses; '
        '"routes"=$routes; '
        '"packages"=$packages '
        '}; '
        ':local json [:serialize to=json value=$payload]; '
        ':if ([:len $json] <= 60000) do={ '
        f'/tool fetch url="{discovery_url}" '
        'http-method=post '
        f'http-header-field="Content-Type: application/json,Authorization: Bearer {control_secret}" '
        'http-data=$json '
        'keep-result=no; '
        '}; '
        '} on-error={ :log warning "CAIWAVE discovery execution failed"; };'
    )

    commands = [
        build_comment(
            "CAIWAVE observational router discovery"
        ),
        build_comment(
            "Discovery reads router state and sends it to CAIWAVE"
        ),
        script_body,
    ]

    content = build_section(
        "CAIWAVE Router Discovery",
        commands,
    )

    return RouterOSRenderedSection(
        name=RouterOSSectionName.DISCOVERY,
        status=RenderStatus.RENDERED,
        content=content,
        checksum=_sha256(content),
        warnings=[],
    )
