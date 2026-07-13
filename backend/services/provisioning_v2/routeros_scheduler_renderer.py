"""
RouterOS scheduler renderer for CAIWAVE Provisioning Engine v2.

Generates:
- one immediate provisioning confirmation;
- one immediate heartbeat;
- one recurring heartbeat scheduler.

The callbacks are non-blocking so a temporary CAIWAVE outage cannot stop
the remaining RouterOS import.
"""

from __future__ import annotations

import hashlib
from urllib.parse import urlparse

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


class RouterOSSchedulerRendererError(ValueError):
    """Raised when scheduler callbacks cannot be rendered safely."""


HEARTBEAT_SCRIPT_NAME = "caiwave-heartbeat"
CONFIRM_SCRIPT_NAME = "caiwave-confirm"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _confirm_url(heartbeat_url: str) -> str:
    heartbeat_url = heartbeat_url.strip().rstrip("/")

    parsed = urlparse(heartbeat_url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RouterOSSchedulerRendererError(
            "heartbeat_url must be an absolute HTTPS URL"
        )

    suffix = "/mikrotik-onboard/heartbeat"
    if not heartbeat_url.endswith(suffix):
        raise RouterOSSchedulerRendererError(
            "heartbeat_url must end with "
            "/mikrotik-onboard/heartbeat"
        )

    return heartbeat_url[: -len("heartbeat")] + "confirm"


def _routeros_interval(seconds: int) -> str:
    if not isinstance(seconds, int) or seconds <= 0:
        raise RouterOSSchedulerRendererError(
            "heartbeat interval must be greater than zero"
        )

    if seconds % 3600 == 0:
        return f"{seconds // 3600}h"

    if seconds % 60 == 0:
        return f"{seconds // 60}m"

    return f"{seconds}s"


def _fetch_source(
    *,
    url: str,
    json_body: str,
    failure_log: str,
) -> str:
    return (
        ':do {'
        f' /tool fetch url="{url}"'
        ' http-method=post'
        ' http-header-field="Content-Type: application/json"'
        f' http-data="{json_body}"'
        ' keep-result=no;'
        f' }} on-error={{ :log warning "{failure_log}"; }}'
    )


def render_scheduler_section(
    bundle: ProvisioningBundle,
) -> RouterOSRenderedSection:
    heartbeat = bundle.snapshot.heartbeat
    identity = bundle.snapshot.identity

    heartbeat_url = heartbeat.heartbeat_url.strip().rstrip("/")
    confirm_url = _confirm_url(heartbeat_url)
    interval = _routeros_interval(
        heartbeat.heartbeat_interval_seconds
    )

    nas_identifier = identity.nas_identifier
    router_id = bundle.router_id

    if not nas_identifier:
        raise RouterOSSchedulerRendererError(
            "NAS identifier is required"
        )

    if not router_id:
        raise RouterOSSchedulerRendererError(
            "router ID is required"
        )

    heartbeat_json = (
        '{\\"nas_identifier\\":'
        f'\\"{nas_identifier}\\"'
        '}'
    )
    confirm_json = (
        '{\\"router_id\\":'
        f'\\"{router_id}\\",'
        '\\"nas_identifier\\":'
        f'\\"{nas_identifier}\\"'
        '}'
    )

    heartbeat_source = _fetch_source(
        url=heartbeat_url,
        json_body=heartbeat_json,
        failure_log=(
            "CAIWAVE heartbeat failed; scheduler will retry"
        ),
    )
    confirm_source = _fetch_source(
        url=confirm_url,
        json_body=confirm_json,
        failure_log=(
            "CAIWAVE provisioning confirmation failed"
        ),
    )

    commands = [
        build_comment(
            f"Heartbeat interval: "
            f"{heartbeat.heartbeat_interval_seconds}s"
        ),
        build_comment(f"Heartbeat URL: {heartbeat_url}"),
        build_comment(f"Confirmation URL: {confirm_url}"),

        (
            f'/system scheduler remove '
            f'[find where name="{HEARTBEAT_SCRIPT_NAME}"]'
        ),
        (
            f'/system script remove '
            f'[find where name="{HEARTBEAT_SCRIPT_NAME}"]'
        ),
        (
            f'/system script remove '
            f'[find where name="{CONFIRM_SCRIPT_NAME}"]'
        ),

        build_command(
            "/system script",
            "add",
            {
                "name": HEARTBEAT_SCRIPT_NAME,
                "policy": "read,write,test",
                "source": heartbeat_source,
            },
        ),
        build_command(
            "/system script",
            "add",
            {
                "name": CONFIRM_SCRIPT_NAME,
                "policy": "read,write,test",
                "source": confirm_source,
            },
        ),
        build_command(
            "/system scheduler",
            "add",
            {
                "name": HEARTBEAT_SCRIPT_NAME,
                "interval": interval,
                "on-event": HEARTBEAT_SCRIPT_NAME,
                "disabled": False,
                "comment": (
                    "CAIWAVE managed heartbeat scheduler"
                ),
            },
        ),

        f"/system script run {CONFIRM_SCRIPT_NAME}",
        f"/system script run {HEARTBEAT_SCRIPT_NAME}",
    ]

    content = build_section(
        "CAIWAVE Heartbeat and Confirmation",
        commands,
    )

    return RouterOSRenderedSection(
        name=RouterOSSectionName.SCHEDULERS,
        status=RenderStatus.RENDERED,
        content=content,
        checksum=_sha256(content),
        warnings=[],
    )
