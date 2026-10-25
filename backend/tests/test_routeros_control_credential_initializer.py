import pytest

from backend.services.provisioning_v2.routeros_control_renderer import (
    RouterOSControlRendererError,
    render_control_credential_initializer,
)


def test_initializer_sets_global_without_installing_scheduler():
    section = render_control_credential_initializer(
        control_secret="control-init-test-secret"
    )

    assert section.checksum
    assert "caiwave-control-credential-init" in section.content
    assert "caiwaveControlSecret" in section.content
    assert "control-init-test-secret" in section.content
    assert "/system script add" in section.content
    assert "/system scheduler add" not in section.content
    assert 'name="caiwave-control"' not in section.content
    assert "/system script run caiwave-control " not in section.content


def test_initializer_rejects_empty_secret():
    with pytest.raises(
        RouterOSControlRendererError,
        match="control_secret is required",
    ):
        render_control_credential_initializer(control_secret="")
