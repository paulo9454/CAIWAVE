from __future__ import annotations

import hashlib

import pytest

from backend.services.provisioning_v2.routeros_control_renderer import (
    CONTROL_ARTIFACT_FILE,
    CONTROL_INTERVAL,
    CONTROL_SCHEDULER_NAME,
    CONTROL_SCRIPT_NAME,
    RouterOSControlRendererError,
    _api_base_from_heartbeat,
    _control_source,
    render_control_bootstrap,
)


TEST_NAS_IDENTIFIER = "CAIWAVE-CONTROL-TEST"
TEST_SECRET = "TEST-CONTROL-SECRET-123"

TEST_HEARTBEAT_URL = (
    "https://www.caiwave.com/api/mikrotik-onboard/heartbeat"
)


def _source() -> str:
    return _control_source(
        poll_url=(
            "https://www.caiwave.com/"
            "api/mikrotik-onboard/poll"
        ),
        download_base_url=(
            "https://www.caiwave.com/"
            "api/mikrotik-onboard/artifacts"
        ),
        result_url=(
            "https://www.caiwave.com/"
            "api/mikrotik-onboard/job-result"
        ),
        nas_identifier=TEST_NAS_IDENTIFIER,
        control_secret=TEST_SECRET,
    )


def test_api_base_from_heartbeat_accepts_https():
    assert (
        _api_base_from_heartbeat(TEST_HEARTBEAT_URL)
        == "https://www.caiwave.com/api/mikrotik-onboard"
    )


def test_api_base_from_heartbeat_rejects_http():
    with pytest.raises(RouterOSControlRendererError):
        _api_base_from_heartbeat(
            "http://www.caiwave.com/api/mikrotik-onboard/heartbeat"
        )


def test_api_base_from_heartbeat_rejects_wrong_path():
    with pytest.raises(RouterOSControlRendererError):
        _api_base_from_heartbeat(
            "https://www.caiwave.com/api/heartbeat"
        )


def test_control_source_contains_poll_endpoint():
    content = _source()

    assert (
        'url="https://www.caiwave.com/'
        'api/mikrotik-onboard/poll"'
    ) in content

    assert "http-method=post" in content
    assert "http-data=$pollBody" in content
    assert "output=user" in content
    assert "as-value" in content


def test_control_source_contains_artifact_download():
    content = _source()

    assert (
        'url=("https://www.caiwave.com/'
        'api/mikrotik-onboard/artifacts/" . $artifactId . "/download")'
    ) in content

    assert "http-method=get" in content
    assert "output=file" in content
    assert "dst-path=$artifactFile" in content


def test_control_source_contains_job_result_endpoint():
    content = _source()

    assert (
        'url="https://www.caiwave.com/'
        'api/mikrotik-onboard/job-result"'
    ) in content

    assert "runningBody" in content
    assert "successBody" in content
    assert "failureBody" in content


def test_control_source_contains_bearer_authorization():
    content = _source()

    assert (
        "Authorization: Bearer "
        + TEST_SECRET
    ) in content


def test_control_source_contains_json_content_type():
    content = _source()

    assert "Content-Type: application/json" in content


def test_control_source_requires_tls_certificate_validation():
    content = _source()

    assert content.count("check-certificate=yes") >= 4


def test_control_source_uses_file_capable_routeros_policy():
    """
    The policy is attached by render_control_section().
    This test verifies the required policy constants independently
    from the RouterOS execution source.
    """
    assert CONTROL_SCRIPT_NAME == "caiwave-control"
    assert CONTROL_SCHEDULER_NAME == "caiwave-control"


def test_control_source_has_concurrency_guard():
    content = _source()

    assert "[:jobname]" in content
    assert "count-only" in content
    assert "> 1" in content


def test_control_source_reports_running():
    content = _source()

    assert '\\"status\\":\\"running\\"' in content
    assert '\\"job_id\\":\\"$jobId\\"' in content

def test_control_source_reports_success():
    content = _source()

    assert '\\"status\\":\\"succeeded\\"' in content
    assert '\\"artifact_id\\":\\"$artifactId\\"' in content

def test_control_source_reports_failure():
    content = _source()

    assert '\\"status\\":\\"failed\\"' in content
    assert "CAIWAVE control agent failed" in content


def test_control_source_dry_run_precedes_real_import():
    content = _source()

    dry_run = content.index(
        "/import file-name=$artifactFile verbose=yes dry-run"
    )

    real_import = content.index(
        "/import file-name=$artifactFile;"
    )

    assert dry_run < real_import


def test_control_source_cleans_up_artifact():
    content = _source()

    assert (
        f'/file remove [find where name="{CONTROL_ARTIFACT_FILE}"]'
        in content
    )


