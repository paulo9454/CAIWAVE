from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable
from uuid import uuid4


SOURCE_TYPES = {
    "campaign",
    "live_stream",
    "announcement",
    "marketplace",
}

COVERAGE_SCOPES = {
    "national",
    "county",
    "constituency",
    "specific_hotspots",
}


class PortalNotificationValidationError(ValueError):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(message)


def _required_text(value: object, field: str) -> str:
    normalized = str(value or "").strip()

    if not normalized:
        raise PortalNotificationValidationError(
            field,
            f"{field.replace('_', ' ').title()} is required.",
        )

    return normalized


def _optional_text(value: object) -> str | None:
    normalized = str(value or "").strip()
    return normalized or None


def _normalize_values(values: Iterable[object] | None) -> list[str]:
    normalized = []
    seen = set()

    for value in values or []:
        item = str(value or "").strip()

        if not item:
            continue

        key = item.casefold()

        if key not in seen:
            seen.add(key)
            normalized.append(item)

    return normalized


def _as_utc(value: datetime | str, field: str) -> datetime:
    try:
        parsed = (
            value
            if isinstance(value, datetime)
            else datetime.fromisoformat(
                str(value).replace("Z", "+00:00")
            )
        )
    except (TypeError, ValueError) as exc:
        raise PortalNotificationValidationError(
            field,
            f"{field.replace('_', ' ').title()} is invalid.",
        ) from exc

    if parsed.tzinfo is None:
        raise PortalNotificationValidationError(
            field,
            f"{field.replace('_', ' ').title()} must include a timezone.",
        )

    return parsed.astimezone(timezone.utc)


def normalize_action_path(value: object) -> str:
    path = _required_text(value, "action_path")

    if path.startswith("//"):
        raise PortalNotificationValidationError(
            "action_path",
            "Action path must remain inside CAIWAVE.",
        )

    if not path.startswith(("/", "#")):
        raise PortalNotificationValidationError(
            "action_path",
            "Action path must be a CAIWAVE path or page section.",
        )

    if any(character in path for character in ("\r", "\n", "\\")):
        raise PortalNotificationValidationError(
            "action_path",
            "Action path contains unsupported characters.",
        )

    return path


