from backend.server import CampaignCreate
from backend.services.campaign_targeting import CampaignCoverageScope


def test_campaign_create_defaults_to_national_kenya():
    campaign = CampaignCreate(
        name="National Campaign",
        start_date="2026-07-12T12:00:00+00:00",
        end_date="2026-07-13T12:00:00+00:00",
        assigned_ad_ids=["ad-1"],
    )

    assert campaign.coverage_scope is CampaignCoverageScope.NATIONAL
    assert campaign.country_code == "KE"
    assert campaign.country_name == "Kenya"
    assert campaign.target_counties == []
    assert campaign.target_constituencies == []
    assert campaign.target_hotspot_ids == []


def test_campaign_create_accepts_constituency_targeting():
    campaign = CampaignCreate(
        name="Kilifi North Campaign",
        start_date="2026-07-12T12:00:00+00:00",
        end_date="2026-07-13T12:00:00+00:00",
        coverage_scope="constituency",
        target_constituencies=["Kilifi North"],
        assigned_ad_ids=["ad-1"],
    )

    assert campaign.coverage_scope is CampaignCoverageScope.CONSTITUENCY
    assert campaign.target_constituencies == ["Kilifi North"]


def test_legacy_target_regions_remain_readable():
    campaign = CampaignCreate(
        name="Compatibility Campaign",
        start_date="2026-07-12T12:00:00+00:00",
        end_date="2026-07-13T12:00:00+00:00",
        assigned_ad_ids=["ad-1"],
        target_regions=["Legacy"],
    )

    assert campaign.target_regions == ["Legacy"]
