import asyncio
from copy import deepcopy

import pytest

from backend.schemas.owner_payment import (
    CustomerPaymentMethod,
    CustomerPaymentMethods,
    MPesaPaybillCustomerMethod,
    OwnerPaymentProfileCreate,
    OwnerPaymentProfileUpdate,
    PaymentProfileStatus,
    PaystackCustomerMethod,
    SettlementConfiguration,
    SettlementMethod,
)
from backend.services.owner_payment.repository import (
    OwnerPaymentProfileAlreadyExists,
    OwnerPaymentProfileNotFound,
    OwnerPaymentProfileRepository,
)
from backend.services.owner_payment.service import OwnerPaymentProfileService


class FakeInsertResult:
    inserted_id = "fake-id"


class FakeUpdateResult:
    modified_count = 1


class FakeDeleteResult:
    def __init__(self, deleted_count):
        self.deleted_count = deleted_count


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

    async def delete_one(self, query):
        before = len(self.documents)
        self.documents = [
            document
            for document in self.documents
            if not all(
                document.get(key) == value
                for key, value in query.items()
            )
        ]
        return FakeDeleteResult(before - len(self.documents))


@pytest.fixture
def collection():
    return FakeCollection()


@pytest.fixture
def repository(collection):
    return OwnerPaymentProfileRepository(collection)


@pytest.fixture
def service(repository):
    return OwnerPaymentProfileService(repository)


def paystack_create_request():
    return OwnerPaymentProfileCreate(
        owner_id="owner-1",
        customer_payment_methods=CustomerPaymentMethods(
            paystack=PaystackCustomerMethod(enabled=True),
        ),
        default_customer_method=CustomerPaymentMethod.PAYSTACK,
        settlement=SettlementConfiguration(
            method=SettlementMethod.PAYSTACK_SUBACCOUNT,
            paystack_subaccount_code="ACCT_owner123456",
        ),
        status=PaymentProfileStatus.ACTIVE,
    )


def test_repository_creates_required_indexes(repository, collection):
    async def scenario():
        await repository.ensure_indexes()

        names = [options["name"] for _, options in collection.indexes]

        assert "uniq_owner_payment_profile_owner_id" in names
        assert "uniq_owner_payment_profile_id" in names
        assert all(
            options["unique"] is True
            for _, options in collection.indexes
        )

    asyncio.run(scenario())


def test_service_creates_and_reads_profile(service):
    async def scenario():
        created = await service.create_profile(paystack_create_request())
        loaded = await service.get_profile("owner-1")

        assert created.id
        assert loaded.id == created.id
        assert loaded.owner_id == "owner-1"
        assert loaded.status == PaymentProfileStatus.ACTIVE

    asyncio.run(scenario())


def test_duplicate_owner_profile_is_rejected(service):
    async def scenario():
        await service.create_profile(paystack_create_request())

        with pytest.raises(OwnerPaymentProfileAlreadyExists):
            await service.create_profile(paystack_create_request())

    asyncio.run(scenario())


def test_missing_profile_raises_not_found(service):
    async def scenario():
        with pytest.raises(OwnerPaymentProfileNotFound):
            await service.get_profile("missing-owner")

    asyncio.run(scenario())


def test_profile_update_preserves_identity(service):
    async def scenario():
        created = await service.create_profile(paystack_create_request())

        updated = await service.update_profile(
            "owner-1",
            OwnerPaymentProfileUpdate(
                status=PaymentProfileStatus.SUSPENDED,
            ),
        )

        assert updated.id == created.id
        assert updated.owner_id == created.owner_id
        assert updated.created_at == created.created_at
        assert updated.status == PaymentProfileStatus.SUSPENDED
        assert updated.updated_at >= created.updated_at

    asyncio.run(scenario())


def test_profile_update_revalidates_full_profile(service):
    async def scenario():
        await service.create_profile(paystack_create_request())

        with pytest.raises(
            ValueError,
            match="default_customer_method must reference an enabled",
        ):
            await service.update_profile(
                "owner-1",
                OwnerPaymentProfileUpdate(
                    customer_payment_methods=CustomerPaymentMethods(),
                ),
            )

    asyncio.run(scenario())


def test_public_response_masks_sensitive_values(service):
    async def scenario():
        created = await service.create_profile(paystack_create_request())
        public = service.to_public_response(created)

        assert public.settlement.paystack_subaccount_masked
        assert "ACCT_owner123456" not in (
            public.settlement.paystack_subaccount_masked
        )
        assert public.settlement.paystack_subaccount_masked.endswith("3456")

    asyncio.run(scenario())


def test_valid_paybill_profile_can_be_created(service):
    async def scenario():
        request = OwnerPaymentProfileCreate(
            owner_id="owner-paybill",
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

        created = await service.create_profile(request)
        public = service.to_public_response(created)

        assert created.owner_id == "owner-paybill"
        assert public.customer_payment_methods.mpesa_paybill.enabled is True
        assert (
            public.customer_payment_methods.mpesa_paybill.paybill_number_masked
            == "**3456"
        )

    asyncio.run(scenario())


def test_repository_delete_profile(repository, service):
    async def scenario():
        await service.create_profile(paystack_create_request())

        deleted = await repository.delete_by_owner_id("owner-1")
        loaded = await repository.get_by_owner_id("owner-1")

        assert deleted is True
        assert loaded is None

    asyncio.run(scenario())
