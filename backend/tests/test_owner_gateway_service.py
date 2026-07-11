import asyncio
from copy import deepcopy
from datetime import datetime, timezone

import pytest

from backend.schemas.owner_gateway import (
    GatewayVerificationStatus,
    MPesaDarajaGatewayConfiguration,
    OwnerGatewayProfileCreate,
    OwnerGatewayProfileUpdate,
    OwnerGatewayStatus,
    PaystackGatewayConfiguration,
)
from backend.services.owner_gateway.repository import (
    OwnerGatewayAlreadyExists,
    OwnerGatewayNotFound,
    OwnerGatewayRepository,
)
from backend.services.owner_gateway.service import OwnerGatewayService


class FakeInsertResult:
    inserted_id = "fake-id"


class FakeUpdateResult:
    modified_count = 1


class FakeCollection:
    def __init__(self):
        self.documents = []
        self.indexes = []

    async def create_index(self, field, **kwargs):
        self.indexes.append((field, kwargs))
        return kwargs.get("name")

    async def find_one(self, query, projection=None):
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                result = deepcopy(document)
                result.pop("_id", None)
                return result
        return None

    async def insert_one(self, document):
        self.documents.append(deepcopy(document))
        return FakeInsertResult()

    async def update_one(self, query, operation):
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                document.update(deepcopy(operation["$set"]))
                return FakeUpdateResult()
        return FakeUpdateResult()


@pytest.fixture
def collection():
    return FakeCollection()


@pytest.fixture
def repository(collection):
    return OwnerGatewayRepository(collection)


@pytest.fixture
def service(repository):
    return OwnerGatewayService(repository)


def paystack_request():
    return OwnerGatewayProfileCreate(
        owner_id="owner-1",
        configuration=PaystackGatewayConfiguration(
            business_name="Owner Business",
            contact_email="owner@example.com",
            contact_phone="254700123456",
            uses_caiwave_platform_account=True,
        ),
    )


def test_repository_creates_unique_indexes(repository, collection):
    async def scenario():
        await repository.ensure_indexes()

        names = [
            options["name"]
            for _, options in collection.indexes
        ]

        assert "uniq_owner_gateway_owner_id" in names
        assert "uniq_owner_gateway_id" in names
        assert all(
            options["unique"] is True
            for _, options in collection.indexes
        )

    asyncio.run(scenario())


def test_service_creates_and_reads_profile(service):
    async def scenario():
        created = await service.create_profile(paystack_request())
        loaded = await service.get_profile("owner-1")

        assert created.id
        assert loaded.id == created.id
        assert loaded.owner_id == "owner-1"
        assert loaded.configuration.gateway == "paystack"

    asyncio.run(scenario())


def test_duplicate_owner_gateway_is_rejected(service):
    async def scenario():
        await service.create_profile(paystack_request())

        with pytest.raises(OwnerGatewayAlreadyExists):
            await service.create_profile(paystack_request())

    asyncio.run(scenario())


def test_missing_gateway_raises_not_found(service):
    async def scenario():
        with pytest.raises(OwnerGatewayNotFound):
            await service.get_profile("missing-owner")

    asyncio.run(scenario())


def test_update_preserves_identity(service):
    async def scenario():
        created = await service.create_profile(paystack_request())

        updated = await service.update_profile(
            "owner-1",
            OwnerGatewayProfileUpdate(
                verification_status=(
                    GatewayVerificationStatus.PENDING
                ),
                verification_message="Verification requested.",
            ),
        )

        assert updated.id == created.id
        assert updated.owner_id == created.owner_id
        assert updated.created_at == created.created_at
        assert (
            updated.verification_status
            == GatewayVerificationStatus.PENDING
        )
        assert updated.updated_at >= created.updated_at

    asyncio.run(scenario())


def test_active_update_requires_verified_gateway(service):
    async def scenario():
        await service.create_profile(paystack_request())

        with pytest.raises(
            ValueError,
            match="cannot be active until it is verified",
        ):
            await service.update_profile(
                "owner-1",
                OwnerGatewayProfileUpdate(
                    status=OwnerGatewayStatus.ACTIVE,
                ),
            )

    asyncio.run(scenario())


def test_verified_active_update_is_valid(service):
    async def scenario():
        await service.create_profile(paystack_request())
        now = datetime.now(timezone.utc)

        updated = await service.update_profile(
            "owner-1",
            OwnerGatewayProfileUpdate(
                status=OwnerGatewayStatus.ACTIVE,
                verification_status=(
                    GatewayVerificationStatus.VERIFIED
                ),
                last_verified_at=now,
            ),
        )

        assert updated.status == OwnerGatewayStatus.ACTIVE
        assert (
            updated.verification_status
            == GatewayVerificationStatus.VERIFIED
        )

    asyncio.run(scenario())


def test_public_paystack_response_masks_phone(service):
    async def scenario():
        created = await service.create_profile(paystack_request())
        public = service.to_public_response(created)

        assert public.configuration.gateway.value == "paystack"
        assert (
            public.configuration.contact_phone_masked
            == "********3456"
        )
        assert public.configuration.credentials_configured is True

    asyncio.run(scenario())


def test_public_daraja_response_never_exposes_secret_refs(service):
    async def scenario():
        request = OwnerGatewayProfileCreate(
            owner_id="owner-daraja",
            configuration=MPesaDarajaGatewayConfiguration(
                business_name="Owner Business",
                shortcode="123456",
                shortcode_type="paybill",
                consumer_key_ref="secret://daraja/key",
                consumer_secret_ref="secret://daraja/secret",
                passkey_ref="secret://daraja/passkey",
                callback_url=(
                    "https://www.caiwave.com/"
                    "api/payments/daraja/callback"
                ),
            ),
        )

        created = await service.create_profile(request)
        public = service.to_public_response(created)
        payload = public.model_dump_json()

        assert public.configuration.credentials_configured is True
        assert "secret://daraja/key" not in payload
        assert "secret://daraja/secret" not in payload
        assert "secret://daraja/passkey" not in payload

    asyncio.run(scenario())
