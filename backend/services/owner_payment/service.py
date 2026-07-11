"""
Business logic for Owner Payment Engine v1.

This service:
- validates profile contracts;
- enforces one profile per owner;
- masks sensitive values for API responses;
- preserves immutable profile identity fields;
- performs no payment execution.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
import uuid

from backend.schemas.owner_payment import (
    CustomerPaymentMethod,
    OwnerPaymentProfile,
    OwnerPaymentProfileCreate,
    OwnerPaymentProfileResponse,
    OwnerPaymentProfileUpdate,
    PublicBankTransferCustomerMethod,
    PublicCustomerPaymentMethods,
    PublicMPesaPaybillCustomerMethod,
    PublicMPesaTillCustomerMethod,
    PublicPaystackCustomerMethod,
    PublicSettlementConfiguration,
    mask_sensitive_value,
)
from backend.services.owner_payment.repository import (
    OwnerPaymentProfileNotFound,
    OwnerPaymentProfileRepository,
)


class OwnerPaymentProfileService:
    def __init__(self, repository: OwnerPaymentProfileRepository):
        self.repository = repository

    async def create_profile(
        self,
        request: OwnerPaymentProfileCreate,
    ) -> OwnerPaymentProfile:
        now = datetime.now(timezone.utc)

        profile = OwnerPaymentProfile(
            id=str(uuid.uuid4()),
            owner_id=request.owner_id,
            schema_version="1.0",
            customer_payment_methods=request.customer_payment_methods,
            default_customer_method=request.default_customer_method,
            settlement=request.settlement,
            status=request.status,
            created_at=now,
            updated_at=now,
        )

        created = await self.repository.create(
            profile.model_dump(mode="json")
        )
        return OwnerPaymentProfile.model_validate(created)

    async def get_profile(
        self,
        owner_id: str,
    ) -> OwnerPaymentProfile:
        document = await self.repository.get_by_owner_id(owner_id)
        if not document:
            raise OwnerPaymentProfileNotFound(
                f"Owner payment profile not found for owner {owner_id}."
            )

        return OwnerPaymentProfile.model_validate(document)

    async def update_profile(
        self,
        owner_id: str,
        request: OwnerPaymentProfileUpdate,
    ) -> OwnerPaymentProfile:
        current = await self.get_profile(owner_id)

        update_data = request.model_dump(
            mode="json",
            exclude_none=True,
        )

        merged_data = current.model_dump(mode="json")
        merged_data.update(update_data)
        merged_data["id"] = current.id
        merged_data["owner_id"] = current.owner_id
        merged_data["schema_version"] = current.schema_version
        merged_data["created_at"] = current.created_at
        merged_data["updated_at"] = datetime.now(timezone.utc)

        validated = OwnerPaymentProfile.model_validate(merged_data)

        mutable_updates: Dict[str, Any] = {
            "customer_payment_methods": validated.customer_payment_methods.model_dump(
                mode="json"
            ),
            "default_customer_method": validated.default_customer_method.value,
            "settlement": validated.settlement.model_dump(mode="json"),
            "status": validated.status.value,
            "updated_at": validated.updated_at.isoformat(),
        }

        updated = await self.repository.update_by_owner_id(
            owner_id,
            mutable_updates,
        )
        return OwnerPaymentProfile.model_validate(updated)

    async def get_public_profile(
        self,
        owner_id: str,
    ) -> OwnerPaymentProfileResponse:
        profile = await self.get_profile(owner_id)
        return self.to_public_response(profile)

    def to_public_response(
        self,
        profile: OwnerPaymentProfile,
    ) -> OwnerPaymentProfileResponse:
        methods = profile.customer_payment_methods
        settlement = profile.settlement

        return OwnerPaymentProfileResponse(
            id=profile.id,
            owner_id=profile.owner_id,
            schema_version=profile.schema_version,
            customer_payment_methods=PublicCustomerPaymentMethods(
                paystack=PublicPaystackCustomerMethod(
                    enabled=methods.paystack.enabled,
                    checkout_mode=methods.paystack.checkout_mode,
                    verification_mode=methods.paystack.verification_mode,
                ),
                mpesa_paybill=PublicMPesaPaybillCustomerMethod(
                    enabled=methods.mpesa_paybill.enabled,
                    paybill_number_masked=mask_sensitive_value(
                        methods.mpesa_paybill.paybill_number
                    ),
                    business_name=methods.mpesa_paybill.business_name,
                    account_reference_template=(
                        methods.mpesa_paybill.account_reference_template
                    ),
                    verification_mode=(
                        methods.mpesa_paybill.verification_mode
                    ),
                ),
                mpesa_till=PublicMPesaTillCustomerMethod(
                    enabled=methods.mpesa_till.enabled,
                    till_number_masked=mask_sensitive_value(
                        methods.mpesa_till.till_number
                    ),
                    business_name=methods.mpesa_till.business_name,
                    verification_mode=methods.mpesa_till.verification_mode,
                ),
                bank_transfer=PublicBankTransferCustomerMethod(
                    enabled=methods.bank_transfer.enabled,
                    bank_name=methods.bank_transfer.bank_name,
                    branch=methods.bank_transfer.branch,
                    account_name=methods.bank_transfer.account_name,
                    account_number_masked=mask_sensitive_value(
                        methods.bank_transfer.account_number
                    ),
                    verification_mode=(
                        methods.bank_transfer.verification_mode
                    ),
                ),
            ),
            default_customer_method=CustomerPaymentMethod(
                profile.default_customer_method
            ),
            settlement=PublicSettlementConfiguration(
                method=settlement.method,
                paystack_subaccount_masked=mask_sensitive_value(
                    settlement.paystack_subaccount_code
                ),
                bank_name=settlement.bank_name,
                bank_branch=settlement.bank_branch,
                bank_account_name=settlement.bank_account_name,
                bank_account_number_masked=mask_sensitive_value(
                    settlement.bank_account_number
                ),
                paybill_number_masked=mask_sensitive_value(
                    settlement.paybill_number
                ),
                till_number_masked=mask_sensitive_value(
                    settlement.till_number
                ),
            ),
            status=profile.status,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