def build_portal_notification_payload(
    *,
    title: object,
    message: object,
    source_type: object,
    action_label: object,
    action_path: object,
    coverage_scope: object = "national",
    country_code: object = "KE",
    target_counties: Iterable[object] | None = None,
    target_constituencies: Iterable[object] | None = None,
    target_hotspot_ids: Iterable[object] | None = None,
    source_id: object = None,
    image_url: object = None,
    starts_at: datetime | str,
    expires_at: datetime | str,
    is_active: bool = True,
    priority: int = 0,
    notification_id: object = None,
    created_by: object = None,
    now: datetime | None = None,
) -> dict[str, object]:
    normalized_source_type = str(source_type or "").strip().lower()

    if normalized_source_type not in SOURCE_TYPES:
        raise PortalNotificationValidationError(
            "source_type",
            "Unsupported notification source type.",
        )

    normalized_scope = str(coverage_scope or "").strip().lower()

    if normalized_scope not in COVERAGE_SCOPES:
        raise PortalNotificationValidationError(
            "coverage_scope",
            "Unsupported notification coverage scope.",
        )

    normalized_counties = _normalize_values(target_counties)
    normalized_constituencies = _normalize_values(
        target_constituencies
    )
    normalized_hotspots = _normalize_values(target_hotspot_ids)

    if normalized_scope == "county" and not normalized_counties:
        raise PortalNotificationValidationError(
            "target_counties",
            "Choose at least one target county.",
        )

    if (
        normalized_scope == "constituency"
        and not normalized_constituencies
    ):
        raise PortalNotificationValidationError(
            "target_constituencies",
            "Choose at least one target constituency.",
        )

    if (
        normalized_scope == "specific_hotspots"
        and not normalized_hotspots
    ):
        raise PortalNotificationValidationError(
            "target_hotspot_ids",
            "Choose at least one target hotspot.",
        )

    if normalized_scope == "national":
        normalized_counties = []
        normalized_constituencies = []
        normalized_hotspots = []

    normalized_starts_at = _as_utc(starts_at, "starts_at")
    normalized_expires_at = _as_utc(expires_at, "expires_at")

    if normalized_expires_at <= normalized_starts_at:
        raise PortalNotificationValidationError(
            "expires_at",
            "Expiry must be later than the start time.",
        )

    try:
        normalized_priority = int(priority)
    except (TypeError, ValueError) as exc:
        raise PortalNotificationValidationError(
            "priority",
            "Priority must be a whole number.",
        ) from exc

    if not 0 <= normalized_priority <= 100:
        raise PortalNotificationValidationError(
            "priority",
            "Priority must be between 0 and 100.",
        )

    current_time = now or datetime.now(timezone.utc)

    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)

    current_time = current_time.astimezone(timezone.utc)
    timestamp = current_time.isoformat()

    return {
        "id": str(notification_id or uuid4()),
        "title": _required_text(title, "title"),
        "message": _required_text(message, "message"),
        "source_type": normalized_source_type,
        "source_id": _optional_text(source_id),
        "action_label": _required_text(
            action_label,
            "action_label",
        ),
        "action_path": normalize_action_path(action_path),
        "image_url": _optional_text(image_url),
        "coverage_scope": normalized_scope,
        "country_code": str(country_code or "KE").strip().upper(),
        "target_counties": normalized_counties,
        "target_constituencies": normalized_constituencies,
        "target_hotspot_ids": normalized_hotspots,
        "starts_at": normalized_starts_at.isoformat(),
        "expires_at": normalized_expires_at.isoformat(),
        "is_active": bool(is_active),
        "priority": normalized_priority,
        "created_by": _optional_text(created_by),
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def notification_targets_hotspot(
    notification: dict[str, object],
    hotspot: dict[str, object],
    *,
    now: datetime | None = None,
) -> bool:
    if not notification.get("is_active", False):
        return False

    current_time = now or datetime.now(timezone.utc)

    try:
        starts_at = _as_utc(
            notification.get("starts_at"),
            "starts_at",
        )
        expires_at = _as_utc(
            notification.get("expires_at"),
            "expires_at",
        )
    except PortalNotificationValidationError:
        return False

    if not starts_at <= current_time.astimezone(timezone.utc) < expires_at:
        return False

    scope = notification.get("coverage_scope", "national")

    if scope == "national":
        return (
            str(notification.get("country_code") or "KE").upper()
            == str(hotspot.get("country_code") or "KE").upper()
        )

    if scope == "county":
        targets = {
            str(value).casefold()
            for value in notification.get("target_counties", [])
        }
        return str(hotspot.get("county") or "").casefold() in targets

    if scope == "constituency":
        targets = {
            str(value).casefold()
            for value in notification.get(
                "target_constituencies",
                [],
            )
        }
        return (
            str(hotspot.get("constituency") or "").casefold()
            in targets
        )

    if scope == "specific_hotspots":
        return str(hotspot.get("id") or "") in {
            str(value)
            for value in notification.get(
                "target_hotspot_ids",
                [],
            )
        }

    return False


def select_portal_notification(
    notifications: Iterable[dict[str, object]],
    hotspot: dict[str, object],
    *,
    now: datetime | None = None,
) -> dict[str, object] | None:
    eligible = [
        notification
        for notification in notifications
        if notification_targets_hotspot(
            notification,
            hotspot,
            now=now,
        )
    ]

    if not eligible:
        return None

    return max(
        eligible,
        key=lambda item: (
            int(item.get("priority") or 0),
            str(item.get("starts_at") or ""),
        ),
    )


def build_public_notification(
    notification: dict[str, object],
) -> dict[str, object]:
    public_fields = (
        "id",
        "title",
        "message",
        "source_type",
        "source_id",
        "action_label",
        "action_path",
        "image_url",
        "starts_at",
        "expires_at",
        "priority",
    )

    return {
        field: notification.get(field)
        for field in public_fields
    }
