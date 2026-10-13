"""
RouterOS control-plane renderer for CAIWAVE Provisioning Engine v2.

The control agent:
- polls CAIWAVE for a queued provisioning job;
- reports the claimed job as running;
- downloads the router-owned immutable artifact;
- validates the artifact with RouterOS dry-run import;
- imports the validated artifact;
- reports succeeded/failed;
- removes the temporary artifact.

The control agent does not select physical interfaces. Topology decisions
remain entirely inside the verified provisioning artifact.
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
    quote_routeros_value,
)
from backend.services.provisioning_v2.routeros_renderer_contracts import (
    RenderStatus,
    RouterOSRenderedSection,
    RouterOSSectionName,
)


class RouterOSControlRendererError(ValueError):
    """Raised when the RouterOS control agent cannot be rendered safely."""


CONTROL_SCRIPT_NAME = "caiwave-control"
CONTROL_SCHEDULER_NAME = "caiwave-control"
CONTROL_ARTIFACT_FILE = "caiwave-provisioning.rsc"
CONTROL_INTERVAL = "1m"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _api_base_from_heartbeat(heartbeat_url: str) -> str:
    heartbeat_url = heartbeat_url.strip().rstrip("/")

    parsed = urlparse(heartbeat_url)

    if parsed.scheme != "https" or not parsed.netloc:
        raise RouterOSControlRendererError(
            "heartbeat_url must be an absolute HTTPS URL"
        )

    suffix = "/mikrotik-onboard/heartbeat"

    if not heartbeat_url.endswith(suffix):
        raise RouterOSControlRendererError(
            "heartbeat_url must end with "
            "/mikrotik-onboard/heartbeat"
        )

    return heartbeat_url[: -len(suffix)] + "/mikrotik-onboard"


def _control_source(
    *,
    poll_url: str,
    download_base_url: str,
    result_url: str,
    nas_identifier: str,
    control_secret: str,
) -> str:
    """
    Render the persistent RouterOS control-agent script.

    The script intentionally contains no physical interface assumptions.
    """

    poll_json = (
        '{\\"nas_identifier\\":'
        f'\\"{nas_identifier}\\"'
        '}'
    )

    running_json = (
        '{\\"nas_identifier\\":'
        f'\\"{nas_identifier}\\",'
        '\\\"job_id\\\":\\\"$jobId\\\",'
        '\\"status\\":\\"running\\"'
        '}'
    )

    success_json = (
        '{\\"nas_identifier\\":'
        f'\\"{nas_identifier}\\",'
        '\\\"job_id\\\":\\\"$jobId\\\",'
        '\\"status\\":\\"succeeded\\",'
        '\\"result\\":{'
        '\\\"artifact_id\\\":\\\"$artifactId\\\"'
        '}'
        '}'
    )

    failure_json_prefix = (
        '{\\"nas_identifier\\":'
        f'\\"{nas_identifier}\\",'
        '\\\"job_id\\\":\\\"$jobId\\\",'
        '\\"status\\":\\"failed\\",'
        '\\"error\\":'
    )

    return (
        ':if ([/system script job print count-only as-value '
        'where script=[:jobname]] > 1) do={ :exit; }; '

        ':do { '

        # ---------------------------------------------------------
        # 1. Poll CAIWAVE for a queued provisioning job.
        # ---------------------------------------------------------
        f':local pollBody "{poll_json}"; '

        f':local pollResponse [/tool fetch '
        f'url="{poll_url}" '
        'http-method=post '
        f'http-header-field="Content-Type: application/json,Authorization: Bearer {control_secret}" '
        'http-data=$pollBody '
        'output=user '
        'as-value '
        'check-certificate=yes]; '

        ':if (($pollResponse->"status") != "finished") do={ '
        ':log warning "CAIWAVE control poll did not finish"; '
        ':exit; '
        '}; '

        ':local responseText ($pollResponse->"data"); '

        # ---------------------------------------------------------
        # 2. Deserialize the poll response.
        # ---------------------------------------------------------
        ':local response [:deserialize from=json value=$responseText]; '

        ':if (($response->"job_available") != true) do={ '
        ':exit; '
        '}; '

        ':local job ($response->"job"); '
        ':local jobId ($job->"job_id"); '
        ':local artifactId ($job->"artifact_id"); '

        ':if (([:len $jobId] = 0) or ([:len $artifactId] = 0)) do={ '
        ':log warning "CAIWAVE control response missing job identifiers"; '
        ':exit; '
        '}; '

        # ---------------------------------------------------------
        # 3. Acknowledge that the job is running.
        # ---------------------------------------------------------
        ':do { '

        f':local runningBody "{running_json}"; '

        f'/tool fetch '
        f'url="{result_url}" '
        'http-method=post '
        f'http-header-field="Content-Type: application/json,Authorization: Bearer {control_secret}" '
        'http-data=$runningBody '
        'output=none '
        'check-certificate=yes '

        '} on-error={ '

        ':log warning "CAIWAVE failed to acknowledge running job"; '

        '}; '

        # ---------------------------------------------------------
        # 4. Prepare the fixed temporary artifact filename.
        # ---------------------------------------------------------
        f':local artifactFile "{CONTROL_ARTIFACT_FILE}"; '

        f'/file remove [find where name="{CONTROL_ARTIFACT_FILE}"]; '

        # ---------------------------------------------------------
        # 5. Download and validate/import the immutable artifact.
        # ---------------------------------------------------------
        ':onerror importError in={ '

        f'/tool fetch '
        f'url=("{download_base_url}/" . $artifactId . "/download") '
        'http-method=get '
        f'http-header-field="Authorization: Bearer {control_secret}" '
        'output=file '
        'dst-path=$artifactFile '
        'check-certificate=yes; '

        # First validate the complete RouterOS file without applying it.
        '/import file-name=$artifactFile verbose=yes dry-run; '

        # Only execute after dry-run validation succeeds.
        ':log warning "CAIWAVE control: before provisioning import"; '
        '/import file-name=$artifactFile; '
        ':log warning "CAIWAVE control: provisioning import completed"; '

        # Remove the artifact after successful execution.
        f'/file remove [find where name="{CONTROL_ARTIFACT_FILE}"]; '

        '} do={ '

        # ---------------------------------------------------------
        # 6. Report provisioning failure.
        # ---------------------------------------------------------
        ':do { '

        ':log warning ("CAIWAVE control: provisioning import failed: " . [:tostr $importError]); '
        ':log warning "CAIWAVE control: before failure callback"; '
        ':local errorJson [:serialize to=json value=[:tostr $importError]]; '
        f':local failureBody ("{failure_json_prefix}" . $errorJson . "}}"); '

        f'/tool fetch '
        f'url="{result_url}" '
        'http-method=post '
        f'http-header-field="Content-Type: application/json,Authorization: Bearer {control_secret}" '
        'http-data=$failureBody '
        'output=none '
        'check-certificate=yes '

        ':log warning "CAIWAVE control: failure callback completed"; '

        '} on-error={ '

        ':log warning "CAIWAVE failed to report provisioning failure"; '

        '}; '

        # Always remove a partially downloaded artifact.
        f'/file remove [find where name="{CONTROL_ARTIFACT_FILE}"]; '

        ':log warning "CAIWAVE provisioning artifact import failed"; '

        ':exit; '

        '}; '

        # ---------------------------------------------------------
        # 7. Report provisioning success.
        # ---------------------------------------------------------
        ':do { '

        ':log warning "CAIWAVE control: before success callback"; '

        f':local successBody "{success_json}"; '

        f'/tool fetch '
        f'url="{result_url}" '
        'http-method=post '
        f'http-header-field="Content-Type: application/json,Authorization: Bearer {control_secret}" '
        'http-data=$successBody '
        'output=none '
        'check-certificate=yes '

        ':log warning "CAIWAVE control: success callback completed"; '

        '} on-error={ '

        ':log warning "CAIWAVE failed to report provisioning success"; '

        '}; '

        '} on-error={ '

        ':log warning ("CAIWAVE control agent failed: " . [:tostr $outerError]); '

        '};'
    )


def render_control_section(
    bundle: ProvisioningBundle,
    *,
    control_secret: str | None,
) -> RouterOSRenderedSection:
    """
    Render the persistent CAIWAVE control script and scheduler.
    """

    if not control_secret:
        raise RouterOSControlRendererError(
            "control_secret is required for the RouterOS control agent"
        )

    identity = bundle.snapshot.identity
    heartbeat = bundle.snapshot.heartbeat

    nas_identifier = identity.nas_identifier.strip()

    if not nas_identifier:
        raise RouterOSControlRendererError(
            "NAS identifier is required"
        )

    api_base = _api_base_from_heartbeat(
        heartbeat.heartbeat_url
    )

    poll_url = f"{api_base}/poll"
    download_base_url = f"{api_base}/artifacts"
    result_url = f"{api_base}/job-result"

    source = _control_source(
        poll_url=poll_url,
        download_base_url=download_base_url,
        result_url=result_url,
        nas_identifier=nas_identifier,
        control_secret=control_secret,
    )

    commands = [
        build_comment(
            "CAIWAVE managed provisioning control agent"
        ),
        build_comment(
            "Polls CAIWAVE and executes only router-owned artifacts"
        ),
        build_comment(
            "Topology and physical interface decisions are made by the verified artifact"
        ),

        # Replace only the CAIWAVE-managed control resources.
        f'/system scheduler remove '
        f'[find where name="{CONTROL_SCHEDULER_NAME}"]',

        f'/system script remove '
        f'[find where name="{CONTROL_SCRIPT_NAME}"]',

        # Use the existing RouterOS command builder for safe quoting.
        build_command(
            "/system script",
            "add",
            {
                "name": CONTROL_SCRIPT_NAME,
                "policy": "ftp,read,write,test",
                "source": source,
            },
        ),

        build_command(
            "/system scheduler",
            "add",
            {
                "name": CONTROL_SCHEDULER_NAME,
                "interval": CONTROL_INTERVAL,
                "on-event": CONTROL_SCRIPT_NAME,
                "policy": "ftp,read,write,test",
                "disabled": False,
                "comment": "CAIWAVE managed provisioning control",
            },
        ),

        # Run immediately after installation so the router does not
        # have to wait for the first scheduler interval.
        f"/system script run {CONTROL_SCRIPT_NAME}",
    ]

    content = build_section(
        "CAIWAVE Control Agent Bootstrap",
        commands,
    )
    return RouterOSRenderedSection(
        name=RouterOSSectionName.SCHEDULERS,
        status=RenderStatus.RENDERED,
        content=content,
        checksum=_sha256(content),
        warnings=[],
    )

def render_control_bootstrap(
    *,
    heartbeat_url: str,
    nas_identifier: str,
    control_secret: str,
) -> RouterOSRenderedSection:
    """
    Render a standalone CAIWAVE control-agent bootstrap.

    This bootstrap establishes only the CAIWAVE control channel.
    It does not configure WAN, LAN, bridge, DHCP, NAT, hotspot,
    firewall, RADIUS, or any other production networking state.
    """

    if not control_secret:
        raise RouterOSControlRendererError(
            "control_secret is required for the RouterOS control bootstrap"
        )

    nas_identifier = nas_identifier.strip()

    if not nas_identifier:
        raise RouterOSControlRendererError(
            "NAS identifier is required"
        )

    api_base = _api_base_from_heartbeat(heartbeat_url)

    poll_url = f"{api_base}/poll"
    download_base_url = f"{api_base}/artifacts"
    result_url = f"{api_base}/job-result"

    source = _control_source(
        poll_url=poll_url,
        download_base_url=download_base_url,
        result_url=result_url,
        nas_identifier=nas_identifier,
        control_secret=control_secret,
    )

    commands = [
        # Replace only the CAIWAVE-managed control resources.
        f'/system scheduler remove '
        f'[find where name="{CONTROL_SCHEDULER_NAME}"]',

        f'/system script remove '
        f'[find where name="{CONTROL_SCRIPT_NAME}"]',

        build_command(
            "/system script",
            "add",
            {
                "name": CONTROL_SCRIPT_NAME,
                "policy": "ftp,read,write,test",
                "source": source,
            },
        ),
        build_command(
            "/system scheduler",
            "add",
            {
                "name": CONTROL_SCHEDULER_NAME,
                "interval": CONTROL_INTERVAL,
                "on-event": CONTROL_SCRIPT_NAME,
                "policy": "ftp,read,write,test",
                "start-time": "startup",
            },
        ),
        f"/system script run {quote_routeros_value(CONTROL_SCRIPT_NAME)}",
    ]

    content = build_section(
        "CAIWAVE Control Agent Bootstrap",
        commands,
    ) + "\n"

    return RouterOSRenderedSection(
        name=RouterOSSectionName.SCHEDULERS,
        status=RenderStatus.RENDERED,
        content=content,
        checksum=_sha256(content),
        warnings=[],
    )
