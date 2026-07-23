from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping
from urllib.parse import urlparse

from pywebpush import WebPushException, webpush

from .service import build_web_push_click_url


DEFAULT_PUSH_TTL_SECONDS = 60 * 60
DEFAULT_PUSH_TIMEOUT_SECONDS = 10


@dataclass(frozen=True)
class WebPushConfiguration:
    enabled: bool
    public_key: str | None
    private_key_path: str | None
    subject: str | None
    error: str | None = None


@dataclass(frozen=True)
class WebPushDeliveryResult:
    delivered: bool
    stale_subscription: bool
    status_code: int | None
    error: str | None = None


def load_web_push_configuration(
    environ: Mapping[str, str] | None = None,
) -> WebPushConfiguration:
    values = (
        os.environ
        if environ is None
        else environ
    )
    public_key = str(
        values.get("WEB_PUSH_VAPID_PUBLIC_KEY") or ""
    ).strip()
    private_key_path = str(
        values.get("WEB_PUSH_VAPID_PRIVATE_KEY") or ""
    ).strip()
    subject = str(
        values.get("WEB_PUSH_VAPID_SUBJECT") or ""
    ).strip()

    if not public_key or not private_key_path or not subject:
        return WebPushConfiguration(
            enabled=False,
            public_key=public_key or None,
            private_key_path=private_key_path or None,
            subject=subject or None,
            error="Web Push configuration is incomplete.",
        )

    parsed_subject = urlparse(subject)

    if parsed_subject.scheme not in {"mailto", "https"}:
        return WebPushConfiguration(
            enabled=False,
            public_key=public_key,
            private_key_path=private_key_path,
            subject=subject,
            error="VAPID subject must be mailto or HTTPS.",
        )

    if not Path(private_key_path).is_file():
        return WebPushConfiguration(
            enabled=False,
            public_key=public_key,
            private_key_path=private_key_path,
            subject=subject,
            error="VAPID private key file is unavailable.",
        )

    return WebPushConfiguration(
        enabled=True,
        public_key=public_key,
        private_key_path=private_key_path,
        subject=subject,
    )


def _absolute_media_url(value: object) -> str | None:
    media_url = str(value or "").strip()

    if not media_url:
        return None

    if media_url.startswith("https://"):
        return media_url

    if media_url.startswith("/") and not media_url.startswith("//"):
        return f"https://www.caiwave.com{media_url}"

    return None


def build_web_push_message(
    notification: Mapping[str, object],
    hotspot_id: object,
) -> dict[str, object]:
    return {
        "title": str(
            notification.get("title")
            or "CAIWAVE update"
        ),
        "body": str(
            notification.get("message")
            or "Open CAIWAVE to view this update."
        ),
        "icon": "https://www.caiwave.com/logo-192.svg",
        "badge": "https://www.caiwave.com/logo-192.svg",
        "image": _absolute_media_url(
            notification.get("image_url")
        ),
        "tag": (
            f"caiwave:{notification.get('id')}"
            if notification.get("id")
            else "caiwave:update"
        ),
        "renotify": False,
        "url": build_web_push_click_url(
            notification,
            hotspot_id,
        ),
        "notification_id": notification.get("id"),
        "source_type": notification.get("source_type"),
    }


def send_web_push_notification(
    *,
    subscription: Mapping[str, object],
    notification: Mapping[str, object],
    hotspot_id: object,
    configuration: WebPushConfiguration,
    sender: Callable = webpush,
) -> WebPushDeliveryResult:
    """Send one notification without leaking delivery failures."""
    if not configuration.enabled:
        return WebPushDeliveryResult(
            delivered=False,
            stale_subscription=False,
            status_code=None,
            error=configuration.error or "Web Push is disabled.",
        )

    endpoint = str(subscription.get("endpoint") or "")
    keys = subscription.get("keys") or {}

    if not endpoint or not isinstance(keys, Mapping):
        return WebPushDeliveryResult(
            delivered=False,
            stale_subscription=True,
            status_code=None,
            error="Stored subscription is incomplete.",
        )

    subscription_info = {
        "endpoint": endpoint,
        "keys": {
            "p256dh": str(keys.get("p256dh") or ""),
            "auth": str(keys.get("auth") or ""),
        },
    }
    message = build_web_push_message(
        notification,
        hotspot_id,
    )

    try:
        response = sender(
            subscription_info=subscription_info,
            data=json.dumps(
                message,
                separators=(",", ":"),
            ),
            vapid_private_key=(
                configuration.private_key_path
            ),
            vapid_claims={
                "sub": configuration.subject,
            },
            timeout=DEFAULT_PUSH_TIMEOUT_SECONDS,
            ttl=DEFAULT_PUSH_TTL_SECONDS,
        )
    except WebPushException as exc:
        status_code = getattr(
            getattr(exc, "response", None),
            "status_code",
            None,
        )

        return WebPushDeliveryResult(
            delivered=False,
            stale_subscription=status_code in {404, 410},
            status_code=status_code,
            error="Push service rejected the notification.",
        )
    except Exception:
        return WebPushDeliveryResult(
            delivered=False,
            stale_subscription=False,
            status_code=None,
            error="Push delivery failed.",
        )

    status_code = getattr(response, "status_code", 201)

    return WebPushDeliveryResult(
        delivered=200 <= int(status_code) <= 202,
        stale_subscription=False,
        status_code=int(status_code),
        error=None,
    )
