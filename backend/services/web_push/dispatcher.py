from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import datetime, timezone
from typing import Callable
from zoneinfo import ZoneInfo

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from backend.services.portal_notifications import (
    notification_targets_hotspot,
)

from .sender import (
    WebPushConfiguration,
    load_web_push_configuration,
    send_web_push_notification,
)
from .service import evaluate_web_push_delivery


logger = logging.getLogger(__name__)

NAIROBI_TIMEZONE = ZoneInfo("Africa/Nairobi")
WEB_PUSH_POLL_SECONDS = 60
WEB_PUSH_MAX_ATTEMPTS = 3
WEB_PUSH_NOTIFICATION_LIMIT = 200
WEB_PUSH_SUBSCRIPTION_LIMIT = 5000


def delivery_claim_id(
    notification_id: object,
    subscription_id: object,
) -> str:
    notification = str(notification_id or "").strip()
    subscription = str(subscription_id or "").strip()

    if not notification or not subscription:
        raise ValueError(
            "Notification and subscription IDs are required."
        )

    value = f"{notification}\0{subscription}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def nairobi_delivery_day_start(
    now: datetime,
) -> datetime:
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    local_now = now.astimezone(NAIROBI_TIMEZONE)
    local_start = local_now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    return local_start.astimezone(timezone.utc)


