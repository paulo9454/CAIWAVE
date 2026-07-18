from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Mapping


def _clean(value: object) -> str:
    if isinstance(value, Enum):
        value = value.value

    return str(value or "").strip()


def _as_utc_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    else:
        raw = _clean(value)

        if not raw:
            return None

        try:
            parsed = datetime.fromisoformat(
                raw.replace("Z", "+00:00")
            )
        except (TypeError, ValueError):
            return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def is_campaign_eligible_for_hotspot(
    campaign: Mapping[str, object],
    hotspot: Mapping[str, object],
    *,
    now: datetime | None = None,
) -> bool:
    current_time = now or datetime.now(timezone.utc)

    if _clean(campaign.get("status")).lower() != "active":
        return False

    start_date = _as_utc_datetime(campaign.get("start_date"))
    end_date = _as_utc_datetime(campaign.get("end_date"))

    if not start_date or not end_date:
        return False

    if not start_date <= current_time <= end_date:
        return False

    campaign_country = (
        _clean(campaign.get("country_code")).upper() or "KE"
    )
    hotspot_country = (
        _clean(hotspot.get("country_code")).upper() or "KE"
    )

    if campaign_country != "KE" or hotspot_country != "KE":
        return False

    scope = _clean(campaign.get("coverage_scope")).lower()

    if scope == "national":
        return True

    if scope == "county":
        hotspot_county = _clean(hotspot.get("county")).casefold()
        selected_counties = {
            _clean(value).casefold()
            for value in campaign.get("target_counties", []) or []
            if _clean(value)
        }

        return bool(
            hotspot_county and hotspot_county in selected_counties
        )

    if scope == "constituency":
        hotspot_constituency = _clean(
            hotspot.get("constituency")
        ).casefold()
        selected_constituencies = {
            _clean(value).casefold()
            for value in (
                campaign.get("target_constituencies", []) or []
            )
            if _clean(value)
        }

        return bool(
            hotspot_constituency
            and hotspot_constituency in selected_constituencies
        )

    if scope == "hotspot":
        hotspot_id = _clean(hotspot.get("id"))
        selected_hotspot_ids = {
            _clean(value)
            for value in (
                campaign.get("target_hotspot_ids", []) or []
            )
            if _clean(value)
        }

        return bool(
            hotspot_id and hotspot_id in selected_hotspot_ids
        )

    return False
