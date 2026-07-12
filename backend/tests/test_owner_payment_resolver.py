from datetime import datetime, timezone

import pytest

from backend.schemas.owner_payment import (
    CustomerPaymentMethod,
    CustomerPaymentMethods,
    MPesaPaybillCustomerMethod,
    OwnerPaymentProfile,
    PaymentProfileStatus,
    PaystackCustomerMethod,
    SettlementConfiguration,
    SettlementMethod,
)
from backend.services.owner_payment.resolver import (
    AutomaticVerificationUnavailable,
    OwnerPaymentProfileInactive,
    OwnerPaymentProfileRequired,
    OwnerPaymentResolver,
    PaymentDestination,
    PlatformPaymentType,
)


def make_paystack_profile(
    *,
    owner_id: str = "owner-1",
    status: PaymentProfileStatus = PaymentProfileStatus.ACTIVE,
) -> OwnerPaymentProfile:
    now = datetime.now(timezone.utc)

    return OwnerPaymentProfile(
        id="profile-1",
        owner_id=owner_id,
        schema_version="1.0",
        customer_payment_methods=CustomerPaymentMethods(
            paystack=PaystackCustomerMethod(enabled=True),
        ),
        default_customer_method=CustomerPaymentMethod.PAYSTACK,
        settlement=SettlementConfiguration(
            method=SettlementMethod.PAYSTACK_SUBACCOUNT,
            paystack_subaccount_code="ACCT_owner123",
        ),
        status=status,
        created_at=now,
        updated_at=now,
    )


def make_paybill_profile() -> OwnerPaymentProfile:
    now = datetime.now(timezone.utc)

    return OwnerPaymentProfile(
        id="profile-paybill",
        owner_id="owner-paybill",
        schema_version="1.0",
        customer_payment_methods=CustomerPaymentMethods(
            mpesa_paybill=MPesaPaybillCustomerMethod(
                enabled=True,
                paybill_number="123456",
                business_name="Owner Business",
                account_reference_template="HOTSPOT-{hotspot_id}",
            ),
        ),
        default_customer_method=CustomerPaymentMethod.MPESA_PAYBILL,
        settlement=SettlementConfiguration(
            method=SettlementMethod.DIRECT_PAYBILL,
            paybill_number="123456",
        ),
        status=PaymentProfileStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def resolver():
    return OwnerPaymentResolver()


@pytest.mark.parametrize(
    "payment_type",
    [
        PlatformPaymentType.OWNER_SUBSCRIPTION,
        PlatformPaymentType.ADVERTISER_PACKAGE,
    ],
)
def test_platform_revenue_resolves_to_caiwave(resolver, payment_type):
    result = resolver.resolve(payment_type)

    assert result.destination == PaymentDestination.CAIWAVE
    assert result.owner_id is None
    assert result.automatic_fulfilment_supported is True


def test_wifi_revenue_resolves_to_owner_paystack_profile(resolver):
    result = resolver.resolve(
        PlatformPaymentType.WIFI_PACKAGE,
        owner_id="owner-1",
        owner_profile=make_paystack_profile(),
        require_automatic_fulfilment=True,
    )

    assert result.destination == PaymentDestination.HOTSPOT_OWNER
    assert result.owner_id == "owner-1"
    assert (
        result.customer_payment_method
        == CustomerPaymentMethod.PAYSTACK
    )
    assert (
        result.settlement_method
        == SettlementMethod.PAYSTACK_SUBACCOUNT
    )
    assert result.automatic_fulfilment_supported is True


def test_wifi_resolution_requires_owner_id(resolver):
    with pytest.raises(
        OwnerPaymentProfileRequired,
        match="require a hotspot owner ID",
    ):
        resolver.resolve(
            PlatformPaymentType.WIFI_PACKAGE,
            owner_profile=make_paystack_profile(),
        )


def test_wifi_resolution_requires_owner_profile(resolver):
    with pytest.raises(
        OwnerPaymentProfileRequired,
        match="profile is required",
    ):
        resolver.resolve(
            PlatformPaymentType.WIFI_PACKAGE,
            owner_id="owner-1",
        )


def test_owner_profile_must_match_hotspot_owner(resolver):
    with pytest.raises(
        OwnerPaymentProfileRequired,
        match="does not belong",
    ):
        resolver.resolve(
            PlatformPaymentType.WIFI_PACKAGE,
            owner_id="different-owner",
            owner_profile=make_paystack_profile(),
        )


def test_inactive_owner_profile_is_rejected(resolver):
    with pytest.raises(
        OwnerPaymentProfileInactive,
        match="suspended",
    ):
        resolver.resolve(
            PlatformPaymentType.WIFI_PACKAGE,
            owner_id="owner-1",
            owner_profile=make_paystack_profile(
                status=PaymentProfileStatus.SUSPENDED,
            ),
        )


def test_manual_paybill_can_resolve_without_automatic_fulfilment(resolver):
    result = resolver.resolve(
        PlatformPaymentType.WIFI_PACKAGE,
        owner_id="owner-paybill",
        owner_profile=make_paybill_profile(),
        require_automatic_fulfilment=False,
    )

    assert result.destination == PaymentDestination.HOTSPOT_OWNER
    assert (
        result.customer_payment_method
        == CustomerPaymentMethod.MPESA_PAYBILL
    )
    assert result.automatic_fulfilment_supported is False


def test_manual_paybill_cannot_grant_automatic_hotspot_access(resolver):
    with pytest.raises(
        AutomaticVerificationUnavailable,
        match="cannot automatically",
    ):
        resolver.resolve(
            PlatformPaymentType.WIFI_PACKAGE,
            owner_id="owner-paybill",
            owner_profile=make_paybill_profile(),
            require_automatic_fulfilment=True,
        )
