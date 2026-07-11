import asyncio
from copy import deepcopy

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.schemas.owner_payment import (
    CustomerPaymentMethod,
    CustomerPaymentMethods,
    PaystackCustomerMethod,
    PaymentProfileStatus,
    SettlementConfiguration,
    SettlementMethod,
)
from backend.services.owner_payment.router import (
    create_owner_payment_router,
)


class FakeInsertResult:
    inserted_id = "fake-id"


class FakeUpdateResult:
    modified_count = 1


class FakeDeleteResult:
    deleted_count = 0


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
        return FakeDeleteResult()


def owner_dependency():
    return {
        "id": "authenticated-owner",
        "role": "hotspot_owner",
    }


@pytest.fixture
def collection():
    return FakeCollection()


@pytest.fixture
def client(collection):
    app = FastAPI()

    router = create_owner_payment_router(
        collection=collection,
        owner_dependency=owner_dependency,
    )

    app.include_router(router, prefix="/api")

    with TestClient(app) as test_client:
        yield test_client


def create_payload(owner_id="body-owner"):
    return {
        "owner_id": owner_id,
        "customer_payment_methods": {
            "paystack": {
                "enabled": True,
                "checkout_mode": "hosted",
                "verification_mode": "automatic",
            },
            "mpesa_paybill": {
                "enabled": False,
                "paybill_number": None,
                "business_name": None,
                "account_reference_template": None,
                "verification_mode": "manual",
            },
            "mpesa_till": {
                "enabled": False,
                "till_number": None,
                "business_name": None,
                "verification_mode": "manual",
            },
            "bank_transfer": {
                "enabled": False,
                "bank_name": None,
                "branch": None,
                "account_name": None,
                "account_number": None,
                "verification_mode": "manual",
            },
        },
        "default_customer_method": "paystack",
        "settlement": {
            "method": "paystack_subaccount",
            "paystack_subaccount_code": "ACCT_owner123456",
            "bank_name": None,
            "bank_branch": None,
            "bank_account_name": None,
            "bank_account_number": None,
            "paybill_number": None,
            "till_number": None,
        },
        "status": "active",
    }


def test_get_missing_profile_returns_404(client):
    response = client.get("/api/owner/payment-profile")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_profile_uses_authenticated_owner_not_body_owner(
    client,
    collection,
):
    response = client.post(
        "/api/owner/payment-profile",
        json=create_payload(owner_id="attacker-controlled-owner"),
    )

    assert response.status_code == 201
    body = response.json()

    assert body["owner_id"] == "authenticated-owner"
    assert collection.documents[0]["owner_id"] == "authenticated-owner"
    assert body["owner_id"] != "attacker-controlled-owner"


def test_create_profile_masks_sensitive_settlement_value(client):
    response = client.post(
        "/api/owner/payment-profile",
        json=create_payload(),
    )

    assert response.status_code == 201
    body = response.json()

    masked = body["settlement"]["paystack_subaccount_masked"]

    assert masked.endswith("3456")
    assert "ACCT_owner123456" not in masked


def test_duplicate_profile_returns_409(client):
    first = client.post(
        "/api/owner/payment-profile",
        json=create_payload(),
    )
    second = client.post(
        "/api/owner/payment-profile",
        json=create_payload(),
    )

    assert first.status_code == 201
    assert second.status_code == 409


def test_get_profile_returns_authenticated_owner_profile(client):
    created = client.post(
        "/api/owner/payment-profile",
        json=create_payload(),
    )
    response = client.get("/api/owner/payment-profile")

    assert created.status_code == 201
    assert response.status_code == 200
    assert response.json()["owner_id"] == "authenticated-owner"


def test_update_profile_changes_mutable_fields(client):
    created = client.post(
        "/api/owner/payment-profile",
        json=create_payload(),
    )

    response = client.put(
        "/api/owner/payment-profile",
        json={"status": PaymentProfileStatus.SUSPENDED.value},
    )

    assert created.status_code == 201
    assert response.status_code == 200
    assert response.json()["status"] == "suspended"
    assert response.json()["owner_id"] == "authenticated-owner"


def test_update_missing_profile_returns_404(client):
    response = client.put(
        "/api/owner/payment-profile",
        json={"status": "suspended"},
    )

    assert response.status_code == 404


def test_invalid_profile_returns_422(client):
    payload = create_payload()
    payload["customer_payment_methods"]["paystack"]["enabled"] = False

    response = client.post(
        "/api/owner/payment-profile",
        json=payload,
    )

    assert response.status_code == 422


def test_owner_profile_response_contract_contains_expected_fields(client):
    response = client.post(
        "/api/owner/payment-profile",
        json=create_payload(),
    )

    assert response.status_code == 201

    body = response.json()

    assert set(body) == {
        "id",
        "owner_id",
        "schema_version",
        "customer_payment_methods",
        "default_customer_method",
        "settlement",
        "status",
        "created_at",
        "updated_at",
    }
