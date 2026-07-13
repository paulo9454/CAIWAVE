import pytest

from backend.services.provisioning_v2.routeros_scheduler_renderer import (
    RouterOSSchedulerRendererError,
    render_scheduler_section,
)
from backend.services.provisioning_v2.routeros_renderer_contracts import (
    RenderStatus,
    RouterOSSectionName,
)
from backend.tests.test_routeros_portal_renderer import build_bundle


def test_renders_heartbeat_and_confirmation():
    bundle = build_bundle()
    section = render_scheduler_section(bundle)

    assert section.name == RouterOSSectionName.SCHEDULERS
    assert section.status == RenderStatus.RENDERED
    assert section.checksum

    assert "/system script add" in section.content
    assert "/system scheduler add" in section.content

    assert 'name="caiwave-heartbeat"' in section.content
    assert 'name="caiwave-confirm"' in section.content
    assert 'interval="5m"' in section.content
    assert "disabled=no" in section.content

    assert (
        "https://caiwave.com/api/"
        "mikrotik-onboard/heartbeat"
    ) in section.content
    assert (
        "https://caiwave.com/api/"
        "mikrotik-onboard/confirm"
    ) in section.content

    assert bundle.router_id in section.content
    assert (
        bundle.snapshot.identity.nas_identifier
        in section.content
    )

    assert "/system script run caiwave-confirm" in section.content
    assert "/system script run caiwave-heartbeat" in section.content
    assert "on-error=" in section.content

    assert "heartbeat_token_ref" not in section.content
    assert (
        bundle.snapshot.heartbeat.heartbeat_token_ref
        not in section.content
    )


def test_replaces_existing_managed_scheduler():
    section = render_scheduler_section(build_bundle())

    assert (
        '/system scheduler remove '
        '[find where name="caiwave-heartbeat"]'
    ) in section.content
    assert (
        '/system script remove '
        '[find where name="caiwave-heartbeat"]'
    ) in section.content
    assert (
        '/system script remove '
        '[find where name="caiwave-confirm"]'
    ) in section.content


def test_rejects_unexpected_heartbeat_path():
    bundle = build_bundle()
    bad_snapshot = bundle.snapshot.model_copy(
        update={
            "heartbeat": (
                bundle.snapshot.heartbeat.model_copy(
                    update={
                        "heartbeat_url": (
                            "https://caiwave.com/api/wrong"
                        )
                    }
                )
            )
        }
    )
    bad_bundle = bundle.model_copy(
        update={"snapshot": bad_snapshot}
    )

    with pytest.raises(
        RouterOSSchedulerRendererError,
        match="must end with",
    ):
        render_scheduler_section(bad_bundle)
