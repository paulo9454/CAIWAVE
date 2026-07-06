from backend.tests.test_routeros_golden_fresh_hotspot import build_bundle

from backend.services.provisioning_v2.routeros_render_orchestrator import render_routeros_bundle
from backend.services.provisioning_v2.routeros_renderer_contracts import RenderStatus


def test_rendered_artifact_is_complete_and_rendered():
    artifact = render_routeros_bundle(bundle=build_bundle())

    assert artifact.status == RenderStatus.RENDERED
    assert artifact.content
    assert artifact.checksum
    assert artifact.filename == "router-1-provisioning-v2.rsc"
    assert artifact.content_type == "text/routeros-script"


def test_rendered_artifact_is_deterministic():
    first = render_routeros_bundle(bundle=build_bundle())
    second = render_routeros_bundle(bundle=build_bundle())

    assert first.content == second.content
    assert first.checksum == second.checksum


def test_rendered_artifact_section_order_is_stable():
    artifact = render_routeros_bundle(bundle=build_bundle())

    expected_order = [
        "header",
        "identity",
        "interfaces",
        "bridge",
        "addressing",
        "dhcp",
        "dns",
        "nat",
        "hotspot",
        "portal",
        "radius",
        "firewall",
        "schedulers",
        "validation",
        "footer",
    ]

    assert [section.name.value for section in artifact.sections] == expected_order


def test_rendered_artifact_has_no_empty_required_sections():
    artifact = render_routeros_bundle(bundle=build_bundle())

    rendered_sections = {
        section.name.value: section.content
        for section in artifact.sections
    }

    for name in [
        "identity",
        "bridge",
        "addressing",
        "dhcp",
        "dns",
        "nat",
        "hotspot",
        "portal",
        "radius",
        "firewall",
    ]:
        assert rendered_sections[name].strip()


def test_rendered_artifact_has_no_duplicate_critical_commands():
    artifact = render_routeros_bundle(bundle=build_bundle())
    lines = [line.strip() for line in artifact.content.splitlines() if line.strip()]

    critical_prefixes = [
        '/system identity set name="GOODlife"',
        '/interface bridge add',
        '/ip address add',
        '/ip pool add',
        '/ip dhcp-server add',
        '/ip dns set',
        '/ip hotspot add',
        '/radius add',
    ]

    for prefix in critical_prefixes:
        matches = [line for line in lines if line.startswith(prefix)]
        assert len(matches) == 1, f"Expected exactly one command for {prefix}, got {matches}"


def test_rendered_artifact_contains_no_unresolved_template_markers():
    artifact = render_routeros_bundle(bundle=build_bundle())

    forbidden = ["{{", "}}", "${", "<TODO", "TODO:", "None"]

    for token in forbidden:
        assert token not in artifact.content
