from backend.server import HotspotLocationUpdate


def test_hotspot_location_update_defaults_to_kenya():
    update = HotspotLocationUpdate(
        county="Mombasa",
        constituency="Mvita",
        location_name="Tononoka Grounds",
    )

    assert update.country_code == "KE"
    assert update.country_name == "Kenya"


def test_hotspot_location_update_preserves_optional_coordinates():
    update = HotspotLocationUpdate(
        country_code="KE",
        country_name="Kenya",
        county="Mombasa",
        constituency="Nyali",
        ward="Frere Town",
        location_name="Nyali Centre",
        latitude=-4.0435,
        longitude=39.6682,
    )

    assert update.ward == "Frere Town"
    assert update.latitude == -4.0435
    assert update.longitude == 39.6682
