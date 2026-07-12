from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from .contracts import CampaignCoverageScope


@dataclass(frozen=True)
class CampaignTargetingValidationError(ValueError):
    field: str
    message: str

    def __str__(self) -> str:
        return self.message


def _clean(value: object) -> str:
    return str(value or "").strip()


def _clean_unique(values: Iterable[object] | None) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for value in values or []:
        cleaned = _clean(value)

        if not cleaned or cleaned in seen:
            continue

        seen.add(cleaned)
        result.append(cleaned)

    return result


def normalize_campaign_targeting(
    *,
    coverage_scope: object,
    country_code: object = "KE",
    country_name: object = "Kenya",
    counties: Iterable[object] | None = None,
    constituencies: Iterable[object] | None = None,
    hotspot_ids: Iterable[object] | None = None,
    assigned_ad_ids: Iterable[object] | None = None,
) -> dict[str, object]:
    scope = _clean(coverage_scope).lower()

    return {
        "coverage_scope": scope,
        "country_code": _clean(country_code).upper() or "KE",
        "country_name": _clean(country_name) or "Kenya",
        "counties": _clean_unique(counties),
        "constituencies": _clean_unique(constituencies),
        "hotspot_ids": _clean_unique(hotspot_ids),
        "assigned_ad_ids": _clean_unique(assigned_ad_ids),
    }


def validate_campaign_targeting(
    *,
    coverage_scope: object,
    country_code: object = "KE",
    country_name: object = "Kenya",
    counties: Iterable[object] | None = None,
    constituencies: Iterable[object] | None = None,
    hotspot_ids: Iterable[object] | None = None,
    assigned_ad_ids: Iterable[object] | None = None,
    locations_by_county: Mapping[str, Sequence[str]],
    known_hotspot_ids: Iterable[object] | None = None,
) -> dict[str, object]:
    targeting = normalize_campaign_targeting(
        coverage_scope=coverage_scope,
        country_code=country_code,
        country_name=country_name,
        counties=counties,
        constituencies=constituencies,
        hotspot_ids=hotspot_ids,
        assigned_ad_ids=assigned_ad_ids,
    )

    try:
        scope = CampaignCoverageScope(targeting["coverage_scope"])
    except ValueError as exc:
        raise CampaignTargetingValidationError(
            "coverage_scope",
            "Coverage scope must be national, county, constituency or hotspot.",
        ) from exc

    if targeting["country_code"] != "KE":
        raise CampaignTargetingValidationError(
            "country_code",
            "Campaign Targeting v2 currently supports Kenya only.",
        )

    if str(targeting["country_name"]).casefold() != "kenya":
        raise CampaignTargetingValidationError(
            "country_name",
            "Country name must be Kenya for country code KE.",
        )

    if not targeting["assigned_ad_ids"]:
        raise CampaignTargetingValidationError(
            "assigned_ad_ids",
            "At least one eligible advertisement must be assigned.",
        )

    selected_counties = targeting["counties"]
    selected_constituencies = targeting["constituencies"]
    selected_hotspots = targeting["hotspot_ids"]

    if scope is CampaignCoverageScope.NATIONAL:
        if selected_counties or selected_constituencies or selected_hotspots:
            raise CampaignTargetingValidationError(
                "coverage_scope",
                "National campaigns cannot include regional or hotspot targets.",
            )

    elif scope is CampaignCoverageScope.COUNTY:
        if not selected_counties:
            raise CampaignTargetingValidationError(
                "counties",
                "Select at least one county.",
            )

        unknown_counties = [
            county
            for county in selected_counties
            if county not in locations_by_county
        ]

        if unknown_counties:
            raise CampaignTargetingValidationError(
                "counties",
                "One or more selected counties are not supported.",
            )

        if selected_constituencies or selected_hotspots:
            raise CampaignTargetingValidationError(
                "coverage_scope",
                "County campaigns cannot include constituency or hotspot targets.",
            )

    elif scope is CampaignCoverageScope.CONSTITUENCY:
        if not selected_constituencies:
            raise CampaignTargetingValidationError(
                "constituencies",
                "Select at least one constituency.",
            )

        all_constituencies = {
            constituency
            for values in locations_by_county.values()
            for constituency in values
        }

        unknown_constituencies = [
            constituency
            for constituency in selected_constituencies
            if constituency not in all_constituencies
        ]

        if unknown_constituencies:
            raise CampaignTargetingValidationError(
                "constituencies",
                "One or more selected constituencies are not supported.",
            )

        if selected_counties or selected_hotspots:
            raise CampaignTargetingValidationError(
                "coverage_scope",
                "Constituency campaigns cannot include county or hotspot targets.",
            )

    elif scope is CampaignCoverageScope.HOTSPOT:
        if not selected_hotspots:
            raise CampaignTargetingValidationError(
                "hotspot_ids",
                "Select at least one hotspot.",
            )

        known_ids = set(_clean_unique(known_hotspot_ids))

        if known_ids:
            unknown_hotspots = [
                hotspot_id
                for hotspot_id in selected_hotspots
                if hotspot_id not in known_ids
            ]

            if unknown_hotspots:
                raise CampaignTargetingValidationError(
                    "hotspot_ids",
                    "One or more selected hotspots do not exist.",
                )

        if selected_counties or selected_constituencies:
            raise CampaignTargetingValidationError(
                "coverage_scope",
                "Hotspot campaigns cannot include county or constituency targets.",
            )

    targeting["coverage_scope"] = scope.value
    return targeting
