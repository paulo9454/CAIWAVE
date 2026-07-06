"""
Developer export command for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no router access
- no production route wiring
- no legacy provisioning changes

Generates a deterministic RouterOS .rsc from the golden fresh-hotspot fixture,
validates it through the renderer, lints it, and writes it to disk for CHR
or physical-router import testing.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.provisioning_v2.routeros_render_orchestrator import render_routeros_bundle
from backend.services.provisioning_v2.routeros_script_linter import lint_routeros_script
from backend.tests.test_routeros_golden_fresh_hotspot import build_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="Export CAIWAVE Provisioning v2 RouterOS .rsc")
    parser.add_argument(
        "--output",
        default="artifacts/provisioning_v2/fresh_hotspot_router.rsc",
        help="Output .rsc path",
    )
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    artifact = render_routeros_bundle(bundle=build_bundle())
    lint = lint_routeros_script(artifact.content)

    if not lint.valid:
        print("RouterOS script lint failed:")
        for error in lint.errors:
            print(f"- {error}")
        return 1

    output.write_text(artifact.content)

    print(f"Wrote: {output}")
    print(f"Router ID: {artifact.router_id}")
    print(f"Bundle ID: {artifact.bundle_id}")
    print(f"Checksum: {artifact.checksum}")
    print(f"Sections: {len(artifact.sections)}")
    print("Lint: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
