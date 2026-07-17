from datetime import datetime, timedelta, timezone

import pytest

from backend.services.campaign_targeting import (
    CampaignValidationError,
    build_campaign_write_payload,
    is_ad_eligible_for_campaign,
    validate_campaign_ads,
    validate_campaign_dates,
)


NOW = datetime(2026, 7, 12, 12, 0, tzinfo=timezone.utc)

LOCATIONS = {
    "Kilifi": ["Kilifi North", "Kilifi South"],
    "Mombasa": ["Nyali", "Mvita"],
}

HOTSPOTS = {
    "hotspot-mtwapa",
    "hotspot-nyali",
}


def eligible_ad(ad_id="ad-active"):
    return {
        "id": ad_id,
        "status": "active",
        "is_active": True,
        "approved_at": (NOW - timedelta(days=2)).isoformat(),
        "paid_at": (NOW - timedelta(days=1)).isoformat(),
        "expires_at": (NOW + timedelta(days=5)).isoformat(),
    }


def test_valid_campaign_dates():
    start, end = validate_campaign_dates(
        start_date="2026-07-12T12:00:00+00:00",
        end_date="2026-07-13T12:00:00+00:00",
    )

    assert start == NOW
    assert end > start


@pytest.mark.parametrize(
    ("field", "start_date", "end_date"),
    [
        ("start_date", "", "2026-07-13T12:00:00+00:00"),
        ("end_date", NOW, NOW),
        ("end_date", NOW, NOW - timedelta(minutes=1)),
    ],
)
def test_invalid_campaign_dates(field, start_date, end_date):
    with pytest.raises(CampaignValidationError) as exc:
        validate_campaign_dates(
            start_date=start_date,
            end_date=end_date,
        )

    assert exc.value.field == field


def test_active_paid_approved_unexpired_ad_is_eligible():
    assert is_ad_eligible_for_campaign(
        eligible_ad(),
        now=NOW,
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"status": "approved"},
        {"is_active": False},
        {"approved_at": None},
        {"paid_at": None},
        {"expires_at": None},
        {"expires_at": (NOW - timedelta(seconds=1)).isoformat()},
    ],
)
def test_ineligible_ad_states_are_rejected(changes):
    ad = eligible_ad()
    ad.update(changes)

    assert not is_ad_eligible_for_campaign(ad, now=NOW)


def test_ad_eligibility_does_not_require_payment_id():
    ad = eligible_ad()
    ad["payment_id"] = None

    assert is_ad_eligible_for_campaign(ad, now=NOW)


def test_validate_campaign_ads_allows_no_assigned_advertisements():
    result = validate_campaign_ads(
        assigned_ad_ids=[],
        ads_by_id={},
        now=NOW,
    )

    assert result == []


def test_validate_campaign_ads_deduplicates_ids():
    result = validate_campaign_ads(
        assigned_ad_ids=["ad-active", "ad-active"],
        ads_by_id={"ad-active": eligible_ad()},
        now=NOW,
    )

    assert result == ["ad-active"]


@pytest.mark.parametrize(
    ("expected_message_part", "assigned_ids", "ads"),
    [
        ("do not exist", ["missing"], {}),
        (
            "unpaid, inactive, unapproved or expired",
            ["ad-active"],
            {
                "ad-active": {
                    **eligible_ad(),
                    "paid_at": None,
                },
            },
        ),
    ],
)
def test_invalid_ad_assignments_are_rejected(
    expected_message_part,
    assigned_ids,
    ads,
):
    with pytest.raises(CampaignValidationError) as exc:
        validate_campaign_ads(
            assigned_ad_ids=assigned_ids,
            ads_by_id=ads,
            now=NOW,
        )

    assert exc.value.field == "assigned_ad_ids"
    assert expected_message_part in exc.value.message


def test_build_valid_county_campaign_payload():
    result = build_campaign_write_payload(
        name="Kilifi Campaign",
        description="Local promotion",
        start_date=NOW,
        end_date=NOW + timedelta(days=3),
        coverage_scope="county",
        country_code="KE",
        country_name="Kenya",
        target_counties=["Kilifi"],
        target_constituencies=[],
        target_hotspot_ids=[],
        assigned_ad_ids=["ad-active"],
        locations_by_county=LOCATIONS,
        known_hotspot_ids=HOTSPOTS,
        ads_by_id={"ad-active": eligible_ad()},
        now=NOW,
    )

    assert result["coverage_scope"] == "county"
    assert result["target_counties"] == ["Kilifi"]
    assert result["target_constituencies"] == []
    assert result["target_hotspot_ids"] == []
    assert result["assigned_ad_ids"] == ["ad-active"]
    assert result["target_regions"] == []


def test_build_valid_constituency_campaign_payload():
    result = build_campaign_write_payload(
        name="Mtwapa Campaign",
        description=None,
        start_date=NOW,
        end_date=NOW + timedelta(days=3),
        coverage_scope="constituency",
        target_counties=[],
        target_constituencies=["Kilifi North"],
        target_hotspot_ids=[],
        assigned_ad_ids=["ad-active"],
        locations_by_county=LOCATIONS,
        known_hotspot_ids=HOTSPOTS,
        ads_by_id={"ad-active": eligible_ad()},
        now=NOW,
    )

    assert result["target_constituencies"] == ["Kilifi North"]


def test_build_valid_hotspot_campaign_payload():
    result = build_campaign_write_payload(
        name="Specific Hotspot Campaign",
        description="One location only",
        start_date=NOW,
        end_date=NOW + timedelta(days=1),
        coverage_scope="hotspot",
        target_counties=[],
        target_constituencies=[],
        target_hotspot_ids=["hotspot-mtwapa"],
        assigned_ad_ids=["ad-active"],
        locations_by_county=LOCATIONS,
        known_hotspot_ids=HOTSPOTS,
        ads_by_id={"ad-active": eligible_ad()},
        now=NOW,
    )

    assert result["target_hotspot_ids"] == ["hotspot-mtwapa"]


def test_build_campaign_requires_name():
    with pytest.raises(CampaignValidationError) as exc:
        build_campaign_write_payload(
            name="",
            description=None,
            start_date=NOW,
            end_date=NOW + timedelta(days=1),
            coverage_scope="national",
            assigned_ad_ids=["ad-active"],
            locations_by_county=LOCATIONS,
            known_hotspot_ids=HOTSPOTS,
            ads_by_id={"ad-active": eligible_ad()},
            now=NOW,
        )

    assert exc.value.field == "name"
