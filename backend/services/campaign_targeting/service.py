from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Mapping, Sequence

from .validator import (
    CampaignTargetingValidationError,
    validate_campaign_targeting,
)


@dataclass(frozen=True)
class CampaignValidationError(ValueError):
    field: str
    message: str

    def __str__(self) -> str:
        return self.message


def _as_utc_datetime(value: object, *, field: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        cleaned = value.strip()

        if not cleaned:
            raise CampaignValidationError(
                field,
                f"{field.replace('_', ' ').title()} is required.",
            )

        try:
            parsed = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
        except ValueError as exc:
            raise CampaignValidationError(
                field,
                f"{field.replace('_', ' ').title()} must be a valid date.",
            ) from exc
    else:
        raise CampaignValidationError(
            field,
            f"{field.replace('_', ' ').title()} must be a valid date.",
        )

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def validate_campaign_dates(
    *,
    start_date: object,
    end_date: object,
) -> tuple[datetime, datetime]:
    normalized_start = _as_utc_datetime(
        start_date,
        field="start_date",
    )
    normalized_end = _as_utc_datetime(
        end_date,
        field="end_date",
    )

    if normalized_end <= normalized_start:
        raise CampaignValidationError(
            "end_date",
            "Campaign end date must be later than the start date.",
        )

    return normalized_start, normalized_end


def is_ad_eligible_for_campaign(
    ad: Mapping[str, object],
    *,
    now: datetime | None = None,
) -> bool:
    current_time = now or datetime.now(timezone.utc)

    if ad.get("status") != "active":
        return False

    if ad.get("is_active") is not True:
        return False

    if not ad.get("approved_at"):
        return False

    if not ad.get("paid_at"):
        return False

    expires_at = ad.get("expires_at")

    if not expires_at:
        return False

    try:
        normalized_expiry = _as_utc_datetime(
            expires_at,
            field="expires_at",
        )
    except CampaignValidationError:
        return False

    return normalized_expiry > current_time


def validate_campaign_ads(
    *,
    assigned_ad_ids: Iterable[object] | None,
    ads_by_id: Mapping[str, Mapping[str, object]],
    now: datetime | None = None,
) -> list[str]:
    normalized_ids: list[str] = []
    seen: set[str] = set()

    for raw_id in assigned_ad_ids or []:
        ad_id = str(raw_id or "").strip()

        if not ad_id or ad_id in seen:
            continue

        seen.add(ad_id)
        normalized_ids.append(ad_id)

    if not normalized_ids:
        raise CampaignValidationError(
            "assigned_ad_ids",
            "At least one eligible advertisement must be assigned.",
        )

    missing_ids = [
        ad_id
        for ad_id in normalized_ids
        if ad_id not in ads_by_id
    ]

    if missing_ids:
        raise CampaignValidationError(
            "assigned_ad_ids",
            "One or more assigned advertisements do not exist.",
        )

    ineligible_ids = [
        ad_id
        for ad_id in normalized_ids
        if not is_ad_eligible_for_campaign(
            ads_by_id[ad_id],
            now=now,
        )
    ]

    if ineligible_ids:
        raise CampaignValidationError(
            "assigned_ad_ids",
            (
                "One or more assigned advertisements are unpaid, "
                "inactive, unapproved or expired."
            ),
        )

    return normalized_ids


def build_campaign_write_payload(
    *,
    name: object,
    description: object,
    start_date: object,
    end_date: object,
    coverage_scope: object,
    country_code: object = "KE",
    country_name: object = "Kenya",
    target_counties: Iterable[object] | None = None,
    target_constituencies: Iterable[object] | None = None,
    target_hotspot_ids: Iterable[object] | None = None,
    assigned_ad_ids: Iterable[object] | None = None,
    locations_by_county: Mapping[str, Sequence[str]],
    known_hotspot_ids: Iterable[object] | None,
    ads_by_id: Mapping[str, Mapping[str, object]],
    now: datetime | None = None,
    stream_id: object = None,
    subsidized_uptime_id: object = None,
    image_url: object = None,
) -> dict[str, object]:
    campaign_name = str(name or "").strip()

    if not campaign_name:
        raise CampaignValidationError(
            "name",
            "Campaign name is required.",
        )

    normalized_start, normalized_end = validate_campaign_dates(
        start_date=start_date,
        end_date=end_date,
    )

    try:
        targeting = validate_campaign_targeting(
            coverage_scope=coverage_scope,
            country_code=country_code,
            country_name=country_name,
            counties=target_counties,
            constituencies=target_constituencies,
            hotspot_ids=target_hotspot_ids,
            assigned_ad_ids=assigned_ad_ids,
            locations_by_county=locations_by_county,
            known_hotspot_ids=known_hotspot_ids,
        )
    except CampaignTargetingValidationError as exc:
        raise CampaignValidationError(
            exc.field,
            exc.message,
        ) from exc

    eligible_ad_ids = validate_campaign_ads(
        assigned_ad_ids=targeting["assigned_ad_ids"],
        ads_by_id=ads_by_id,
        now=now,
    )

    return {
        "name": campaign_name,
        "description": str(description or "").strip() or None,
        "start_date": normalized_start,
        "end_date": normalized_end,
        "coverage_scope": targeting["coverage_scope"],
        "country_code": targeting["country_code"],
        "country_name": targeting["country_name"],
        "target_counties": targeting["counties"],
        "target_constituencies": targeting["constituencies"],
        "target_hotspot_ids": targeting["hotspot_ids"],
        "assigned_ad_ids": eligible_ad_ids,
        # Preserve the legacy field as an empty compatibility field.
        "target_regions": [],
        "stream_id": str(stream_id or "").strip() or None,
        "subsidized_uptime_id":
            str(subsidized_uptime_id or "").strip() or None,
        "image_url": str(image_url or "").strip() or None,
    }
