from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from backend.schemas.owner_gateway import (
    BankPaybillAPIGatewayConfiguration,
    GatewayVerificationStatus,
    KopoKopoGatewayConfiguration,
    MPesaDarajaGatewayConfiguration,
    OwnerGatewayProfile,
    OwnerGatewayProfileCreate,
    OwnerGatewayStatus,
    PaystackGatewayConfiguration,
    mask_value,
)


def test_valid_paystack_draft_profile():
    profile = OwnerGatewayProfileCreate(
        owner_id="owner-1",
        configuration=PaystackGatewayConfiguration(
            business_name="Owner Business",
            contact_email="owner@example.com",
            contact_phone="254700000000",
            uses_caiwave_platform_account=True,
        ),
    )

    assert profile.owner_id == "owner-1"
    assert profile.configuration.gateway == "paystack"
    assert profile.status == OwnerGatewayStatus.DRAFT


def test_external_paystack_account_requires_subaccount():
    with pytest.raises(
        ValidationError,
        match="subaccount code is required",
    ):
        PaystackGatewayConfiguration(
            business_name="Owner Business",
            contact_email="owner@example.com",
            contact_phone="254700000000",
            uses_caiwave_platform_account=False,
        )


def test_active_gateway_must_be_verified():
    with pytest.raises(
        ValidationError,
        match="cannot be active until it is verified",
    ):
        OwnerGatewayProfileCreate(
            owner_id="owner-1",
            configuration=PaystackGatewayConfiguration(
                business_name="Owner Business",
                contact_email="owner@example.com",
                contact_phone="254700000000",
            ),
            status=OwnerGatewayStatus.ACTIVE,
            verification_status=(
                GatewayVerificationStatus.NOT_VERIFIED
            ),
        )


def test_verified_gateway_requires_timestamp():
    with pytest.raises(
        ValidationError,
        match="last_verified_at is required",
    ):
        OwnerGatewayProfileCreate(
            owner_id="owner-1",
            configuration=PaystackGatewayConfiguration(
                business_name="Owner Business",
                contact_email="owner@example.com",
                contact_phone="254700000000",
            ),
            verification_status=GatewayVerificationStatus.VERIFIED,
        )


def test_valid_verified_active_gateway():
    now = datetime.now(timezone.utc)

    profile = OwnerGatewayProfile(
        id="gateway-1",
        owner_id="owner-1",
        configuration=PaystackGatewayConfiguration(
            business_name="Owner Business",
            contact_email="owner@example.com",
            contact_phone="254700000000",
            paystack_subaccount_code="ACCT_owner123",
        ),
        status=OwnerGatewayStatus.ACTIVE,
        verification_status=GatewayVerificationStatus.VERIFIED,
        last_verified_at=now,
        created_at=now,
        updated_at=now,
    )

    assert profile.status == OwnerGatewayStatus.ACTIVE
    assert profile.last_verified_at == now


def test_daraja_requires_https_callback():
    with pytest.raises(
        ValidationError,
        match="callback URL must use HTTPS",
    ):
        MPesaDarajaGatewayConfiguration(
            business_name="Owner Business",
            shortcode="123456",
            shortcode_type="paybill",
            consumer_key_ref="secret://daraja/key",
            consumer_secret_ref="secret://daraja/secret",
            passkey_ref="secret://daraja/passkey",
            callback_url="http://example.com/callback",
        )


def test_valid_daraja_configuration():
    config = MPesaDarajaGatewayConfiguration(
        business_name="Owner Business",
        shortcode="123456",
        shortcode_type="paybill",
        consumer_key_ref="secret://daraja/key",
        consumer_secret_ref="secret://daraja/secret",
        passkey_ref="secret://daraja/passkey",
        callback_url="https://www.caiwave.com/api/payments/daraja/callback",
    )

    assert config.gateway == "mpesa_daraja"
    assert config.shortcode_type == "paybill"


def test_valid_kopokopo_configuration():
    config = KopoKopoGatewayConfiguration(
        business_name="Owner Business",
        till_number="123456",
        client_id_ref="secret://kopokopo/client-id",
        client_secret_ref="secret://kopokopo/client-secret",
        callback_url="https://www.caiwave.com/api/payments/kopokopo/callback",
    )

    assert config.gateway == "kopokopo"


def test_bank_gateway_requires_https_urls():
    with pytest.raises(
        ValidationError,
        match="payment API URL must use HTTPS",
    ):
        BankPaybillAPIGatewayConfiguration(
            provider_name="Example Bank",
            business_name="Owner Business",
            paybill_number="542542",
            receiving_account_number="825975",
            client_id_ref="secret://bank/client-id",
            client_secret_ref="secret://bank/client-secret",
            callback_signing_secret_ref="secret://bank/callback",
            payment_api_url="http://bank.example/api",
            callback_url="https://www.caiwave.com/api/payments/bank/callback",
        )


def test_valid_bank_paybill_api_configuration():
    config = BankPaybillAPIGatewayConfiguration(
        provider_name="Example Bank",
        business_name="Owner Business",
        paybill_number="542542",
        receiving_account_number="825975",
        client_id_ref="secret://bank/client-id",
        client_secret_ref="secret://bank/client-secret",
        callback_signing_secret_ref="secret://bank/callback",
        payment_api_url="https://bank.example/api",
        callback_url="https://www.caiwave.com/api/payments/bank/callback",
    )

    assert config.gateway == "bank_paybill_api"


def test_discriminated_gateway_configuration_rejects_unknown_gateway():
    with pytest.raises(ValidationError):
        OwnerGatewayProfileCreate.model_validate({
            "owner_id": "owner-1",
            "configuration": {
                "gateway": "manual_paybill",
                "business_name": "Owner Business",
            },
        })


def test_unknown_fields_are_rejected():
    with pytest.raises(ValidationError):
        PaystackGatewayConfiguration(
            business_name="Owner Business",
            contact_email="owner@example.com",
            contact_phone="254700000000",
            unexpected_field="not-allowed",
        )


def test_mask_value():
    assert mask_value("1234567890") == "******7890"
    assert mask_value("1234") == "****"
    assert mask_value("") is None
    assert mask_value(None) is None
