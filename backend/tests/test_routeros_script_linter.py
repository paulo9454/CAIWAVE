from backend.tests.test_routeros_golden_fresh_hotspot import build_bundle

from backend.services.provisioning_v2.routeros_render_orchestrator import render_routeros_bundle
from backend.services.provisioning_v2.routeros_script_linter import lint_routeros_script


def test_lints_rendered_fresh_hotspot_script():
    artifact = render_routeros_bundle(bundle=build_bundle())

    result = lint_routeros_script(artifact.content)

    assert result.valid is True
    assert result.errors == []


def test_rejects_empty_script():
    result = lint_routeros_script("")

    assert result.valid is False
    assert "RouterOS script is empty" in result.errors


def test_detects_missing_required_command():
    result = lint_routeros_script('/system identity set name="router"\n')

    assert result.valid is False
    assert any("Missing required RouterOS command" in error for error in result.errors)


def test_detects_unresolved_template_marker():
    artifact = render_routeros_bundle(bundle=build_bundle())
    result = lint_routeros_script(artifact.content + "\n{{UNRESOLVED}}\n")

    assert result.valid is False
    assert "Unresolved or forbidden token found: {{" in result.errors


def test_detects_unbalanced_quotes():
    script = '/system identity set name="router\n'

    result = lint_routeros_script(script)

    assert result.valid is False
    assert any("unbalanced quotes" in error for error in result.errors)


def test_detects_duplicate_commands():
    artifact = render_routeros_bundle(bundle=build_bundle())
    first_command = next(
        line for line in artifact.content.splitlines()
        if line.startswith("/system identity set")
    )

    result = lint_routeros_script(artifact.content + first_command + "\n")

    assert result.valid is False
    assert any("Duplicate RouterOS command found" in error for error in result.errors)
