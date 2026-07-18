from datetime import datetime, timedelta, timezone

from backend.services.campaign_targeting import (
    is_campaign_eligible_for_hotspot,
)


NOW = datetime(2026, 7, 18, 6, 0, tzinfo=timezone.utc)

HOTSPOT = {
    "id": "hotspot-mtwapa",
    "country_code": "KE",
    "country_name": "Kenya",
    "county": "Kilifi",
    "constituency": "Kilifi North",
}


def campaign(**overrides):
    value = {
        "id": "campaign-1",
        "status": "active",
        "start_date": (NOW - timedelta(hours=1)).isoformat(),
        "end_date": (NOW + timedelta(hours=1)).isoformat(),
        "coverage_scope": "national",
        "country_code": "KE",
        "target_counties": [],
        "target_constituencies": [],
        "target_hotspot_ids": [],
    }
    value.update(overrides)
    return value


def test_national_campaign_matches_kenya_hotspot():
    assert is_campaign_eligible_for_hotspot(
        campaign(),
        HOTSPOT,
        now=NOW,
    )


def test_county_campaign_matches_selected_county():
    assert is_campaign_eligible_for_hotspot(
        campaign(
            coverage_scope="county",
            target_counties=["Kilifi"],
        ),
        HOTSPOT,
        now=NOW,
    )


def test_county_campaign_does_not_leak_to_other_county():
    assert not is_campaign_eligible_for_hotspot(
        campaign(
            coverage_scope="county",
            target_counties=["Mombasa"],
        ),
        HOTSPOT,
        now=NOW,
    )


def test_constituency_campaign_matches_selected_constituency():
    assert is_campaign_eligible_for_hotspot(
        campaign(
            coverage_scope="constituency",
            target_constituencies=["Kilifi North"],
        ),
        HOTSPOT,
        now=NOW,
    )


def test_constituency_campaign_does_not_leak():
    assert not is_campaign_eligible_for_hotspot(
        campaign(
            coverage_scope="constituency",
            target_constituencies=["Kilifi South"],
        ),
        HOTSPOT,
        now=NOW,
    )


def test_hotspot_campaign_matches_selected_hotspot():
    assert is_campaign_eligible_for_hotspot(
        campaign(
            coverage_scope="hotspot",
            target_hotspot_ids=["hotspot-mtwapa"],
        ),
        HOTSPOT,
        now=NOW,
    )


def test_hotspot_campaign_does_not_match_other_hotspot():
    assert not is_campaign_eligible_for_hotspot(
        campaign(
            coverage_scope="hotspot",
            target_hotspot_ids=["hotspot-other"],
        ),
        HOTSPOT,
        now=NOW,
    )


def test_non_active_campaign_is_excluded():
    assert not is_campaign_eligible_for_hotspot(
        campaign(status="draft"),
        HOTSPOT,
        now=NOW,
    )


def test_campaign_before_start_is_excluded():
    assert not is_campaign_eligible_for_hotspot(
        campaign(
            start_date=(NOW + timedelta(hours=1)).isoformat(),
            end_date=(NOW + timedelta(hours=2)).isoformat(),
        ),
        HOTSPOT,
        now=NOW,
    )


def test_expired_campaign_is_excluded():
    assert not is_campaign_eligible_for_hotspot(
        campaign(
            start_date=(NOW - timedelta(hours=2)).isoformat(),
            end_date=(NOW - timedelta(hours=1)).isoformat(),
        ),
        HOTSPOT,
        now=NOW,
    )


def test_malformed_dates_are_excluded_safely():
    assert not is_campaign_eligible_for_hotspot(
        campaign(start_date="invalid"),
        HOTSPOT,
        now=NOW,
    )


def test_unknown_scope_is_excluded():
    assert not is_campaign_eligible_for_hotspot(
        campaign(coverage_scope="region"),
        HOTSPOT,
        now=NOW,
    )
