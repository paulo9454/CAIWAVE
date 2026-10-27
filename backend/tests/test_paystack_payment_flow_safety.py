from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import server


class FakeCollection:
    def __init__(self, documents=None):
        self.documents = [dict(doc) for doc in (documents or [])]

    async def find_one(self, query, projection=None):
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                return dict(document)
        return None

    async def insert_one(self, document):
        self.documents.append(dict(document))
        return SimpleNamespace(inserted_id=document.get("id", "test-id"))

    async def update_one(self, query, update):
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                document.update(update.get("$set", {}))
                return SimpleNamespace(matched_count=1)
        return SimpleNamespace(matched_count=0)


class FakePaystackService:
    def __init__(self):
        self.charge_requests = []
        self.initialize_requests = []

    def is_configured(self):
        return True

    async def charge_mobile_money(self, request):
        self.charge_requests.append(request)
        return {
            "status": True,
            "message": "Mock payment accepted",
            "data": {"reference": "paystack-test-reference"},
        }

    async def initialize_transaction(self, request):
        self.initialize_requests.append(request)
        return {
            "status": True,
            "data": {
                "authorization_url": "https://example.invalid/checkout",
                "access_code": "test-access-code",
            },
        }


def make_app(monkeypatch, db, payment_service, user=None):
    monkeypatch.setattr(server, "db", db)
    monkeypatch.setattr(server, "paystack_service", payment_service)

    app = FastAPI()
    app.include_router(server.paystack_router, prefix="/api")

    if user is not None:
        async def fake_current_user():
            return user

        app.dependency_overrides[server.get_current_user] = fake_current_user

    return app


def test_paystack_wifi_payment_preserves_split_and_transaction_flow(monkeypatch):
    owner = {
        "id": "owner-test-1",
        "email": "owner@example.com",
        "paystack_subaccount_code": "ACCT_TEST_SUBACCOUNT",
    }
    db = SimpleNamespace(
        hotspots=FakeCollection([{
            "id": "hotspot-test-1",
            "owner_id": owner["id"],
            "status": server.HotspotStatus.ACTIVE.value,
        }]),
        packages=FakeCollection([{
            "id": "package-test-1",
            "is_active": True,
            "price": 60,
            "name": "One hour",
            "duration_minutes": 60,
        }]),
        users=FakeCollection([owner]),
        paystack_transactions=FakeCollection(),
    )
    payment_service = FakePaystackService()
    app = make_app(monkeypatch, db, payment_service)

    with TestClient(app) as client:
        response = client.post(
            "/api/paystack/client/pay-wifi",
            json={
                "hotspot_id": "hotspot-test-1",
                "package_id": "package-test-1",
                "phone_number": "0712345678",
                "email": "customer@example.com",
            },
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert body["amount"] == 60
    assert body["package_name"] == "One hour"
    assert body["duration"] == 60

    assert len(payment_service.charge_requests) == 1
    charge = payment_service.charge_requests[0]
    assert charge.phone_number == "254712345678"
    assert charge.subaccount_code == "ACCT_TEST_SUBACCOUNT"
    assert charge.provider == "mpesa"
    assert charge.metadata["payment_type"] == "wifi"
    assert charge.metadata["hotspot_id"] == "hotspot-test-1"

    transactions = db.paystack_transactions.documents
    assert len(transactions) == 1
    transaction = transactions[0]
    assert transaction["provider"] == "paystack"
    assert transaction["payment_type"] == "wifi"
    assert transaction["amount"] == 60
    assert transaction["status"] == "pending_confirmation"
    assert transaction["paystack_reference"] == "paystack-test-reference"
    assert transaction["subaccount_code"] == "ACCT_TEST_SUBACCOUNT"


def test_paystack_owner_subscription_preserves_invoice_and_payment_flow(
    monkeypatch,
):
    owner_id = "owner-subscription-test"
    owner = {
        "id": owner_id,
        "email": "subscription@example.com",
    }
    invoice = {
        "id": "invoice-test-1",
        "owner_id": owner_id,
        "amount": 500.0,
        "status": server.InvoiceStatus.UNPAID.value,
    }
    db = SimpleNamespace(
        users=FakeCollection([owner]),
        invoices=FakeCollection([invoice]),
        paystack_transactions=FakeCollection(),
    )
    payment_service = FakePaystackService()
    app = make_app(
        monkeypatch,
        db,
        payment_service,
        user={
            "id": owner_id,
            "role": server.UserRole.HOTSPOT_OWNER.value,
            "email": owner["email"],
        },
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/paystack/owner/pay-subscription",
            json={
                "phone_number": "0712345678",
                "invoice_id": "invoice-test-1",
            },
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert body["amount"] == 500.0

    assert len(payment_service.charge_requests) == 1
    charge = payment_service.charge_requests[0]
    assert charge.phone_number == "254712345678"
    assert charge.metadata["payment_type"] == "subscription"
    assert charge.metadata["invoice_id"] == "invoice-test-1"
    assert charge.metadata["owner_id"] == owner_id

    transactions = db.paystack_transactions.documents
    assert len(transactions) == 1
    transaction = transactions[0]
    assert transaction["provider"] == "paystack"
    assert transaction["payment_type"] == "subscription"
    assert transaction["invoice_id"] == "invoice-test-1"
    assert transaction["owner_id"] == owner_id
    assert transaction["status"] == "pending_confirmation"
    assert transaction["paystack_reference"] == "paystack-test-reference"


def test_paystack_initialize_preserves_checkout_and_transaction_flow(monkeypatch):
    db = SimpleNamespace(paystack_transactions=FakeCollection())
    payment_service = FakePaystackService()
    app = make_app(monkeypatch, db, payment_service)

    with TestClient(app) as client:
        response = client.post(
            "/api/paystack/initialize",
            json={
                "email": "customer@example.com",
                "phone_number": "0712345678",
                "amount": 60,
                "payment_type": "wifi",
                "reference_id": "hotspot-test-1",
                "description": "Wi-Fi package test",
            },
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert body["authorization_url"] == "https://example.invalid/checkout"
    assert body["access_code"] == "test-access-code"

    assert len(payment_service.initialize_requests) == 1
    request = payment_service.initialize_requests[0]
    assert request.email == "customer@example.com"
    assert request.amount == 60
    assert request.metadata["payment_type"] == "wifi"
    assert request.metadata["reference_id"] == "hotspot-test-1"
    assert request.metadata["phone_number"] == "254712345678"

    transactions = db.paystack_transactions.documents
    assert len(transactions) == 1
    transaction = transactions[0]
    assert transaction["provider"] == "paystack"
    assert transaction["payment_type"] == "wifi"
    assert transaction["phone_number"] == "254712345678"
    assert transaction["status"] == "pending"
    assert transaction["authorization_url"] == body["authorization_url"]
    assert transaction["access_code"] == body["access_code"]
