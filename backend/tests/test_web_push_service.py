import base64
from datetime import datetime, timezone

import pytest

from backend.services.web_push import (
    WebPushValidationError,
    build_web_push_click_url,
    build_web_push_subscription_payload,
    evaluate_web_push_delivery,
    normalize_push_endpoint,
    normalize_push_preferences,
)


NOW = datetime(2026, 7, 23, 12, 0, tzinfo=timezone.utc)
P256DH = base64.urlsafe_b64encode(
    bytes([4]) + (b"a" * 64)
).decode().rstrip("=")
AUTH = base64.urlsafe_b64encode(
    b"b" * 16
).decode().rstrip("=")


def build_subscription(**overrides):
    values = {
        "endpoint": "https://push.example.com/subscription/one",
        "p256dh": P256DH,
        "auth": AUTH,
        "hotspot_id": "hotspot-1",
        "now": NOW,
    }
    values.update(overrides)
    return build_web_push_subscription_payload(**values)


def test_builds_secure_subscription_payload():
    result = build_subscription()

    assert result["hotspot_id"] == "hotspot-1"
    assert result["is_active"] is True
    assert len(result["endpoint_hash"]) == 64
    assert result["preferences"]["campaign"] is True
    assert result["preferences"]["marketplace"] is False


def test_requires_https_endpoint():
    with pytest.raises(WebPushValidationError) as exc:
        normalize_push_endpoint(
            "http://push.example.com/subscription"
        )

    assert exc.value.field == "endpoint"


def test_rejects_endpoint_credentials():
    with pytest.raises(WebPushValidationError):
        normalize_push_endpoint(
            "https://user:password@push.example.com/one"
        )


def test_requires_valid_p256dh_key():
    with pytest.raises(WebPushValidationError) as exc:
        build_subscription(p256dh=AUTH)

    assert exc.value.field == "p256dh"


def test_requires_auth_secret_of_at_least_sixteen_bytes():
    short_auth = base64.urlsafe_b64encode(
        b"short"
    ).decode().rstrip("=")

    with pytest.raises(WebPushValidationError) as exc:
        build_subscription(auth=short_auth)

    assert exc.value.field == "auth"


def test_preferences_are_boolean_and_known():
    assert normalize_push_preferences(
        {"marketplace": True}
    )["marketplace"] is True

    with pytest.raises(WebPushValidationError):
        normalize_push_preferences({"unknown": True})

    with pytest.raises(WebPushValidationError):
        normalize_push_preferences({"campaign": "yes"})


def test_prevents_duplicate_delivery():
    allowed, reason = evaluate_web_push_delivery(
        build_subscription(),
        {"source_type": "campaign"},
        already_delivered=True,
        now=NOW,
    )

    assert not allowed
    assert reason == "already_delivered"


def test_enforces_two_pushes_per_day():
    allowed, reason = evaluate_web_push_delivery(
        build_subscription(),
        {"source_type": "campaign"},
        deliveries_today=2,
        now=NOW,
    )

    assert not allowed
    assert reason == "daily_limit"


def test_respects_disabled_preference():
    subscription = build_subscription(
        preferences={"marketplace": False}
    )
    allowed, reason = evaluate_web_push_delivery(
        subscription,
        {"source_type": "marketplace"},
        now=NOW,
    )

    assert not allowed
    assert reason == "preference_disabled"


def test_campaign_is_suppressed_during_quiet_hours():
    quiet_time = datetime(
        2026,
        7,
        23,
        20,
        30,
        tzinfo=timezone.utc,
    )
    allowed, reason = evaluate_web_push_delivery(
        build_subscription(),
        {"source_type": "campaign"},
        now=quiet_time,
    )

    assert not allowed
    assert reason == "quiet_hours"


def test_live_stream_can_bypass_quiet_hours():
    quiet_time = datetime(
        2026,
        7,
        23,
        20,
        30,
        tzinfo=timezone.utc,
    )
    allowed, reason = evaluate_web_push_delivery(
        build_subscription(),
        {"source_type": "live_stream"},
        now=quiet_time,
    )

    assert allowed
    assert reason == "eligible"


def test_internal_section_builds_hotspot_click_url():
    url = build_web_push_click_url(
        {"action_path": "#campaign"},
        "hotspot/one",
    )

    assert url == (
        "https://www.caiwave.com/portal/"
        "hotspot%2Fone#campaign"
    )


def test_external_action_falls_back_to_portal():
    url = build_web_push_click_url(
        {"action_path": "https://example.com"},
        "hotspot-1",
    )

    assert url == (
        "https://www.caiwave.com/portal/hotspot-1"
    )
