import pytest

from backend.services.hotspot_location import (
    HotspotLocationValidationError,
    normalize_hotspot_location,
    validate_hotspot_location,
)


LOCATIONS = {
    "Mombasa": ["Changamwe", "Nyali", "Mvita"],
    "Nairobi": ["Westlands", "Langata"],
}


def test_normalize_location_defaults_to_kenya():
    result = normalize_hotspot_location(
        country_code="",
        country_name="",
        county=" Mombasa ",
        constituency=" Nyali ",
        location_name=" Nyali Beach ",
    )

    assert result == {
        "country_code": "KE",
        "country_name": "Kenya",
        "county": "Mombasa",
        "constituency": "Nyali",
        "location_name": "Nyali Beach",
        "ward": None,
    }


def test_validate_valid_kenya_location():
    result = validate_hotspot_location(
        country_code="KE",
        country_name="Kenya",
        county="Mombasa",
        constituency="Mvita",
        location_name="Tononoka Grounds",
        locations_by_county=LOCATIONS,
    )

    assert result["county"] == "Mombasa"
    assert result["constituency"] == "Mvita"


@pytest.mark.parametrize(
    ("field", "kwargs"),
    [
        ("country_code", {"country_code": "UG"}),
        ("country_name", {"country_name": "Uganda"}),
        ("location_name", {"location_name": ""}),
        ("county", {"county": ""}),
        ("county", {"county": "Unknown"}),
        ("constituency", {"constituency": ""}),
        ("constituency", {"county": "Mombasa", "constituency": "Westlands"}),
    ],
)
def test_invalid_location_is_rejected(field, kwargs):
    payload = {
        "country_code": "KE",
        "country_name": "Kenya",
        "county": "Mombasa",
        "constituency": "Nyali",
        "location_name": "Nyali Beach",
        "locations_by_county": LOCATIONS,
    }
    payload.update(kwargs)

    with pytest.raises(HotspotLocationValidationError) as exc:
        validate_hotspot_location(**payload)

    assert exc.value.field == field


def test_optional_ward_is_trimmed():
    result = validate_hotspot_location(
        country_code="KE",
        country_name="Kenya",
        county="Mombasa",
        constituency="Nyali",
        location_name="Beach Hotel",
        ward="  Frere Town  ",
        locations_by_county=LOCATIONS,
    )

    assert result["ward"] == "Frere Town"
