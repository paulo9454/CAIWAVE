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
) -> RouterOSRenderedSection:
    discovery_url = _validate_url(discovery_url)

    nas_identifier = nas_identifier.strip()
    if not nas_identifier:
        raise RouterOSDiscoveryRendererError(
            "NAS identifier is required"
        )

    script_body = (
        ':local interfaces [/interface print as-value]; '
        ':local bridges [/interface bridge print as-value]; '
        ':local vlans [/interface vlan print as-value]; '
        ':local addresses [/ip address print as-value]; '
        ':local routes [/ip route print as-value]; '
        ':local packages [/system package print as-value]; '
        ':local board [/system resource get board-name]; '
        ':local version [/system resource get version]; '
        ':local architecture [/system resource get architecture-name]; '
        ':local wireless {}; '
        ':do { '
        ':set wireless [/interface wireless print as-value]; '
        '} on-error={ '
        ':set wireless {}; '
        '}; '
        ':local payload { '
        '"nas_identifier"=$nas_identifier; '
        '"router"={ '
        '"board_name"=$board; '
        '"routeros_version"=$version; '
        '"architecture"=$architecture; '
        '}; '
        '"interfaces"=$interfaces; '
        '"bridges"=$bridges; '
        '"vlans"=$vlans; '
        '"addresses"=$addresses; '
        '"routes"=$routes; '
        '"packages"=$packages; '
        '"wireless_interfaces"=$wireless; '
        '}; '
        ':local json [:serialize to=json value=$payload]; '
        f'/tool fetch url="{discovery_url}" '
        'http-method=post '
        'http-header-field="Content-Type: application/json" '
        'http-data=$json '
        'keep-result=no;'
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