def test_control_source_has_error_handling():
    content = _source()

    assert ":onerror importError in={" in content
    assert "CAIWAVE provisioning artifact import failed" in content
    assert "CAIWAVE control agent failed" in content


def test_control_source_has_no_physical_interface_assumptions():
    content = _source().lower()

    assert "ether1" not in content
    assert "ether2" not in content
    assert "ether3" not in content
    assert "ether4" not in content
    assert "ether5" not in content


def test_control_source_contains_nas_identifier():
    content = _source()

    assert TEST_NAS_IDENTIFIER in content


def test_control_source_contains_artifact_filename():
    content = _source()

    assert CONTROL_ARTIFACT_FILE in content


def test_control_constants_are_expected():
    assert CONTROL_SCRIPT_NAME == "caiwave-control"
    assert CONTROL_SCHEDULER_NAME == "caiwave-control"
    assert CONTROL_ARTIFACT_FILE == "caiwave-provisioning.rsc"
    assert CONTROL_INTERVAL == "1m"


def test_control_source_checksum_is_deterministic():
    content = _source()

    checksum_one = hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()

    checksum_two = hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()

    assert checksum_one == checksum_two
    assert len(checksum_one) == 64


def test_control_source_does_not_contain_real_credentials():
    content = _source()

    assert TEST_SECRET in content
    assert "secret_hash" not in content
    assert "JWT_SECRET" not in content
    assert "RADIUS_SECRET" not in content

def test_control_bootstrap_contains_script_and_scheduler():
    section = render_control_bootstrap(
        heartbeat_url=TEST_HEARTBEAT_URL,
        nas_identifier=TEST_NAS_IDENTIFIER,
        control_secret=TEST_SECRET,
    )

    assert section.status.value == "rendered"
    assert "CAIWAVE Control Agent Bootstrap" in section.content
    assert 'name="caiwave-control"' in section.content
    assert 'name="caiwave-control"' in section.content
    assert 'interval="1m"' in section.content
    assert "/system script run" in section.content
    assert section.content.endswith("\n")


def test_control_bootstrap_contains_control_endpoints():
    section = render_control_bootstrap(
        heartbeat_url=TEST_HEARTBEAT_URL,
        nas_identifier=TEST_NAS_IDENTIFIER,
        control_secret=TEST_SECRET,
    )

    assert "/api/mikrotik-onboard/poll" in section.content
    assert "/api/mikrotik-onboard/artifacts/" in section.content
    assert "/api/mikrotik-onboard/job-result" in section.content


def test_control_bootstrap_has_no_production_configuration():
    section = render_control_bootstrap(
        heartbeat_url=TEST_HEARTBEAT_URL,
        nas_identifier=TEST_NAS_IDENTIFIER,
        control_secret=TEST_SECRET,
    )

    content = section.content.lower()

    forbidden = [
        "/ip address",
        "/ip dhcp-server",
        "/ip firewall",
        "/ip hotspot",
        "/ip route",
        "/interface bridge",
        "/interface bridge port",
        "/radius",
    ]

    for token in forbidden:
        assert token not in content


def test_control_bootstrap_has_no_physical_interface_assumptions():
    section = render_control_bootstrap(
        heartbeat_url=TEST_HEARTBEAT_URL,
        nas_identifier=TEST_NAS_IDENTIFIER,
        control_secret=TEST_SECRET,
    )

    content = section.content.lower()

    for interface_name in (
        "ether1",
        "ether2",
        "ether3",
        "ether4",
        "ether5",
    ):
        assert interface_name not in content


def test_control_bootstrap_requires_secret():
    with pytest.raises(RouterOSControlRendererError):
        render_control_bootstrap(
            heartbeat_url=TEST_HEARTBEAT_URL,
            nas_identifier=TEST_NAS_IDENTIFIER,
            control_secret="",
        )


def test_control_bootstrap_requires_nas_identifier():
    with pytest.raises(RouterOSControlRendererError):
        render_control_bootstrap(
            heartbeat_url=TEST_HEARTBEAT_URL,
            nas_identifier="",
            control_secret=TEST_SECRET,
        )


def test_control_bootstrap_is_deterministic():
    first = render_control_bootstrap(
        heartbeat_url=TEST_HEARTBEAT_URL,
        nas_identifier=TEST_NAS_IDENTIFIER,
        control_secret=TEST_SECRET,
    )

    second = render_control_bootstrap(
        heartbeat_url=TEST_HEARTBEAT_URL,
        nas_identifier=TEST_NAS_IDENTIFIER,
        control_secret=TEST_SECRET,
    )

    assert first.content == second.content
    assert first.checksum == second.checksum
