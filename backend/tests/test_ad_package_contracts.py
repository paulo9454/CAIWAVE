import pytest
from pydantic import ValidationError

from backend.server import (
    AdCoverageScope,
    AdPackage,
    AdPackageCreate,
    AdPackageStatus,
    AdPackageUpdate,
)


def valid_create_payload(**overrides):
    payload = {
        "name": "Local Starter",
        "description": "Local constituency advertising package.",
        "coverage_scope": "constituency",
        "duration_days": 7,
        "price": 5,
        "max_impressions": 5000,
    }
    payload.update(overrides)
    return payload


def test_kes_five_package_is_valid():
    package = AdPackageCreate(**valid_create_payload())

    assert package.price == 5
    assert package.duration_days == 7
    assert package.coverage_scope is AdCoverageScope.CONSTITUENCY


@pytest.mark.parametrize("price", [0, -1, -500])
def test_zero_and_negative_prices_are_rejected(price):
    with pytest.raises(ValidationError):
        AdPackageCreate(**valid_create_payload(price=price))


@pytest.mark.parametrize("duration_days", [0, -1])
def test_invalid_duration_is_rejected(duration_days):
    with pytest.raises(ValidationError):
        AdPackageCreate(
            **valid_create_payload(duration_days=duration_days)
        )


@pytest.mark.parametrize("max_impressions", [0, -10])
def test_invalid_impression_limit_is_rejected(max_impressions):
    with pytest.raises(ValidationError):
        AdPackageCreate(
            **valid_create_payload(
                max_impressions=max_impressions,
            )
        )


def test_blank_name_is_rejected_after_whitespace_trim():
    with pytest.raises(ValidationError):
        AdPackageCreate(**valid_create_payload(name="   "))


def test_blank_description_is_rejected_after_whitespace_trim():
    with pytest.raises(ValidationError):
        AdPackageCreate(
            **valid_create_payload(description="   ")
        )


def test_unknown_create_fields_are_rejected():
    with pytest.raises(ValidationError):
        AdPackageCreate(
            **valid_create_payload(browser_amount=1)
        )


def test_partial_update_accepts_price_only():
    update = AdPackageUpdate(price=5)

    assert update.price == 5
    assert update.name is None


def test_update_serializes_enums_as_plain_strings():
    update = AdPackageUpdate(
        coverage_scope=AdCoverageScope.COUNTY,
        status=AdPackageStatus.DISABLED,
    )

    payload = update.model_dump(
        mode="json",
        exclude_none=True,
        exclude_unset=True,
    )

    assert payload == {
        "coverage_scope": "county",
        "status": "disabled",
    }


def test_full_package_serializes_matching_frontend_contract():
    package = AdPackage(**valid_create_payload())

    payload = package.model_dump(mode="json")

    assert payload["name"] == "Local Starter"
    assert payload["coverage_scope"] == "constituency"
    assert payload["duration_days"] == 7
    assert payload["price"] == 5
    assert payload["max_impressions"] == 5000
    assert payload["status"] == "active"
