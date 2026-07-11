"""
Owner Payment Engine v1 contracts.

These contracts are intentionally isolated:
- no database I/O
- no route registration
- no live payment changes
- no portal behavior changes
- no migration of existing Paystack fields
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CustomerPaymentMethod(str, Enum):
    PAYSTACK = "paystack"
    MPESA_PAYBILL = "mpesa_paybill"
    MPESA_TILL = "mpesa_till"
    BANK_TRANSFER = "bank_transfer"


class SettlementMethod(str, Enum):
    PAYSTACK_SUBACCOUNT = "paystack_subaccount"
    DIRECT_PAYBILL = "direct_paybill"
    DIRECT_TILL = "direct_till"
    BANK_ACCOUNT = "bank_account"


class VerificationMode(str, Enum):
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    UNSUPPORTED = "unsupported"


class PaymentProfileStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"


def mask_sensitive_value(
    value: Optional[str],
    visible_characters: int = 4,
) -> Optional[str]:
    """
    Mask a sensitive value while retaining a short suffix.

    Examples:
    1234567890 -> ******7890
    1234       -> ****
    None       -> None
    """
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


class PaystackCustomerMethod(StrictModel):
    enabled: bool = False
    checkout_mode: str = "hosted"
    verification_mode: VerificationMode = VerificationMode.AUTOMATIC

    @model_validator(mode="after")
    def validate_paystack_method(self) -> "PaystackCustomerMethod":
        if self.checkout_mode != "hosted":
            raise ValueError(
                "Owner Payment Engine v1 supports hosted Paystack checkout only."
            )

        if self.verification_mode != VerificationMode.AUTOMATIC:
            raise ValueError(
                "Paystack checkout must use automatic verification."
            )

        return self


class MPesaPaybillCustomerMethod(StrictModel):
    enabled: bool = False
    paybill_number: Optional[str] = None
    business_name: Optional[str] = None
    account_reference_template: Optional[str] = None
    verification_mode: VerificationMode = VerificationMode.MANUAL

    @model_validator(mode="after")
    def validate_paybill(self) -> "MPesaPaybillCustomerMethod":
        if self.verification_mode == VerificationMode.AUTOMATIC:
            raise ValueError(
                "Paybill cannot use automatic verification until a "
                "verified callback or transaction-query integration exists."
            )

        if self.enabled:
            if not self.paybill_number:
                raise ValueError(
                    "paybill_number is required when M-Pesa Paybill is enabled."
                )
            if not self.account_reference_template:
                raise ValueError(
                    "account_reference_template is required when "
                    "M-Pesa Paybill is enabled."
                )

        return self


class MPesaTillCustomerMethod(StrictModel):
    enabled: bool = False
    till_number: Optional[str] = None
    business_name: Optional[str] = None
    verification_mode: VerificationMode = VerificationMode.MANUAL

    @model_validator(mode="after")
    def validate_till(self) -> "MPesaTillCustomerMethod":
        if self.verification_mode == VerificationMode.AUTOMATIC:
            raise ValueError(
                "Till payments cannot use automatic verification until a "
                "verified callback or transaction-query integration exists."
            )

        if self.enabled and not self.till_number:
            raise ValueError(
                "till_number is required when M-Pesa Till is enabled."
            )

        return self


class BankTransferCustomerMethod(StrictModel):
    enabled: bool = False
    bank_name: Optional[str] = None
    branch: Optional[str] = None
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    verification_mode: VerificationMode = VerificationMode.MANUAL

    @model_validator(mode="after")
    def validate_bank_transfer(self) -> "BankTransferCustomerMethod":
        if self.verification_mode == VerificationMode.AUTOMATIC:
            raise ValueError(
                "Bank transfer cannot use automatic verification without "
                "a supported bank-verification integration."
            )

        if self.enabled:
            missing = [
                field_name
                for field_name, value in {
                    "bank_name": self.bank_name,
                    "account_name": self.account_name,
                    "account_number": self.account_number,
                }.items()
                if not value
            ]

            if missing:
                raise ValueError(
                    "Missing required bank transfer fields: "
                    + ", ".join(missing)
                )

        return self


class CustomerPaymentMethods(StrictModel):
    paystack: PaystackCustomerMethod = Field(
        default_factory=PaystackCustomerMethod
    )
    mpesa_paybill: MPesaPaybillCustomerMethod = Field(
        default_factory=MPesaPaybillCustomerMethod
    )
    mpesa_till: MPesaTillCustomerMethod = Field(
        default_factory=MPesaTillCustomerMethod
    )
    bank_transfer: BankTransferCustomerMethod = Field(
        default_factory=BankTransferCustomerMethod
    )

    def is_enabled(self, method: CustomerPaymentMethod) -> bool:
        return {
            CustomerPaymentMethod.PAYSTACK: self.paystack.enabled,
            CustomerPaymentMethod.MPESA_PAYBILL: self.mpesa_paybill.enabled,
            CustomerPaymentMethod.MPESA_TILL: self.mpesa_till.enabled,
            CustomerPaymentMethod.BANK_TRANSFER: self.bank_transfer.enabled,
        }[method]


class SettlementConfiguration(StrictModel):
    method: SettlementMethod = SettlementMethod.PAYSTACK_SUBACCOUNT

    paystack_subaccount_code: Optional[str] = None

    bank_name: Optional[str] = None
    bank_branch: Optional[str] = None
    bank_account_name: Optional[str] = None
    bank_account_number: Optional[str] = None

    paybill_number: Optional[str] = None
    till_number: Optional[str] = None

    @model_validator(mode="after")
    def validate_settlement(self) -> "SettlementConfiguration":
        if self.method == SettlementMethod.PAYSTACK_SUBACCOUNT:
            if not self.paystack_subaccount_code:
                raise ValueError(
                    "paystack_subaccount_code is required for "
                    "Paystack subaccount settlement."
                )

        elif self.method == SettlementMethod.DIRECT_PAYBILL:
            if not self.paybill_number:
                raise ValueError(
                    "paybill_number is required for direct Paybill settlement."
                )

        elif self.method == SettlementMethod.DIRECT_TILL:
            if not self.till_number:
                raise ValueError(
                    "till_number is required for direct Till settlement."
                )

        elif self.method == SettlementMethod.BANK_ACCOUNT:
            missing = [
                field_name
                for field_name, value in {
                    "bank_name": self.bank_name,
                    "bank_account_name": self.bank_account_name,
                    "bank_account_number": self.bank_account_number,
                }.items()
                if not value
            ]

            if missing:
                raise ValueError(
                    "Missing required settlement bank fields: "
                    + ", ".join(missing)
                )

        return self


class OwnerPaymentProfileBase(StrictModel):
    customer_payment_methods: CustomerPaymentMethods
    default_customer_method: CustomerPaymentMethod
    settlement: SettlementConfiguration
    status: PaymentProfileStatus = PaymentProfileStatus.DRAFT

    @model_validator(mode="after")
    def validate_profile(self) -> "OwnerPaymentProfileBase":
        if not self.customer_payment_methods.is_enabled(
            self.default_customer_method
        ):
            raise ValueError(
                "default_customer_method must reference an enabled "
                "customer payment method."
            )

        if (
            self.settlement.method == SettlementMethod.DIRECT_PAYBILL
            and not self.customer_payment_methods.mpesa_paybill.enabled
        ):
            raise ValueError(
                "Direct Paybill settlement requires M-Pesa Paybill "
                "to be enabled."
            )

        if (
            self.settlement.method == SettlementMethod.DIRECT_TILL
            and not self.customer_payment_methods.mpesa_till.enabled
        ):
            raise ValueError(
                "Direct Till settlement requires M-Pesa Till to be enabled."
            )

        if (
            self.settlement.method == SettlementMethod.BANK_ACCOUNT
            and not self.customer_payment_methods.bank_transfer.enabled
        ):
            raise ValueError(
                "Bank account settlement requires bank transfer "
                "to be enabled."
            )

        return self


class OwnerPaymentProfileCreate(OwnerPaymentProfileBase):
    owner_id: str


class OwnerPaymentProfileUpdate(StrictModel):
    customer_payment_methods: Optional[CustomerPaymentMethods] = None
    default_customer_method: Optional[CustomerPaymentMethod] = None
    settlement: Optional[SettlementConfiguration] = None
    status: Optional[PaymentProfileStatus] = None


class OwnerPaymentProfile(OwnerPaymentProfileBase):
    id: str
    owner_id: str
    schema_version: str = "1.0"
    created_at: datetime
    updated_at: datetime


class PublicPaystackCustomerMethod(StrictModel):
    enabled: bool
    checkout_mode: str
    verification_mode: VerificationMode


class PublicMPesaPaybillCustomerMethod(StrictModel):
    enabled: bool
    paybill_number_masked: Optional[str] = None
    business_name: Optional[str] = None
    account_reference_template: Optional[str] = None
    verification_mode: VerificationMode


class PublicMPesaTillCustomerMethod(StrictModel):
    enabled: bool
    till_number_masked: Optional[str] = None
    business_name: Optional[str] = None
    verification_mode: VerificationMode


class PublicBankTransferCustomerMethod(StrictModel):
    enabled: bool
    bank_name: Optional[str] = None
    branch: Optional[str] = None
    account_name: Optional[str] = None
    account_number_masked: Optional[str] = None
    verification_mode: VerificationMode


class PublicCustomerPaymentMethods(StrictModel):
    paystack: PublicPaystackCustomerMethod
    mpesa_paybill: PublicMPesaPaybillCustomerMethod
    mpesa_till: PublicMPesaTillCustomerMethod
    bank_transfer: PublicBankTransferCustomerMethod


class PublicSettlementConfiguration(StrictModel):
    method: SettlementMethod
    paystack_subaccount_masked: Optional[str] = None
    bank_name: Optional[str] = None
    bank_branch: Optional[str] = None
    bank_account_name: Optional[str] = None
    bank_account_number_masked: Optional[str] = None
    paybill_number_masked: Optional[str] = None
    till_number_masked: Optional[str] = None


class OwnerPaymentProfileResponse(StrictModel):
    id: str
    owner_id: str
    schema_version: str
    customer_payment_methods: PublicCustomerPaymentMethods
    default_customer_method: CustomerPaymentMethod
    settlement: PublicSettlementConfiguration
    status: PaymentProfileStatus
    created_at: datetime
    updated_at: datetime
