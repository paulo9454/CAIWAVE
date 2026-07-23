from datetime import datetime, timezone

import pytest

from backend.services.web_push.dispatcher import (
    WEB_PUSH_MAX_ATTEMPTS,
    delivery_claim_id,
    nairobi_delivery_day_start,
)


def test_delivery_claim_is_stable_and_unique():
    first = delivery_claim_id(
        "notification-1",
        "subscription-1",
    )
    repeated = delivery_claim_id(
        "notification-1",
        "subscription-1",
    )
    different = delivery_claim_id(
        "notification-1",
        "subscription-2",
    )

    assert first == repeated
    assert first != different
    assert len(first) == 64


def test_delivery_claim_requires_both_ids():
    with pytest.raises(ValueError):
        delivery_claim_id("", "subscription-1")

    with pytest.raises(ValueError):
        delivery_claim_id("notification-1", "")


def test_nairobi_day_start_is_returned_in_utc():
    now = datetime(
        2026,
        7,
        23,
        20,
        30,
        tzinfo=timezone.utc,
    )

    result = nairobi_delivery_day_start(now)

    assert result == datetime(
        2026,
        7,
        22,
        21,
        0,
        tzinfo=timezone.utc,
    )


def test_retry_limit_is_three_attempts():
    assert WEB_PUSH_MAX_ATTEMPTS == 3
