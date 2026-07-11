from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from backend.schemas.owner_payment import (
    BankTransferCustomerMethod,
    CustomerPaymentMethod,
    CustomerPaymentMethods,
    MPesaPaybillCustomerMethod,
    MPesaTillCustomerMethod,
    OwnerPaymentProfile,
    OwnerPaymentProfileCreate,
    PaymentProfileStatus,
    PaystackCustomerMethod,
    SettlementConfiguration,
    SettlementMethod,
    VerificationMode,
    mask_sensitive_value,
)


def valid_paystack_profile() -> OwnerPaymentProfileCreate:
    return OwnerPaymentProfileCreate(
        owner_id="owner-1",
        customer_payment_methods=CustomerPaymentMethods(
            paystack=PaystackCustomerMethod(enabled=True),
        ),
        default_customer_method=CustomerPaymentMethod.PAYSTACK,
        settlement=SettlementConfiguration(
            method=SettlementMethod.PAYSTACK_SUBACCOUNT,
            paystack_subaccount_code="ACCT_owner123",
        ),
        status=PaymentProfileStatus.ACTIVE,
    )


def test_valid_paystack_profile_contract():
    profile = valid_paystack_profile()

    assert profile.owner_id == "owner-1"
    assert profile.customer_payment_methods.paystack.enabled is True
    assert profile.default_customer_method == CustomerPaymentMethod.PAYSTACK
    assert (
        profile.settlement.method
        == SettlementMethod.PAYSTACK_SUBACCOUNT
    )


def test_unknown_fields_are_rejected():
    with pytest.raises(ValidationError):
        OwnerPaymentProfileCreate(
            owner_id="owner-1",
            customer_payment_methods=CustomerPaymentMethods(
                paystack=PaystackCustomerMethod(enabled=True),
            ),
            default_customer_method=CustomerPaymentMethod.PAYSTACK,
            settlement=SettlementConfiguration(
                method=SettlementMethod.PAYSTACK_SUBACCOUNT,
                paystack_subaccount_code="ACCT_owner123",
            ),
            unknown_field="not-allowed",
        )


def test_default_customer_method_must_be_enabled():
    with pytest.raises(
        ValidationError,
        match="default_customer_method must reference an enabled",
    ):
        OwnerPaymentProfileCreate(
            owner_id="owner-1",
            customer_payment_methods=CustomerPaymentMethods(),
            default_customer_method=CustomerPaymentMethod.PAYSTACK,
            settlement=SettlementConfiguration(
                method=SettlementMethod.PAYSTACK_SUBACCOUNT,
                paystack_subaccount_code="ACCT_owner123",
            ),
        )


def test_paystack_settlement_requires_subaccount_code():
    with pytest.raises(
        ValidationError,
        match="paystack_subaccount_code is required",
    ):
        SettlementConfiguration(
            method=SettlementMethod.PAYSTACK_SUBACCOUNT,
        )


def test_enabled_paybill_requires_number_and_reference_template():
    with pytest.raises(
        ValidationError,
        match="paybill_number is required",
    ):
        MPesaPaybillCustomerMethod(
            enabled=True,
            account_reference_template="HOTSPOT-{hotspot_id}",
        )

    with pytest.raises(
        ValidationError,
        match="account_reference_template is required",
    ):
        MPesaPaybillCustomerMethod(
            enabled=True,
            paybill_number="123456",
        )


def test_enabled_till_requires_till_number():
    with pytest.raises(
        ValidationError,
        match="till_number is required",
    ):
        MPesaTillCustomerMethod(enabled=True)


def test_enabled_bank_transfer_requires_core_bank_fields():
    with pytest.raises(
        ValidationError,
        match="Missing required bank transfer fields",
    ):
        BankTransferCustomerMethod(
            enabled=True,
            bank_name="Example Bank",
        )


def test_manual_methods_cannot_claim_automatic_verification():
    with pytest.raises(
        ValidationError,
        match="Paybill cannot use automatic verification",
    ):
        MPesaPaybillCustomerMethod(
            enabled=True,
            paybill_number="123456",
            account_reference_template="HOTSPOT-{hotspot_id}",
            verification_mode=VerificationMode.AUTOMATIC,
        )

    with pytest.raises(
        ValidationError,
        match="Till payments cannot use automatic verification",
    ):
        MPesaTillCustomerMethod(
            enabled=True,
            till_number="654321",
            verification_mode=VerificationMode.AUTOMATIC,
        )

    with pytest.raises(
        ValidationError,
        match="Bank transfer cannot use automatic verification",
    ):
        BankTransferCustomerMethod(
            enabled=True,
            bank_name="Example Bank",
            account_name="CAIWAVE Owner",
            account_number="1234567890",
            verification_mode=VerificationMode.AUTOMATIC,
        )


def test_direct_paybill_settlement_requires_paybill_customer_method():
    with pytest.raises(
        ValidationError,
        match="Direct Paybill settlement requires",
    ):
        OwnerPaymentProfileCreate(
            owner_id="owner-1",
            customer_payment_methods=CustomerPaymentMethods(
                paystack=PaystackCustomerMethod(enabled=True),
            ),
            default_customer_method=CustomerPaymentMethod.PAYSTACK,
            settlement=SettlementConfiguration(
                method=SettlementMethod.DIRECT_PAYBILL,
                paybill_number="123456",
            ),
        )


def test_valid_direct_paybill_profile():
    profile = OwnerPaymentProfileCreate(
        owner_id="owner-1",
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
    )

    assert profile.customer_payment_methods.mpesa_paybill.enabled is True
    assert profile.settlement.paybill_number == "123456"


def test_sensitive_value_masking():
    assert mask_sensitive_value("1234567890") == "******7890"
    assert mask_sensitive_value("1234") == "****"
    assert mask_sensitive_value("") is None
    assert mask_sensitive_value(None) is None


def test_persisted_profile_contract():
    now = datetime.now(timezone.utc)

    profile = OwnerPaymentProfile(
        id="profile-1",
        owner_id="owner-1",
        schema_version="1.0",
        customer_payment_methods=CustomerPaymentMethods(
            paystack=PaystackCustomerMethod(enabled=True),
        ),
        default_customer_method=CustomerPaymentMethod.PAYSTACK,
        settlement=SettlementConfiguration(
            method=SettlementMethod.PAYSTACK_SUBACCOUNT,
            paystack_subaccount_code="ACCT_owner123",
        ),
        status=PaymentProfileStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )

    assert profile.id == "profile-1"
    assert profile.schema_version == "1.0"
    assert profile.created_at == now
