import pytest

from backend.services.campaign_targeting import (
    CampaignCoverageScope,
    CampaignTargetingValidationError,
    normalize_campaign_targeting,
    validate_campaign_targeting,
)


LOCATIONS = {
    "Mombasa": ["Changamwe", "Nyali", "Mvita"],
    "Kilifi": ["Kilifi North", "Kilifi South"],
    "Nairobi": ["Westlands", "Langata"],
}

HOTSPOTS = {
    "hotspot-mtwapa",
    "hotspot-nyali",
}


def validate(**overrides):
    payload = {
        "coverage_scope": "national",
        "country_code": "KE",
        "country_name": "Kenya",
        "counties": [],
        "constituencies": [],
        "hotspot_ids": [],
        "assigned_ad_ids": ["ad-1"],
        "locations_by_county": LOCATIONS,
        "known_hotspot_ids": HOTSPOTS,
    }
    payload.update(overrides)
    return validate_campaign_targeting(**payload)


def test_coverage_scope_values_are_stable():
    assert [scope.value for scope in CampaignCoverageScope] == [
        "national",
        "county",
        "constituency",
        "hotspot",
    ]


def test_normalization_trims_and_deduplicates_values():
    result = normalize_campaign_targeting(
        coverage_scope=" COUNTY ",
        counties=[" Kilifi ", "Kilifi", "", "Mombasa"],
        assigned_ad_ids=[" ad-1 ", "ad-1", "ad-2"],
    )

    assert result["coverage_scope"] == "county"
    assert result["counties"] == ["Kilifi", "Mombasa"]
    assert result["assigned_ad_ids"] == ["ad-1", "ad-2"]


def test_valid_national_campaign():
    result = validate()

    assert result["coverage_scope"] == "national"
    assert result["country_code"] == "KE"


def test_valid_county_campaign():
    result = validate(
        coverage_scope="county",
        counties=["Kilifi", "Mombasa"],
    )

    assert result["counties"] == ["Kilifi", "Mombasa"]


def test_valid_constituency_campaign():
    result = validate(
        coverage_scope="constituency",
        constituencies=["Kilifi North", "Nyali"],
    )

    assert result["constituencies"] == ["Kilifi North", "Nyali"]


def test_valid_hotspot_campaign():
    result = validate(
        coverage_scope="hotspot",
        hotspot_ids=["hotspot-mtwapa"],
    )

    assert result["hotspot_ids"] == ["hotspot-mtwapa"]


def test_campaign_targeting_allows_no_assigned_advertisements():
    result = validate(assigned_ad_ids=[])

    assert result["assigned_ad_ids"] == []


@pytest.mark.parametrize(
    ("field", "overrides"),
    [
        ("coverage_scope", {"coverage_scope": "region"}),
        ("country_code", {"country_code": "UG"}),
        ("country_name", {"country_name": "Uganda"}),
        ("counties", {"coverage_scope": "county", "counties": []}),
        (
            "counties",
            {"coverage_scope": "county", "counties": ["Unknown"]},
        ),
        (
            "constituencies",
            {
                "coverage_scope": "constituency",
                "constituencies": [],
            },
        ),
        (
            "constituencies",
            {
                "coverage_scope": "constituency",
                "constituencies": ["Unknown"],
            },
        ),
        (
            "hotspot_ids",
            {"coverage_scope": "hotspot", "hotspot_ids": []},
        ),
        (
            "hotspot_ids",
            {
                "coverage_scope": "hotspot",
                "hotspot_ids": ["missing-hotspot"],
            },
        ),
    ],
)
def test_invalid_campaign_targeting_is_rejected(field, overrides):
    with pytest.raises(CampaignTargetingValidationError) as exc:
        validate(**overrides)

    assert exc.value.field == field


@pytest.mark.parametrize(
    "overrides",
    [
        {
            "coverage_scope": "national",
            "counties": ["Kilifi"],
        },
        {
            "coverage_scope": "county",
            "counties": ["Kilifi"],
            "constituencies": ["Kilifi North"],
        },
        {
            "coverage_scope": "constituency",
            "constituencies": ["Kilifi North"],
            "hotspot_ids": ["hotspot-mtwapa"],
        },
        {
            "coverage_scope": "hotspot",
            "hotspot_ids": ["hotspot-mtwapa"],
            "counties": ["Kilifi"],
        },
    ],
)
def test_scopes_cannot_mix_incompatible_targets(overrides):
    with pytest.raises(CampaignTargetingValidationError) as exc:
        validate(**overrides)

    assert exc.value.field == "coverage_scope"