async def _claim_delivery(
    db,
    *,
    claim_id: str,
    notification: dict,
    subscription: dict,
    now: datetime,
) -> dict | None:
    timestamp = now.isoformat()

    try:
        return await db.web_push_deliveries.find_one_and_update(
            {
                "id": claim_id,
                "$or": [
                    {"status": {"$exists": False}},
                    {
                        "status": "failed",
                        "attempt_count": {
                            "$lt": WEB_PUSH_MAX_ATTEMPTS
                        },
                    },
                ],
            },
            {
                "$setOnInsert": {
                    "id": claim_id,
                    "notification_id": notification["id"],
                    "subscription_id": subscription["id"],
                    "hotspot_id": subscription["hotspot_id"],
                    "source_type": notification.get(
                        "source_type"
                    ),
                    "created_at": timestamp,
                },
                "$set": {
                    "status": "sending",
                    "last_attempt_at": timestamp,
                    "updated_at": timestamp,
                    "error": None,
                },
                "$inc": {"attempt_count": 1},
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
    except DuplicateKeyError:
        return None


async def dispatch_pending_web_pushes(
    db,
    *,
    now: datetime | None = None,
    configuration: WebPushConfiguration | None = None,
    sender: Callable = send_web_push_notification,
) -> dict[str, int]:
    current_time = now or datetime.now(timezone.utc)

    if current_time.tzinfo is None:
        current_time = current_time.replace(
            tzinfo=timezone.utc
        )

    current_time = current_time.astimezone(timezone.utc)
    now_iso = current_time.isoformat()

    summary = {
        "notifications": 0,
        "subscriptions": 0,
        "eligible": 0,
        "delivered": 0,
        "failed": 0,
        "stale": 0,
    }

    push_configuration = (
        configuration or load_web_push_configuration()
    )

    if not push_configuration.enabled:
        return summary

    notifications = await db.portal_notifications.find(
        {
            "is_active": True,
            "starts_at": {"$lte": now_iso},
            "expires_at": {"$gt": now_iso},
        },
        {"_id": 0},
    ).sort(
        [
            ("priority", -1),
            ("starts_at", -1),
        ]
    ).to_list(WEB_PUSH_NOTIFICATION_LIMIT)

    subscriptions = await db.web_push_subscriptions.find(
        {"is_active": True},
        {"_id": 0},
    ).to_list(WEB_PUSH_SUBSCRIPTION_LIMIT)

    summary["notifications"] = len(notifications)
    summary["subscriptions"] = len(subscriptions)

    hotspot_cache: dict[str, dict | None] = {}
    daily_counts: dict[str, int] = {}
    day_start = nairobi_delivery_day_start(
        current_time
    ).isoformat()

    for notification in notifications:
        notification_id = str(
            notification.get("id") or ""
        ).strip()

        if not notification_id:
            continue

        for subscription in subscriptions:
            subscription_id = str(
                subscription.get("id") or ""
            ).strip()
            hotspot_id = str(
                subscription.get("hotspot_id") or ""
            ).strip()

            if not subscription_id or not hotspot_id:
                continue

            if hotspot_id not in hotspot_cache:
                hotspot_cache[hotspot_id] = (
                    await db.hotspots.find_one(
                        {"id": hotspot_id},
                        {"_id": 0},
                    )
                )

            hotspot = hotspot_cache[hotspot_id]

            if not hotspot:
                continue

            if not notification_targets_hotspot(
                notification,
                hotspot,
                now=current_time,
            ):
                continue

            claim_id = delivery_claim_id(
                notification_id,
                subscription_id,
            )

            existing = (
                await db.web_push_deliveries.find_one(
                    {"id": claim_id},
                    {
                        "_id": 0,
                        "status": 1,
                    },
                )
            )

            already_delivered = bool(
                existing
                and existing.get("status") == "delivered"
            )

            if subscription_id not in daily_counts:
                daily_counts[subscription_id] = (
                    await db.web_push_deliveries.count_documents(
                        {
                            "subscription_id": subscription_id,
                            "status": "delivered",
                            "delivered_at": {
                                "$gte": day_start
                            },
                        }
                    )
                )

            allowed, _reason = evaluate_web_push_delivery(
                subscription,
                notification,
                already_delivered=already_delivered,
                deliveries_today=(
                    daily_counts[subscription_id]
                ),
                now=current_time,
            )

            if not allowed:
                continue

            claim = await _claim_delivery(
                db,
                claim_id=claim_id,
                notification=notification,
                subscription=subscription,
                now=current_time,
            )

            if not claim:
                continue

            summary["eligible"] += 1

            result = await asyncio.to_thread(
                sender,
                subscription=subscription,
                notification=notification,
                hotspot_id=hotspot_id,
                configuration=push_configuration,
            )

            completed_at = datetime.now(
                timezone.utc
            ).isoformat()

            if result.delivered:
                summary["delivered"] += 1
                daily_counts[subscription_id] += 1
                delivery_status = "delivered"
                delivered_at = completed_at
            elif result.stale_subscription:
                summary["stale"] += 1
                delivery_status = "stale"
                delivered_at = None

                await db.web_push_subscriptions.update_one(
                    {"id": subscription_id},
                    {
                        "$set": {
                            "is_active": False,
                            "disabled_reason": (
                                "push_subscription_expired"
                            ),
                            "updated_at": completed_at,
                        }
                    },
                )
            else:
                summary["failed"] += 1
                delivery_status = "failed"
                delivered_at = None

            await db.web_push_deliveries.update_one(
                {"id": claim_id},
                {
                    "$set": {
                        "status": delivery_status,
                        "status_code": result.status_code,
                        "error": result.error,
                        "delivered_at": delivered_at,
                        "completed_at": completed_at,
                        "updated_at": completed_at,
                    }
                },
            )

    return summary


async def monitor_web_push_delivery(
    db,
    *,
    poll_seconds: int = WEB_PUSH_POLL_SECONDS,
) -> None:
    logger.info("Web Push delivery monitor started")

    while True:
        try:
            summary = await dispatch_pending_web_pushes(
                db
            )

            if (
                summary["delivered"]
                or summary["failed"]
                or summary["stale"]
            ):
                logger.info(
                    "Web Push delivery cycle: "
                    "delivered=%s failed=%s stale=%s",
                    summary["delivered"],
                    summary["failed"],
                    summary["stale"],
                )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "Web Push delivery cycle failed safely"
            )

        await asyncio.sleep(max(30, poll_seconds))
