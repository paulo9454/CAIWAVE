from copy import deepcopy

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.services.owner_gateway.router import (
    create_owner_gateway_router,
)


class FakeInsertResult:
    inserted_id = "fake-id"


class FakeUpdateResult:
    modified_count = 1


class FakeCollection:
    def __init__(self):
        self.documents = []

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

    app.include_router(
        create_owner_gateway_router(
            collection=collection,
            owner_dependency=owner_dependency,
        ),
        prefix="/api",
    )

    with TestClient(app) as test_client:
        yield test_client


def paystack_payload():
    return {
        "configuration": {
            "gateway": "paystack",
            "business_name": "Owner Business",
            "contact_email": "owner@example.com",
            "contact_phone": "254700123456",
            "uses_caiwave_platform_account": True,
        }
    }


def test_missing_gateway_returns_404(client):
    response = client.get("/api/owner/payment-gateway")

    assert response.status_code == 404


def test_owner_can_create_draft_gateway(client, collection):
    response = client.post(
        "/api/owner/payment-gateway",
        json=paystack_payload(),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["owner_id"] == "authenticated-owner"
    assert body["status"] == "draft"
    assert body["verification_status"] == "not_verified"
    assert collection.documents[0]["owner_id"] == "authenticated-owner"


def test_owner_cannot_submit_owner_id(client):
    payload = paystack_payload()
    payload["owner_id"] = "attacker-owner"

    response = client.post(
        "/api/owner/payment-gateway",
        json=payload,
    )

    assert response.status_code == 422


def test_owner_cannot_self_activate_gateway(client):
    payload = paystack_payload()
    payload["status"] = "active"
    payload["verification_status"] = "verified"

    response = client.post(
        "/api/owner/payment-gateway",
        json=payload,
    )

    assert response.status_code == 422


def test_duplicate_gateway_returns_409(client):
    first = client.post(
        "/api/owner/payment-gateway",
        json=paystack_payload(),
    )
    second = client.post(
        "/api/owner/payment-gateway",
        json=paystack_payload(),
    )

    assert first.status_code == 201
    assert second.status_code == 409


def test_public_response_masks_phone(client):
    response = client.post(
        "/api/owner/payment-gateway",
        json=paystack_payload(),
    )

    assert response.status_code == 201

    config = response.json()["configuration"]

    assert config["contact_phone_masked"] == "********3456"
    assert "254700123456" not in str(response.json())


def test_owner_can_suspend_gateway(client):
    created = client.post(
        "/api/owner/payment-gateway",
        json=paystack_payload(),
    )

    response = client.put(
        "/api/owner/payment-gateway",
        json={"status": "suspended"},
    )

    assert created.status_code == 201
    assert response.status_code == 200
    assert response.json()["status"] == "suspended"


def test_owner_cannot_set_active_status_on_update(client):
    client.post(
        "/api/owner/payment-gateway",
        json=paystack_payload(),
    )

    response = client.put(
        "/api/owner/payment-gateway",
        json={"status": "active"},
    )

    assert response.status_code == 422


def test_configuration_change_resets_verification(client):
    client.post(
        "/api/owner/payment-gateway",
        json=paystack_payload(),
    )

    payload = paystack_payload()
    payload["configuration"]["business_name"] = "Updated Business"

    response = client.put(
        "/api/owner/payment-gateway",
        json=payload,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "draft"
    assert body["verification_status"] == "not_verified"
    assert "requires verification" in body["verification_message"]


def test_update_missing_gateway_returns_404(client):
    response = client.put(
        "/api/owner/payment-gateway",
        json={"status": "suspended"},
    )

    assert response.status_code == 404
