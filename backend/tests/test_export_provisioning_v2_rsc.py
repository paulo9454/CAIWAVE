import subprocess
import sys
from pathlib import Path


def test_export_provisioning_v2_rsc_command(tmp_path):
    output = tmp_path / "fresh_hotspot_router.rsc"

    result = subprocess.run(
        [
            sys.executable,
            "backend/scripts/export_provisioning_v2_rsc.py",
            "--output",
            str(output),
        ],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert output.exists()
    content = output.read_text()

    assert "/system identity set" in content
    assert "/ip hotspot add" in content
    assert "/radius add" in content
    assert "Lint: passed" in result.stdout
