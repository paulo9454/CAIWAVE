"""
Usage accounting helper.

Pure business logic for usage-based WiFi packages.
No database access.
No FastAPI dependency.
No MongoDB dependency.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class UsageAccountingResult:
    delta_seconds: int
    used_seconds: int
    remaining_seconds: int
    expired: bool


def calculate_usage_update(
    *,
    package_duration_seconds: int,
    used_seconds: int,
    last_accounted_session_time: int,
    current_session_time: int,
) -> UsageAccountingResult:
    """
    Calculate a safe usage accounting update.

    Duplicate or out-of-order accounting packets never increase usage.
    """

    delta = max(
        0,
        current_session_time - last_accounted_session_time,
    )

    used = used_seconds + delta

    remaining = max(
        0,
        package_duration_seconds - used,
    )

    return UsageAccountingResult(
        delta_seconds=delta,
        used_seconds=used,
        remaining_seconds=remaining,
        expired=(remaining == 0),
    )
