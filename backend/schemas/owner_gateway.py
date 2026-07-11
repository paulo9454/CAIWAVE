"""
Owner Automated Payment Gateway contracts.

One hotspot owner configures exactly one active automated gateway.
Customers never select a gateway; they only enter their phone number,
click Pay, receive an STK prompt, and obtain internet after verification.

This module has:
- no database I/O
- no API registration
- no live payment execution
- no changes to current WiFi checkout
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Literal, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    model_validator,
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class OwnerGatewayType(str, Enum):
    PAYSTACK = "paystack"
    MPESA_DARAJA = "mpesa_daraja"
    KOPOKOPO = "kopokopo"
    BANK_PAYBILL_API = "bank_paybill_api"


class OwnerGatewayStatus(str, Enum):
    DRAFT = "draft"
    PENDING_VERIFICATION = "pending_verification"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class GatewayVerificationStatus(str, Enum):
    NOT_VERIFIED = "not_verified"
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"


class PaystackGatewayConfiguration(StrictModel):
    gateway: Literal["paystack"] = "paystack"

    business_name: str
    contact_email: EmailStr
    contact_phone: str

    paystack_subaccount_code: Optional[str] = None
    settlement_bank_name: Optional[str] = None
    settlement_account_last4: Optional[str] = None

    uses_caiwave_platform_account: bool = True

    @model_validator(mode="after")
    def validate_paystack(self) -> "PaystackGatewayConfiguration":
        if (
            not self.uses_caiwave_platform_account
            and not self.paystack_subaccount_code
        ):
            raise ValueError(
                "A Paystack subaccount code is required when the owner "
                "does not use the CAIWAVE platform account."
            )

        return self


class MPesaDarajaGatewayConfiguration(StrictModel):
    gateway: Literal["mpesa_daraja"] = "mpesa_daraja"

    business_name: str
    shortcode: str
    shortcode_type: Literal["paybill", "till"]

    consumer_key_ref: str
    consumer_secret_ref: str
    passkey_ref: str

    callback_url: str
    callback_signing_secret_ref: Optional[str] = None

    @model_validator(mode="after")
    def validate_daraja(self) -> "MPesaDarajaGatewayConfiguration":
        if not self.shortcode.strip():
            raise ValueError("M-Pesa shortcode is required.")

        if not self.callback_url.startswith("https://"):
            raise ValueError("M-Pesa callback URL must use HTTPS.")

        return self


class KopoKopoGatewayConfiguration(StrictModel):
    gateway: Literal["kopokopo"] = "kopokopo"

    business_name: str
    till_number: str

    client_id_ref: str
    client_secret_ref: str
    api_key_ref: Optional[str] = None

    callback_url: str
    callback_signing_secret_ref: Optional[str] = None

    @model_validator(mode="after")
    def validate_kopokopo(self) -> "KopoKopoGatewayConfiguration":
        if not self.till_number.strip():
            raise ValueError("Kopo Kopo Till number is required.")

        if not self.callback_url.startswith("https://"):
            raise ValueError("Kopo Kopo callback URL must use HTTPS.")

        return self


class BankPaybillAPIGatewayConfiguration(StrictModel):
    gateway: Literal["bank_paybill_api"] = "bank_paybill_api"

    provider_name: str
    business_name: str

    paybill_number: str
    receiving_account_number: str

    client_id_ref: str
    client_secret_ref: str
    callback_signing_secret_ref: str

    payment_api_url: str
    callback_url: str

    @model_validator(mode="after")
    def validate_bank_gateway(
        self,
    ) -> "BankPaybillAPIGatewayConfiguration":
        if not self.paybill_number.strip():
            raise ValueError("Bank Paybill number is required.")

        if not self.receiving_account_number.strip():
            raise ValueError("Bank receiving account number is required.")

        if not self.payment_api_url.startswith("https://"):
            raise ValueError("Bank payment API URL must use HTTPS.")

        if not self.callback_url.startswith("https://"):
            raise ValueError("Bank callback URL must use HTTPS.")

        return self


OwnerGatewayConfiguration = Annotated[
    Union[
        PaystackGatewayConfiguration,
        MPesaDarajaGatewayConfiguration,
        KopoKopoGatewayConfiguration,
        BankPaybillAPIGatewayConfiguration,
    ],
    Field(discriminator="gateway"),
]


class OwnerGatewayProfileBase(StrictModel):
    configuration: OwnerGatewayConfiguration

    status: OwnerGatewayStatus = OwnerGatewayStatus.DRAFT
    verification_status: GatewayVerificationStatus = (
        GatewayVerificationStatus.NOT_VERIFIED
    )

    verification_message: Optional[str] = None
    last_verified_at: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_activation_state(self) -> "OwnerGatewayProfileBase":
        if (
            self.status == OwnerGatewayStatus.ACTIVE
            and self.verification_status
            != GatewayVerificationStatus.VERIFIED
        ):
            raise ValueError(
                "An owner gateway cannot be active until it is verified."
            )

        if (
            self.verification_status
            == GatewayVerificationStatus.VERIFIED
            and self.last_verified_at is None
        ):
            raise ValueError(
                "last_verified_at is required for a verified gateway."
            )

        return self


class OwnerGatewayProfileCreate(OwnerGatewayProfileBase):
    owner_id: str


class OwnerGatewayProfileUpdate(StrictModel):
    configuration: Optional[OwnerGatewayConfiguration] = None
    status: Optional[OwnerGatewayStatus] = None
    verification_status: Optional[GatewayVerificationStatus] = None
    verification_message: Optional[str] = None
    last_verified_at: Optional[datetime] = None


class OwnerGatewayProfile(OwnerGatewayProfileBase):
    id: str
    owner_id: str

    schema_version: str = "1.0"

    created_at: datetime
    updated_at: datetime


class PublicOwnerGatewayConfiguration(StrictModel):
    gateway: OwnerGatewayType
    business_name: str

    provider_name: Optional[str] = None

    contact_email: Optional[str] = None
    contact_phone_masked: Optional[str] = None

    shortcode_masked: Optional[str] = None
    till_number_masked: Optional[str] = None
    paybill_number_masked: Optional[str] = None
    receiving_account_masked: Optional[str] = None
    settlement_account_last4: Optional[str] = None

    uses_caiwave_platform_account: Optional[bool] = None

    credentials_configured: bool
    callback_url: Optional[str] = None


class OwnerGatewayProfileResponse(StrictModel):
    id: str
    owner_id: str
    schema_version: str

    configuration: PublicOwnerGatewayConfiguration

    status: OwnerGatewayStatus
    verification_status: GatewayVerificationStatus
    verification_message: Optional[str] = None
    last_verified_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime


def mask_value(
    value: Optional[str],
    visible_characters: int = 4,
) -> Optional[str]:
    if value is None:
        return None

    normalized = str(value).strip()

    if not normalized:
        return None

    if len(normalized) <= visible_characters:
        return "*" * len(normalized)

    return (
        "*" * (len(normalized) - visible_characters)
        + normalized[-visible_characters:]
    )
