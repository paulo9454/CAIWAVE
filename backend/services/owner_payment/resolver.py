"""
Payment destination resolution for CAIWAVE.

This module determines who should receive a payment and which owner
settlement configuration applies. It performs no payment execution,
database writes, HTTP calls, or route registration.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict

from backend.schemas.owner_payment import (
    CustomerPaymentMethod,
    OwnerPaymentProfile,
    PaymentProfileStatus,
    SettlementMethod,
    VerificationMode,
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PlatformPaymentType(str, Enum):
    WIFI_PACKAGE = "wifi_package"
    OWNER_SUBSCRIPTION = "owner_subscription"
    ADVERTISER_PACKAGE = "advertiser_package"


class PaymentDestination(str, Enum):
    CAIWAVE = "caiwave"
    HOTSPOT_OWNER = "hotspot_owner"


class PaymentResolutionError(Exception):
    """Base error for payment destination resolution."""


class OwnerPaymentProfileRequired(PaymentResolutionError):
    """Raised when an owner payment profile is required but unavailable."""


class OwnerPaymentProfileInactive(PaymentResolutionError):
    """Raised when the owner's payment profile is not active."""


class PaymentMethodUnavailable(PaymentResolutionError):
    """Raised when the selected owner payment method is unavailable."""


class AutomaticVerificationUnavailable(PaymentResolutionError):
    """Raised when automatic access requires an automatically verified method."""


class PaymentDestinationResolution(StrictModel):
    payment_type: PlatformPaymentType
    destination: PaymentDestination
    owner_id: Optional[str] = None
    customer_payment_method: Optional[CustomerPaymentMethod] = None
    settlement_method: Optional[SettlementMethod] = None
    verification_mode: Optional[VerificationMode] = None
    automatic_fulfilment_supported: bool
    reason: str


class OwnerPaymentResolver:
    """
    Resolve the recipient and applicable owner payment configuration.

    Platform revenue always resolves to CAIWAVE.

    WiFi package revenue resolves to the hotspot owner and therefore
    requires a valid active owner payment profile.
    """

    PLATFORM_PAYMENT_TYPES = {
        PlatformPaymentType.OWNER_SUBSCRIPTION,
        PlatformPaymentType.ADVERTISER_PACKAGE,
    }

    def resolve(
        self,
        payment_type: PlatformPaymentType,
        *,
        owner_id: Optional[str] = None,
        owner_profile: Optional[OwnerPaymentProfile] = None,
        require_automatic_fulfilment: bool = False,
    ) -> PaymentDestinationResolution:
        if payment_type in self.PLATFORM_PAYMENT_TYPES:
            return PaymentDestinationResolution(
                payment_type=payment_type,
                destination=PaymentDestination.CAIWAVE,
                automatic_fulfilment_supported=True,
                reason="Platform revenue is settled to the CAIWAVE account.",
            )

        if payment_type != PlatformPaymentType.WIFI_PACKAGE:
            raise PaymentResolutionError(
                f"Unsupported payment type: {payment_type}"
            )

        if not owner_id:
            raise OwnerPaymentProfileRequired(
                "WiFi package payments require a hotspot owner ID."
            )

        if owner_profile is None:
            raise OwnerPaymentProfileRequired(
                f"Owner payment profile is required for owner {owner_id}."
            )

        if owner_profile.owner_id != owner_id:
            raise OwnerPaymentProfileRequired(
                "Owner payment profile does not belong to the hotspot owner."
            )

        if owner_profile.status != PaymentProfileStatus.ACTIVE:
            raise OwnerPaymentProfileInactive(
                f"Owner payment profile is {owner_profile.status.value}."
            )

        method = owner_profile.default_customer_method
        methods = owner_profile.customer_payment_methods

        if not methods.is_enabled(method):
            raise PaymentMethodUnavailable(
                f"Owner payment method {method.value} is not enabled."
            )

        verification_mode = self._verification_mode(
            owner_profile,
            method,
        )

        automatic_supported = (
            verification_mode == VerificationMode.AUTOMATIC
        )

        if require_automatic_fulfilment and not automatic_supported:
            raise AutomaticVerificationUnavailable(
                f"Payment method {method.value} cannot automatically "
                "verify payment or grant hotspot access."
            )

        return PaymentDestinationResolution(
            payment_type=payment_type,
            destination=PaymentDestination.HOTSPOT_OWNER,
            owner_id=owner_id,
            customer_payment_method=method,
            settlement_method=owner_profile.settlement.method,
            verification_mode=verification_mode,
            automatic_fulfilment_supported=automatic_supported,
            reason=(
                "WiFi package revenue is routed according to the active "
                "hotspot owner payment profile."
            ),
        )

    @staticmethod
    def _verification_mode(
        profile: OwnerPaymentProfile,
        method: CustomerPaymentMethod,
    ) -> VerificationMode:
        methods = profile.customer_payment_methods

        mapping = {
            CustomerPaymentMethod.PAYSTACK:
                methods.paystack.verification_mode,
            CustomerPaymentMethod.MPESA_PAYBILL:
                methods.mpesa_paybill.verification_mode,
            CustomerPaymentMethod.MPESA_TILL:
                methods.mpesa_till.verification_mode,
            CustomerPaymentMethod.BANK_TRANSFER:
                methods.bank_transfer.verification_mode,
        }

        return mapping[method]
