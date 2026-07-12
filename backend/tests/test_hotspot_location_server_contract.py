import pytest

from backend.server import (
    HotspotCreate,
    KENYA_LOCATIONS,
)
from backend.services.hotspot_location import (
    HotspotLocationValidationError,
    validate_hotspot_location,
)


def test_hotspot_create_defaults_country_to_kenya():
    hotspot = HotspotCreate(
        name="Test Hotspot",
        ssid="CAIWAVE_Test",
        location_name="Tononoka Grounds",
        county="Mombasa",
        constituency="Mvita",
    )

    assert hotspot.country_code == "KE"
    assert hotspot.country_name == "Kenya"


def test_hotspot_create_accepts_explicit_kenya_location():
    hotspot = HotspotCreate(
        name="Test Hotspot",
        ssid="CAIWAVE_Test",
        country_code="KE",
        country_name="Kenya",
        location_name="Nyali Centre",
        county="Mombasa",
        constituency="Nyali",
        ward="Frere Town",
    )

    validated = validate_hotspot_location(
        country_code=hotspot.country_code,
        country_name=hotspot.country_name,
        county=hotspot.county,
        constituency=hotspot.constituency,
        location_name=hotspot.location_name,
        ward=hotspot.ward,
        locations_by_county=KENYA_LOCATIONS,
    )

    assert validated == {
        "country_code": "KE",
        "country_name": "Kenya",
        "county": "Mombasa",
        "constituency": "Nyali",
        "location_name": "Nyali Centre",
        "ward": "Frere Town",
    }


@pytest.mark.parametrize(
    ("county", "constituency", "expected_field"),
    [
        (None, None, "county"),
        ("Mombasa", None, "constituency"),
        ("Mombasa", "Westlands", "constituency"),
        ("Unknown County", "Unknown Area", "county"),
    ],
)
def test_hotspot_create_location_validation_rejects_invalid_values(
    county,
    constituency,
    expected_field,
):
    hotspot = HotspotCreate(
        name="Invalid Hotspot",
        ssid="CAIWAVE_Invalid",
        location_name="Invalid Place",
        county=county,
        constituency=constituency,
    )

    with pytest.raises(HotspotLocationValidationError) as exc:
        validate_hotspot_location(
            country_code=hotspot.country_code,
            country_name=hotspot.country_name,
            county=hotspot.county,
            constituency=hotspot.constituency,
            location_name=hotspot.location_name,
            ward=hotspot.ward,
            locations_by_county=KENYA_LOCATIONS,
        )

    assert exc.value.field == expected_field
