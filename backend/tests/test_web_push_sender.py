from pathlib import Path

from pywebpush import WebPushException

from backend.services.web_push import (
    WebPushConfiguration,
    build_web_push_message,
    load_web_push_configuration,
    send_web_push_notification,
)


PRIVATE_KEY = (
    "/opt/caiwave/backend/secrets/webpush/private_key.pem"
)


def enabled_configuration():
    return WebPushConfiguration(
        enabled=True,
        public_key="public-key",
        private_key_path=PRIVATE_KEY,
        subject="https://www.caiwave.com",
    )


def subscription():
    return {
        "endpoint": "https://push.example.com/one",
        "keys": {
            "p256dh": "public-encryption-key",
            "auth": "authentication-secret",
        },
    }


def notification():
    return {
        "id": "notification-1",
        "title": "Campaign update",
        "message": "A new campaign is available.",
        "source_type": "campaign",
        "action_path": "#campaign",
        "image_url": "/api/uploads/campaigns/one.png",
    }


def test_incomplete_configuration_is_disabled():
    result = load_web_push_configuration({})

    assert not result.enabled
    assert result.error


def test_configuration_requires_existing_private_key(tmp_path):
    result = load_web_push_configuration(
        {
            "WEB_PUSH_VAPID_PUBLIC_KEY": "public",
            "WEB_PUSH_VAPID_PRIVATE_KEY": str(
                tmp_path / "missing.pem"
            ),
            "WEB_PUSH_VAPID_SUBJECT": (
                "https://www.caiwave.com"
            ),
        }
    )

    assert not result.enabled
    assert "unavailable" in result.error


def test_complete_configuration_is_enabled(tmp_path):
    private_key = tmp_path / "private.pem"
    private_key.write_text("test-key")

    result = load_web_push_configuration(
        {
            "WEB_PUSH_VAPID_PUBLIC_KEY": "public",
            "WEB_PUSH_VAPID_PRIVATE_KEY": str(private_key),
            "WEB_PUSH_VAPID_SUBJECT": (
                "https://www.caiwave.com"
            ),
        }
    )

    assert result.enabled
    assert result.error is None


def test_builds_internal_click_message():
    result = build_web_push_message(
        notification(),
        "hotspot-1",
    )

    assert result["url"] == (
        "https://www.caiwave.com/portal/"
        "hotspot-1#campaign"
    )
    assert result["renotify"] is False
    assert result["image"].startswith(
        "https://www.caiwave.com/api/"
    )


def test_successful_delivery_returns_result():
    calls = []

    class Response:
        status_code = 201

    def fake_sender(**kwargs):
        calls.append(kwargs)
        return Response()

    result = send_web_push_notification(
        subscription=subscription(),
        notification=notification(),
        hotspot_id="hotspot-1",
        configuration=enabled_configuration(),
        sender=fake_sender,
    )

    assert result.delivered
    assert result.status_code == 201
    assert calls[0]["timeout"] == 10
    assert calls[0]["ttl"] == 3600
    assert "private_key.pem" in calls[0][
        "vapid_private_key"
    ]


def test_expired_subscription_is_marked_stale():
    class Response:
        status_code = 410

    def fake_sender(**kwargs):
        raise WebPushException(
            "Subscription expired",
            response=Response(),
        )

    result = send_web_push_notification(
        subscription=subscription(),
        notification=notification(),
        hotspot_id="hotspot-1",
        configuration=enabled_configuration(),
        sender=fake_sender,
    )

    assert not result.delivered
    assert result.stale_subscription
    assert result.status_code == 410


def test_unexpected_failure_never_escapes():
    def fake_sender(**kwargs):
        raise RuntimeError("network unavailable")

    result = send_web_push_notification(
        subscription=subscription(),
        notification=notification(),
        hotspot_id="hotspot-1",
        configuration=enabled_configuration(),
        sender=fake_sender,
    )

    assert not result.delivered
    assert not result.stale_subscription
    assert result.error == "Push delivery failed."


def test_disabled_configuration_does_not_call_sender():
    called = False

    def fake_sender(**kwargs):
        nonlocal called
        called = True

    result = send_web_push_notification(
        subscription=subscription(),
        notification=notification(),
        hotspot_id="hotspot-1",
        configuration=WebPushConfiguration(
            enabled=False,
            public_key=None,
            private_key_path=None,
            subject=None,
            error="disabled",
        ),
        sender=fake_sender,
    )

    assert not result.delivered
    assert not called
