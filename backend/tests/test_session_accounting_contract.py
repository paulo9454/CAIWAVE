"""Runtime WiFi session lifecycle contracts."""

from pathlib import Path
import ast


SERVER_PATH = Path(__file__).resolve().parents[1] / "server.py"


def _function_source(function_name: str) -> str:
    source = SERVER_PATH.read_text()
    tree = ast.parse(source)

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == function_name:
                return ast.get_source_segment(source, node) or ""

    raise AssertionError(f"Function {function_name!r} not found")


def test_accounting_stop_does_not_complete_valid_entitlement():
    source = _function_source("radius_accounting")

    assert '"status": "completed"' not in source
    assert "session_status = SessionStatus.ACTIVE.value" in source
    assert "session_status = SessionStatus.EXPIRED.value" in source


def test_accounting_stop_preserves_disconnect_and_usage_statistics():
    source = _function_source("radius_accounting")

    required_fields = (
        '"disconnected_at": now',
        '"total_session_time": session_time',
        '"total_upload_bytes": input_octets',
        '"total_download_bytes": output_octets',
        '"data_used_mb": total_mb',
        '"status": session_status',
    )

    for field in required_fields:
        assert field in source
