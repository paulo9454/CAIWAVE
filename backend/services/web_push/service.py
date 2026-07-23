from __future__ import annotations

import base64
import binascii
import hashlib
from datetime import datetime, timezone
from typing import Mapping
from urllib.parse import quote, urlparse
from uuid import uuid4
from zoneinfo import ZoneInfo


CAIWAVE_PORTAL_BASE_URL = "https://www.caiwave.com/portal"
MAX_PUSHES_PER_DEVICE_PER_DAY = 2
QUIET_HOURS_START = 21
QUIET_HOURS_END = 8
NAIROBI_TIMEZONE = ZoneInfo("Africa/Nairobi")

PUSH_SOURCE_TYPES = {
    "campaign",
    "live_stream",
    "announcement",
    "marketplace",
}

DEFAULT_PUSH_PREFERENCES = {
    "campaign": True,
    "live_stream": True,
    "announcement": True,
    "marketplace": False,
}


class WebPushValidationError(ValueError):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(message)


def _required_text(value: object, field: str) -> str:
    normalized = str(value or "").strip()

    if not normalized:
        raise WebPushValidationError(
            field,
            f"{field.replace('_', ' ').title()} is required.",
        )

    return normalized


def _optional_text(value: object) -> str | None:
    normalized = str(value or "").strip()
    return normalized or None


def _decode_base64url(value: object, field: str) -> bytes:
    normalized = _required_text(value, field)
    padding = "=" * (-len(normalized) % 4)

    try:
        decoded = base64.urlsafe_b64decode(
            normalized + padding
        )
    except (ValueError, binascii.Error) as exc:
        raise WebPushValidationError(
            field,
            f"{field} is not valid base64url data.",
        ) from exc

    if not decoded:
        raise WebPushValidationError(
            field,
            f"{field} is empty.",
        )

    return decoded


def normalize_push_endpoint(value: object) -> str:
    endpoint = _required_text(value, "endpoint")

    if len(endpoint) > 2048:
        raise WebPushValidationError(
            "endpoint",
            "Push endpoint is too long.",
        )

    parsed = urlparse(endpoint)

    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username
        or parsed.password
    ):
        raise WebPushValidationError(
            "endpoint",
            "Push endpoint must be a secure HTTPS URL.",
        )

    return endpoint


def hash_push_endpoint(value: object) -> str:
    endpoint = normalize_push_endpoint(value)
    return hashlib.sha256(
        endpoint.encode("utf-8")
    ).hexdigest()


def normalize_push_preferences(
    preferences: Mapping[str, object] | None,
) -> dict[str, bool]:
    normalized = dict(DEFAULT_PUSH_PREFERENCES)

    for source_type, enabled in (preferences or {}).items():
        if source_type not in PUSH_SOURCE_TYPES:
            raise WebPushValidationError(
                "preferences",
                "Unsupported push notification preference.",
            )

        if not isinstance(enabled, bool):
            raise WebPushValidationError(
                "preferences",
                "Push preferences must be true or false.",
            )

        normalized[source_type] = enabled

    return normalized


def build_web_push_subscription_payload(
    *,
    endpoint: object,
    p256dh: object,
    auth: object,
    hotspot_id: object,
    preferences: Mapping[str, object] | None = None,
    subscription_id: object = None,
    user_agent: object = None,
    session_id: object = None,
    now: datetime | None = None,
) -> dict[str, object]:
    normalized_endpoint = normalize_push_endpoint(endpoint)
    normalized_p256dh = _required_text(p256dh, "p256dh")
    normalized_auth = _required_text(auth, "auth")

    p256dh_bytes = _decode_base64url(
        normalized_p256dh,
        "p256dh",
    )
    auth_bytes = _decode_base64url(
        normalized_auth,
        "auth",
    )

    if len(p256dh_bytes) != 65 or p256dh_bytes[0] != 4:
        raise WebPushValidationError(
            "p256dh",
            "p256dh must be an uncompressed P-256 public key.",
        )

    if len(auth_bytes) < 16:
        raise WebPushValidationError(
            "auth",
            "auth must contain at least 16 bytes.",
        )

    current_time = now or datetime.now(timezone.utc)

    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)

    timestamp = current_time.astimezone(
        timezone.utc
    ).isoformat()

    return {
        "id": str(subscription_id or uuid4()),
        "endpoint": normalized_endpoint,
        "endpoint_hash": hash_push_endpoint(
            normalized_endpoint
        ),
        "keys": {
            "p256dh": normalized_p256dh,
            "auth": normalized_auth,
        },
        "hotspot_id": _required_text(
            hotspot_id,
            "hotspot_id",
        ),
        "session_id": _optional_text(session_id),
        "user_agent": _optional_text(user_agent),
        "preferences": normalize_push_preferences(
            preferences
        ),
        "is_active": True,
        "muted_until": None,
        "last_seen_at": timestamp,
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def evaluate_web_push_delivery(
    subscription: Mapping[str, object],
    notification: Mapping[str, object],
    *,
    already_delivered: bool = False,
    deliveries_today: int = 0,
    now: datetime | None = None,
) -> tuple[bool, str]:
    if not subscription.get("is_active", False):
        return False, "inactive_subscription"

    if already_delivered:
        return False, "already_delivered"

    if deliveries_today >= MAX_PUSHES_PER_DEVICE_PER_DAY:
        return False, "daily_limit"

    source_type = str(
        notification.get("source_type") or ""
    )

    if source_type not in PUSH_SOURCE_TYPES:
        return False, "unsupported_source"

    preferences = subscription.get(
        "preferences",
        DEFAULT_PUSH_PREFERENCES,
    )

    if not bool(preferences.get(source_type, False)):
        return False, "preference_disabled"

    current_time = now or datetime.now(timezone.utc)

    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)

    muted_until = subscription.get("muted_until")

    if muted_until:
        try:
            muted_time = datetime.fromisoformat(
                str(muted_until).replace("Z", "+00:00")
            )
        except ValueError:
            return False, "invalid_mute"

        if muted_time.astimezone(timezone.utc) > (
            current_time.astimezone(timezone.utc)
        ):
            return False, "muted"

    local_hour = current_time.astimezone(
        NAIROBI_TIMEZONE
    ).hour

    in_quiet_hours = (
        local_hour >= QUIET_HOURS_START
        or local_hour < QUIET_HOURS_END
    )

    if in_quiet_hours and source_type != "live_stream":
        return False, "quiet_hours"

    return True, "eligible"


def build_web_push_click_url(
    notification: Mapping[str, object],
    hotspot_id: object,
) -> str:
    encoded_hotspot_id = quote(
        _required_text(hotspot_id, "hotspot_id"),
        safe="",
    )
    action_path = str(
        notification.get("action_path") or ""
    ).strip()

    portal_url = (
        f"{CAIWAVE_PORTAL_BASE_URL}/"
        f"{encoded_hotspot_id}"
    )

    if action_path.startswith("#"):
        return f"{portal_url}{action_path}"

    if action_path.startswith("/") and not action_path.startswith("//"):
        return f"https://www.caiwave.com{action_path}"

    return portal_url
