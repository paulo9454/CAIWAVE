from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class HotspotLocationValidationError(ValueError):
    field: str
    message: str

    def __str__(self) -> str:
        return self.message


def _clean(value: object) -> str:
    return str(value or "").strip()


def normalize_hotspot_location(
    *,
    country_code: object,
    country_name: object,
    county: object,
    constituency: object,
    location_name: object,
    ward: object = None,
) -> dict[str, str | None]:
    normalized_country_code = _clean(country_code).upper() or "KE"
    normalized_country_name = _clean(country_name) or "Kenya"

    return {
        "country_code": normalized_country_code,
        "country_name": normalized_country_name,
        "county": _clean(county),
        "constituency": _clean(constituency),
        "location_name": _clean(location_name),
        "ward": _clean(ward) or None,
    }


def validate_hotspot_location(
    *,
    country_code: object,
    country_name: object,
    county: object,
    constituency: object,
    location_name: object,
    locations_by_county: Mapping[str, Sequence[str]],
    ward: object = None,
) -> dict[str, str | None]:
    location = normalize_hotspot_location(
        country_code=country_code,
        country_name=country_name,
        county=county,
        constituency=constituency,
        location_name=location_name,
        ward=ward,
    )

    if location["country_code"] != "KE":
        raise HotspotLocationValidationError(
            "country_code",
            "Hotspot Location v1 currently supports Kenya only.",
        )

    if location["country_name"].casefold() != "kenya":
        raise HotspotLocationValidationError(
            "country_name",
            "Country name must be Kenya for country code KE.",
        )

    if not location["location_name"]:
        raise HotspotLocationValidationError(
            "location_name",
            "Location name is required.",
        )

    county_name = location["county"]
    if not county_name:
        raise HotspotLocationValidationError(
            "county",
            "County is required.",
        )

    if county_name not in locations_by_county:
        raise HotspotLocationValidationError(
            "county",
            "Selected county is not supported.",
        )

    constituency_name = location["constituency"]
    if not constituency_name:
        raise HotspotLocationValidationError(
            "constituency",
            "Constituency is required.",
        )

    valid_constituencies = locations_by_county[county_name]
    if constituency_name not in valid_constituencies:
        raise HotspotLocationValidationError(
            "constituency",
            "Selected constituency does not belong to the selected county.",
        )

    return location
