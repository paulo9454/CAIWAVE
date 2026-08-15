from backend.services.provisioning_v2.routeros_discovery_renderer import (
    RouterOSDiscoveryRendererError,
    render_discovery_script,
)


def test_discovery_renderer_generates_read_only_collection_script():
    section = render_discovery_script(
        discovery_url="https://caiwave.com/api/mikrotik-onboard/discovery",
        nas_identifier="CAIWAVE-TEST",
    )

    assert section.status.value == "rendered"
    assert "/interface print as-value" in section.content
    assert "/system resource get board-name" in section.content
    assert "/system resource get version" in section.content
    assert "/system package print as-value" in section.content
    assert "/interface wireless print as-value" in section.content
    assert ":serialize to=json" in section.content
    assert "/tool fetch url=" in section.content
    assert "/system script add" not in section.content
    assert "/system script run" not in section.content
    assert "CAIWAVE observational router discovery" in section.content



def test_discovery_renderer_rejects_non_https_url():
    try:
        render_discovery_script(
            discovery_url="http://caiwave.com/api/mikrotik-onboard/discovery",
            nas_identifier="CAIWAVE-TEST",
        )
    except RouterOSDiscoveryRendererError:
        return

    raise AssertionError("Expected non-HTTPS URL to be rejected")


def test_discovery_renderer_rejects_blank_nas_identifier():
    try:
        render_discovery_script(
            discovery_url="https://caiwave.com/api/mikrotik-onboard/discovery",
            nas_identifier="   ",
        )
    except RouterOSDiscoveryRendererError:
        return

    raise AssertionError("Expected blank NAS identifier to be rejected")

