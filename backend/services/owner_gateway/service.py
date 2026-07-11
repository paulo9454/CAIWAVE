"""
Business logic for owner automated payment gateways.

This service:
- validates one gateway per owner;
- preserves immutable profile identity;
- masks sensitive account identifiers;
- never returns credential references;
- performs no external gateway calls.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
import uuid

from backend.schemas.owner_gateway import (
    BankPaybillAPIGatewayConfiguration,
    KopoKopoGatewayConfiguration,
    MPesaDarajaGatewayConfiguration,
    OwnerGatewayProfile,
    OwnerGatewayProfileCreate,
    OwnerGatewayProfileResponse,
    OwnerGatewayProfileUpdate,
    OwnerGatewayType,
    PaystackGatewayConfiguration,
    PublicOwnerGatewayConfiguration,
    mask_value,
)
from backend.services.owner_gateway.repository import (
    OwnerGatewayNotFound,
    OwnerGatewayRepository,
)


class OwnerGatewayService:
    def __init__(self, repository: OwnerGatewayRepository):
        self.repository = repository

    async def create_profile(
        self,
        request: OwnerGatewayProfileCreate,
    ) -> OwnerGatewayProfile:
        now = datetime.now(timezone.utc)

        profile = OwnerGatewayProfile(
            id=str(uuid.uuid4()),
            owner_id=request.owner_id,
            schema_version="1.0",
            configuration=request.configuration,
            status=request.status,
            verification_status=request.verification_status,
            verification_message=request.verification_message,
            last_verified_at=request.last_verified_at,
            created_at=now,
            updated_at=now,
        )

        created = await self.repository.create(
            profile.model_dump(mode="json")
        )

        return OwnerGatewayProfile.model_validate(created)

    async def get_profile(
        self,
        owner_id: str,
    ) -> OwnerGatewayProfile:
        document = await self.repository.get_by_owner_id(owner_id)

        if not document:
            raise OwnerGatewayNotFound(
                f"Owner gateway profile not found for owner {owner_id}."
            )

        return OwnerGatewayProfile.model_validate(document)

    async def update_profile(
        self,
        owner_id: str,
        request: OwnerGatewayProfileUpdate,
    ) -> OwnerGatewayProfile:
        current = await self.get_profile(owner_id)

        update_data = request.model_dump(
            mode="json",
            exclude_none=True,
        )

        merged = current.model_dump(mode="json")
        merged.update(update_data)

        merged["id"] = current.id
        merged["owner_id"] = current.owner_id
        merged["schema_version"] = current.schema_version
        merged["created_at"] = current.created_at
        merged["updated_at"] = datetime.now(timezone.utc)

        validated = OwnerGatewayProfile.model_validate(merged)

        updates: Dict[str, Any] = {
            "configuration": validated.configuration.model_dump(
                mode="json"
            ),
            "status": validated.status.value,
            "verification_status": validated.verification_status.value,
            "verification_message": validated.verification_message,
            "last_verified_at": (
                validated.last_verified_at.isoformat()
                if validated.last_verified_at
                else None
            ),
            "updated_at": validated.updated_at.isoformat(),
        }

        updated = await self.repository.update_by_owner_id(
            owner_id,
            updates,
        )

        return OwnerGatewayProfile.model_validate(updated)

    async def get_public_profile(
        self,
        owner_id: str,
    ) -> OwnerGatewayProfileResponse:
        profile = await self.get_profile(owner_id)
        return self.to_public_response(profile)

    def to_public_response(
        self,
        profile: OwnerGatewayProfile,
    ) -> OwnerGatewayProfileResponse:
        config = profile.configuration

        public_config = self._public_configuration(config)

        return OwnerGatewayProfileResponse(
            id=profile.id,
            owner_id=profile.owner_id,
            schema_version=profile.schema_version,
            configuration=public_config,
            status=profile.status,
            verification_status=profile.verification_status,
            verification_message=profile.verification_message,
            last_verified_at=profile.last_verified_at,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    @staticmethod
    def _public_configuration(
        config: Any,
    ) -> PublicOwnerGatewayConfiguration:
        if isinstance(config, PaystackGatewayConfiguration):
            return PublicOwnerGatewayConfiguration(
                gateway=OwnerGatewayType.PAYSTACK,
                business_name=config.business_name,
                contact_email=str(config.contact_email),
                contact_phone_masked=mask_value(config.contact_phone),
                settlement_account_last4=(
                    config.settlement_account_last4
                ),
                uses_caiwave_platform_account=(
                    config.uses_caiwave_platform_account
                ),
                credentials_configured=True,
            )

        if isinstance(config, MPesaDarajaGatewayConfiguration):
            return PublicOwnerGatewayConfiguration(
                gateway=OwnerGatewayType.MPESA_DARAJA,
                business_name=config.business_name,
                shortcode_masked=mask_value(config.shortcode),
                credentials_configured=all([
                    config.consumer_key_ref,
                    config.consumer_secret_ref,
                    config.passkey_ref,
                ]),
                callback_url=config.callback_url,
            )

        if isinstance(config, KopoKopoGatewayConfiguration):
            return PublicOwnerGatewayConfiguration(
                gateway=OwnerGatewayType.KOPOKOPO,
                business_name=config.business_name,
                till_number_masked=mask_value(config.till_number),
                credentials_configured=all([
                    config.client_id_ref,
                    config.client_secret_ref,
                ]),
                callback_url=config.callback_url,
            )

        if isinstance(config, BankPaybillAPIGatewayConfiguration):
            return PublicOwnerGatewayConfiguration(
                gateway=OwnerGatewayType.BANK_PAYBILL_API,
                business_name=config.business_name,
                provider_name=config.provider_name,
                paybill_number_masked=mask_value(
                    config.paybill_number
                ),
                receiving_account_masked=mask_value(
                    config.receiving_account_number
                ),
                credentials_configured=all([
                    config.client_id_ref,
                    config.client_secret_ref,
                    config.callback_signing_secret_ref,
                ]),
                callback_url=config.callback_url,
            )

        raise TypeError(
            f"Unsupported owner gateway configuration: {type(config)!r}"
        )
