from backend.services.provisioning_v2.routeros_scheduler_renderer import (
    _fetch_source,
)


def test_scheduler_callbacks_do_not_depend_on_credential_initializer():
    urls = [
        "https://www.caiwave.com/api/mikrotik-onboard/heartbeat",
        "https://www.caiwave.com/api/mikrotik-onboard/confirm",
    ]

    for url in urls:
        source = _fetch_source(
            url=url,
            json_body=r'{\"nas_identifier\":\"CAIWAVE-TEST\"}',
            failure_log="CAIWAVE callback failed",
        )

        assert "caiwave-control-credential-init" not in source
        assert ":global caiwaveControlSecret;" in source
        assert "Authorization: Bearer $caiwaveControlSecret" in source


def test_control_agent_advertises_safe_replay_and_stops_on_failed_running_ack():
    from backend.services.provisioning_v2.routeros_control_renderer import (
        _control_source,
    )

    source = _control_source(
        poll_url="https://www.caiwave.com/api/mikrotik-onboard/poll",
        download_base_url=(
            "https://www.caiwave.com/api/mikrotik-onboard/artifacts"
        ),
        result_url="https://www.caiwave.com/api/mikrotik-onboard/job-result",
        nas_identifier="CAIWAVE-TEST",
        control_secret="test-secret",
    )

    assert "supports_safe_dispatched_replay" in source

    ack_failure = source.index(
        ':log warning "CAIWAVE failed to acknowledge running job";'
    )
    exit_after_failure = source.index(":exit;", ack_failure)
    artifact_download = source.index(":local artifactFile")

    assert ack_failure < exit_after_failure < artifact_download
