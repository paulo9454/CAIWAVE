"""
CAIWAVE MikroTik Provisioning Builder.

This is the single compatibility entry point for MikroTik provisioning.

All provisioning decisions and RouterOS generation are owned by
Provisioning Engine v2.

Do not add alternate provisioning generators here.
"""

from __future__ import annotations

from backend.services.provisioning_v2.mikrotik_builder_adapter import (
    build_provisioning_v2_rsc_from_router,
)


def build_mikrotik_script(router: dict) -> str:
    """
    Build the single authoritative CAIWAVE MikroTik provisioning script.

    Compatibility API:
        Existing callers continue using build_mikrotik_script(router).

    Implementation:
        Provisioning Engine v2 only.

    There is intentionally no legacy fallback.
    """

    result = build_provisioning_v2_rsc_from_router(router)

    if not isinstance(result.content, str):
        raise TypeError(
            "Provisioning Engine v2 must return RouterOS script content as str"
        )

    if not result.content.strip():
        raise RuntimeError(
            "Provisioning Engine v2 returned an empty provisioning script"
        )

    return result.content
