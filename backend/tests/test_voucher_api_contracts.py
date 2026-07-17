from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import backend.server as server


class FakeInsertResult:
    inserted_id = "fake-id"


class FakeUpdateResult:
    def __init__(self, *, matched_count=1, modified_count=1):
        self.matched_count = matched_count
        self.modified_count = modified_count


class FakeDeleteResult:
    def __init__(self, deleted_count=1):
        self.deleted_count = deleted_count


def matches(document, query):
    for key, expected in query.items():
        actual = document.get(key)

        if isinstance(expected, dict):
            if "$gt" in expected and not (actual > expected["$gt"]):
                return False

            if "$in" in expected and actual not in expected["$in"]:
                return False

            continue

        if actual != expected:
            return False

    return True


class FakeCursor:
    def __init__(self, documents):
        self.documents = deepcopy(documents)

    def sort(self, field, direction):
        reverse = direction < 0
        self.documents.sort(
            key=lambda document: document.get(field) or "",
            reverse=reverse,
        )
        return self

    def limit(self, count):
        self.documents = self.documents[:count]
        return self

    async def to_list(self, length=None):
        if length is None:
            return deepcopy(self.documents)

        return deepcopy(self.documents[:length])


class FakeCollection:
    def __init__(self, documents=None, *, fail_insert=False):
        self.documents = deepcopy(documents or [])
        self.fail_insert = fail_insert

    def find(self, query, projection=None):
        matched = []

        for document in self.documents:
            if not matches(document, query):
                continue

            result = deepcopy(document)

            if projection and projection.get("_id") == 0:
                result.pop("_id", None)

            matched.append(result)

        return FakeCursor(matched)

    async def find_one(self, query, projection=None):
        for document in self.documents:
            if matches(document, query):
                result = deepcopy(document)
                result.pop("_id", None)
                return result

        return None

    async def find_one_and_update(
        self,
        query,
        operation,
        projection=None,
        return_document=None,
    ):
        for document in self.documents:
            if matches(document, query):
                document.update(deepcopy(operation.get("$set", {})))
                result = deepcopy(document)

                if projection and projection.get("_id") == 0:
                    result.pop("_id", None)

                return result

        return None

    async def insert_one(self, document):
        if self.fail_insert:
            raise RuntimeError("Simulated session insertion failure")

        self.documents.append(deepcopy(document))
        return FakeInsertResult()

    async def update_one(self, query, operation):
        for document in self.documents:
            if not matches(document, query):
                continue

            if "$set" in operation:
                document.update(deepcopy(operation["$set"]))

            if "$inc" in operation:
                for key, amount in operation["$inc"].items():
                    document[key] = document.get(key, 0) + amount

            return FakeUpdateResult()

        return FakeUpdateResult(
            matched_count=0,
            modified_count=0,
        )

    async def update_many(self, query, operation):
        matched_count = 0
        modified_count = 0

        for document in self.documents:
            if not matches(document, query):
                continue

            matched_count += 1
            before = deepcopy(document)

            if "$set" in operation:
                document.update(deepcopy(operation["$set"]))

            if "$inc" in operation:
                for key, amount in operation["$inc"].items():
                    document[key] = document.get(key, 0) + amount

            if document != before:
                modified_count += 1

        return FakeUpdateResult(
            matched_count=matched_count,
            modified_count=modified_count,
        )

    async def delete_one(self, query):
        for index, document in enumerate(self.documents):
            if matches(document, query):
                self.documents.pop(index)
                return FakeDeleteResult(1)

        return FakeDeleteResult(0)


def active_hotspot():
    return {
        "id": "hotspot-1",
        "owner_id": "owner-1",
        "status": "active",
        "total_sessions": 0,
    }


def active_package():
    return {
        "id": "pkg-30min",
        "is_active": True,
        "duration_minutes": 30,
        "speed_mbps": 5,
    }


def unused_voucher(**changes):
    voucher = {
        "id": "voucher-1",
        "code": "CAITEST1",
        "package_id": "pkg-30min",
        "hotspot_id": "hotspot-1",
        "owner_id": "owner-1",
        "generated_by": "admin-1",
        "purpose": "test",
        "username": "voucher-user",
        "password": "voucher-pass",
        "is_used": False,
        "redemption_status": "unused",
        "used_at": None,
        "used_mac": None,
        "used_ip": None,
        "redeemed_session_id": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (
            datetime.now(timezone.utc) + timedelta(days=1)
        ).isoformat(),
    }
    voucher.update(changes)
    return voucher


@pytest.fixture
def environment(monkeypatch):
    fake_db = SimpleNamespace(
        hotspots=FakeCollection([active_hotspot()]),
        packages=FakeCollection([active_package()]),
        vouchers=FakeCollection([unused_voucher()]),
        sessions=FakeCollection(),
    )

    monkeypatch.setattr(server, "db", fake_db)

    app = FastAPI()
    app.include_router(server.vouchers_router, prefix="/api")

    app.dependency_overrides[server.get_current_user] = lambda: {
        "id": "owner-1",
        "role": server.UserRole.HOTSPOT_OWNER.value,
    }

    with TestClient(app) as client:
        yield client, fake_db


def test_successful_redemption_creates_wifi_session(environment):
    client, fake_db = environment

    response = client.post(
        "/api/vouchers/redeem/caitest1",
        params={
            "hotspot_id": "hotspot-1",
            "user_mac": "aa-bb-cc-dd-ee-ff",
            "user_ip": "10.10.0.25",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["status"] == "completed"
    assert body["payment_type"] == "voucher"
    assert body["wifi_credentials"]["username"] == "voucher-user"
    assert body["wifi_credentials"]["password"] == "voucher-pass"
    assert body["wifi_credentials"]["duration_minutes"] == 30

    assert len(fake_db.sessions.documents) == 1

    session = fake_db.sessions.documents[0]

    assert session["username"] == "voucher-user"
    assert session["password"] == "voucher-pass"
    assert session["rate_limit"] == "5M/5M"
    assert session["user_mac"] == "AA:BB:CC:DD:EE:FF"
    assert session["user_ip"] == "10.10.0.25"
    assert session["voucher_code"] == "CAITEST1"

    voucher = fake_db.vouchers.documents[0]

    assert voucher["is_used"] is True
    assert voucher["redemption_status"] == "redeemed"
    assert voucher["redeemed_session_id"] == session["id"]

    assert fake_db.hotspots.documents[0]["total_sessions"] == 1


def test_used_voucher_is_rejected(environment):
    client, fake_db = environment
    fake_db.vouchers.documents[0]["is_used"] = True
    fake_db.vouchers.documents[0]["redemption_status"] = "redeemed"

    response = client.post(
        "/api/vouchers/redeem/CAITEST1",
        params={"hotspot_id": "hotspot-1"},
    )

    assert response.status_code == 409
    assert "already been used" in response.json()["detail"]


def test_wrong_hotspot_is_rejected(environment):
    client, _ = environment

    response = client.post(
        "/api/vouchers/redeem/CAITEST1",
        params={"hotspot_id": "different-hotspot"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Hotspot not found"


def test_expired_voucher_is_rejected(environment):
    client, fake_db = environment

    fake_db.vouchers.documents[0]["expires_at"] = (
        datetime.now(timezone.utc) - timedelta(minutes=1)
    ).isoformat()

    response = client.post(
        "/api/vouchers/redeem/CAITEST1",
        params={"hotspot_id": "hotspot-1"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Voucher has expired"


def test_inactive_hotspot_is_rejected(environment):
    client, fake_db = environment
    fake_db.hotspots.documents[0]["status"] = "suspended"

    response = client.post(
        "/api/vouchers/redeem/CAITEST1",
        params={"hotspot_id": "hotspot-1"},
    )

    assert response.status_code == 400
    assert "not currently active" in response.json()["detail"]


def test_inactive_package_releases_voucher(environment):
    client, fake_db = environment
    fake_db.packages.documents[0]["is_active"] = False

    response = client.post(
        "/api/vouchers/redeem/CAITEST1",
        params={"hotspot_id": "hotspot-1"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Voucher package is unavailable"

    voucher = fake_db.vouchers.documents[0]

    assert voucher["is_used"] is False
    assert voucher["redemption_status"] == "unused"
    assert voucher["used_at"] is None
    assert len(fake_db.sessions.documents) == 0


def test_session_insert_failure_rolls_back_voucher(monkeypatch):
    fake_db = SimpleNamespace(
        hotspots=FakeCollection([active_hotspot()]),
        packages=FakeCollection([active_package()]),
        vouchers=FakeCollection([unused_voucher()]),
        sessions=FakeCollection(fail_insert=True),
    )

    monkeypatch.setattr(server, "db", fake_db)

    app = FastAPI()
    app.include_router(server.vouchers_router, prefix="/api")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/vouchers/redeem/CAITEST1",
            params={"hotspot_id": "hotspot-1"},
        )

    assert response.status_code == 500
    assert len(fake_db.sessions.documents) == 0
    assert fake_db.hotspots.documents[0]["total_sessions"] == 0

    voucher = fake_db.vouchers.documents[0]

    assert voucher["is_used"] is False
    assert voucher["redemption_status"] == "unused"
    assert voucher["used_at"] is None
    assert voucher["redeemed_session_id"] is None


def test_second_redemption_cannot_create_second_session(environment):
    client, fake_db = environment

    first = client.post(
        "/api/vouchers/redeem/CAITEST1",
        params={"hotspot_id": "hotspot-1"},
    )

    second = client.post(
        "/api/vouchers/redeem/CAITEST1",
        params={"hotspot_id": "hotspot-1"},
    )

    assert first.status_code == 200
    assert second.status_code == 409
    assert len(fake_db.sessions.documents) == 1
    assert fake_db.hotspots.documents[0]["total_sessions"] == 1


def test_generated_vouchers_share_one_batch(environment):
    client, fake_db = environment

    fake_db.vouchers.documents = []

    response = client.post(
        "/api/vouchers/generate",
        json={
            "package_id": "pkg-30min",
            "hotspot_id": "hotspot-1",
            "quantity": 3,
            "validity_days": 14,
            "purpose": "standard",
            "batch_name": "Weekend sales",
        },
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200

    vouchers = response.json()

    assert len(vouchers) == 3
    assert len({voucher["batch_id"] for voucher in vouchers}) == 1
    assert all(
        voucher["batch_name"] == "Weekend sales"
        for voucher in vouchers
    )


def test_generated_batch_name_defaults_to_none(environment):
    client, fake_db = environment

    fake_db.vouchers.documents = []

    response = client.post(
        "/api/vouchers/generate",
        json={
            "package_id": "pkg-30min",
            "hotspot_id": "hotspot-1",
            "quantity": 2,
        },
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200

    vouchers = response.json()

    assert len({voucher["batch_id"] for voucher in vouchers}) == 1
    assert all(voucher["batch_name"] is None for voucher in vouchers)


def test_owner_can_filter_own_vouchers_by_hotspot(environment):
    client, fake_db = environment

    fake_db.vouchers.documents = [
        unused_voucher(
            id="voucher-own-one",
            code="OWNONE01",
            owner_id="owner-1",
            hotspot_id="hotspot-1",
        ),
        unused_voucher(
            id="voucher-own-two",
            code="OWNTWO02",
            owner_id="owner-1",
            hotspot_id="hotspot-2",
        ),
        unused_voucher(
            id="voucher-other",
            code="OTHER003",
            owner_id="owner-2",
            hotspot_id="hotspot-1",
        ),
    ]

    response = client.get(
        "/api/vouchers/",
        params={"hotspot_id": "hotspot-1"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200

    vouchers = response.json()

    assert [voucher["id"] for voucher in vouchers] == [
        "voucher-own-one"
    ]


def test_owner_listing_never_exposes_other_owner_vouchers(environment):
    client, fake_db = environment

    fake_db.vouchers.documents = [
        unused_voucher(
            id="voucher-own",
            code="OWNER001",
            owner_id="owner-1",
        ),
        unused_voucher(
            id="voucher-other",
            code="OTHER001",
            owner_id="owner-2",
        ),
    ]

    response = client.get(
        "/api/vouchers/",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200

    vouchers = response.json()

    assert [voucher["id"] for voucher in vouchers] == [
        "voucher-own"
    ]


def test_owner_can_revoke_own_unused_voucher(environment):
    client, fake_db = environment

    fake_db.vouchers.documents = [
        unused_voucher(
            id="voucher-revoke",
            code="REVOKE01",
            owner_id="owner-1",
        )
    ]

    response = client.post(
        "/api/vouchers/voucher-revoke/revoke",
        json={"reason": "Issued by mistake"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["voucher"]["redemption_status"] == "revoked"
    assert body["voucher"]["revoked_by"] == "owner-1"
    assert body["voucher"]["revocation_reason"] == (
        "Issued by mistake"
    )
    assert body["voucher"]["revoked_at"]

    voucher = fake_db.vouchers.documents[0]

    assert voucher["is_used"] is False
    assert voucher["redemption_status"] == "revoked"
    assert voucher["revoked_by"] == "owner-1"


def test_owner_cannot_revoke_another_owners_voucher(environment):
    client, fake_db = environment

    fake_db.vouchers.documents = [
        unused_voucher(
            id="voucher-other-owner",
            code="OTHER999",
            owner_id="owner-2",
        )
    ]

    response = client.post(
        "/api/vouchers/voucher-other-owner/revoke",
        json={"reason": "Not mine"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Voucher not found"

    voucher = fake_db.vouchers.documents[0]

    assert voucher["redemption_status"] == "unused"
    assert voucher["is_used"] is False


def test_redeemed_voucher_cannot_be_revoked(environment):
    client, fake_db = environment

    fake_db.vouchers.documents = [
        unused_voucher(
            id="voucher-redeemed",
            code="USED0001",
            is_used=True,
            redemption_status="redeemed",
            redeemed_session_id="session-1",
        )
    ]

    response = client.post(
        "/api/vouchers/voucher-redeemed/revoke",
        json={"reason": "Too late"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Only unused vouchers can be revoked"
    )


def test_revoked_voucher_cannot_be_redeemed(environment):
    client, fake_db = environment

    fake_db.vouchers.documents = [
        unused_voucher(
            id="voucher-revoked",
            code="REVOKED1",
            redemption_status="revoked",
            revoked_at=datetime.now(timezone.utc).isoformat(),
            revoked_by="owner-1",
            revocation_reason="Issued by mistake",
        )
    ]

    response = client.post(
        "/api/vouchers/redeem/REVOKED1",
        params={"hotspot_id": "hotspot-1"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Voucher has been revoked"
    assert len(fake_db.sessions.documents) == 0


def test_owner_voucher_summary_is_scoped_and_status_aware(environment):
    client, fake_db = environment
    now = datetime.now(timezone.utc)

    fake_db.vouchers.documents = [
        unused_voucher(
            id="unused-own",
            code="SUMMARY1",
            owner_id="owner-1",
            hotspot_id="hotspot-1",
            redemption_status="unused",
            expires_at=(now + timedelta(days=1)).isoformat(),
        ),
        unused_voucher(
            id="redeemed-own",
            code="SUMMARY2",
            owner_id="owner-1",
            hotspot_id="hotspot-1",
            is_used=True,
            redemption_status="redeemed",
        ),
        unused_voucher(
            id="revoked-own",
            code="SUMMARY3",
            owner_id="owner-1",
            hotspot_id="hotspot-1",
            redemption_status="revoked",
        ),
        unused_voucher(
            id="expired-own",
            code="SUMMARY4",
            owner_id="owner-1",
            hotspot_id="hotspot-1",
            redemption_status="unused",
            expires_at=(now - timedelta(minutes=1)).isoformat(),
        ),
        unused_voucher(
            id="other-hotspot",
            code="SUMMARY5",
            owner_id="owner-1",
            hotspot_id="hotspot-2",
        ),
        unused_voucher(
            id="other-owner",
            code="SUMMARY6",
            owner_id="owner-2",
            hotspot_id="hotspot-1",
        ),
    ]

    response = client.get(
        "/api/vouchers/summary",
        params={"hotspot_id": "hotspot-1"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "total": 4,
        "unused": 1,
        "processing": 0,
        "redeemed": 1,
        "revoked": 1,
        "expired": 1,
    }


def test_owner_batch_listing_groups_vouchers(environment):
    client, fake_db = environment
    now = datetime.now(timezone.utc)

    fake_db.vouchers.documents = [
        unused_voucher(
            id="batch-one-a",
            code="BATCHA01",
            owner_id="owner-1",
            hotspot_id="hotspot-1",
            batch_id="batch-one",
            batch_name="Weekend sales",
            created_at=(now - timedelta(hours=1)).isoformat(),
        ),
        unused_voucher(
            id="batch-one-b",
            code="BATCHA02",
            owner_id="owner-1",
            hotspot_id="hotspot-1",
            batch_id="batch-one",
            batch_name="Weekend sales",
            is_used=True,
            redemption_status="redeemed",
            created_at=(now - timedelta(hours=1)).isoformat(),
        ),
        unused_voucher(
            id="batch-two-a",
            code="BATCHB01",
            owner_id="owner-1",
            hotspot_id="hotspot-1",
            batch_id="batch-two",
            batch_name=None,
            redemption_status="revoked",
            created_at=now.isoformat(),
        ),
        unused_voucher(
            id="other-owner",
            code="BATCHC01",
            owner_id="owner-2",
            hotspot_id="hotspot-1",
            batch_id="other-batch",
        ),
    ]

    response = client.get(
        "/api/vouchers/batches",
        params={"hotspot_id": "hotspot-1"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200

    batches = response.json()

    assert [batch["batch_id"] for batch in batches] == [
        "batch-two",
        "batch-one",
    ]

    batch_one = next(
        batch for batch in batches
        if batch["batch_id"] == "batch-one"
    )

    assert batch_one["batch_name"] == "Weekend sales"
    assert batch_one["total"] == 2
    assert batch_one["unused"] == 1
    assert batch_one["redeemed"] == 1
    assert batch_one["revoked"] == 0
    assert batch_one["hotspot_id"] == "hotspot-1"


def test_owner_can_revoke_unused_vouchers_in_own_batch(environment):
    client, fake_db = environment

    fake_db.vouchers.documents = [
        unused_voucher(
            id="batch-unused-one",
            code="BREVOKE1",
            owner_id="owner-1",
            batch_id="batch-revoke",
            redemption_status="unused",
        ),
        unused_voucher(
            id="batch-unused-two",
            code="BREVOKE2",
            owner_id="owner-1",
            batch_id="batch-revoke",
            redemption_status="unused",
        ),
        unused_voucher(
            id="batch-redeemed",
            code="BREVOKE3",
            owner_id="owner-1",
            batch_id="batch-revoke",
            is_used=True,
            redemption_status="redeemed",
            redeemed_session_id="session-1",
        ),
    ]

    response = client.post(
        "/api/vouchers/batches/batch-revoke/revoke",
        json={"reason": "Batch issued in error"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "batch_id": "batch-revoke",
        "total": 3,
        "revoked": 2,
        "skipped": 1,
        "message": "Unused vouchers in batch revoked successfully.",
    }

    unused = [
        voucher
        for voucher in fake_db.vouchers.documents
        if voucher["id"] in {
            "batch-unused-one",
            "batch-unused-two",
        }
    ]

    assert all(
        voucher["redemption_status"] == "revoked"
        for voucher in unused
    )
    assert all(
        voucher["revoked_by"] == "owner-1"
        for voucher in unused
    )
    assert all(
        voucher["revocation_reason"] == "Batch issued in error"
        for voucher in unused
    )

    redeemed = next(
        voucher
        for voucher in fake_db.vouchers.documents
        if voucher["id"] == "batch-redeemed"
    )

    assert redeemed["redemption_status"] == "redeemed"
    assert redeemed["is_used"] is True


def test_owner_cannot_revoke_another_owners_batch(environment):
    client, fake_db = environment

    fake_db.vouchers.documents = [
        unused_voucher(
            id="other-owner-batch",
            code="OTHERBAT",
            owner_id="owner-2",
            batch_id="batch-other",
        )
    ]

    response = client.post(
        "/api/vouchers/batches/batch-other/revoke",
        json={"reason": "Not my batch"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Voucher batch not found"
    assert (
        fake_db.vouchers.documents[0]["redemption_status"]
        == "unused"
    )


def test_batch_revocation_rejects_batch_with_no_unused_vouchers(environment):
    client, fake_db = environment

    fake_db.vouchers.documents = [
        unused_voucher(
            id="already-redeemed",
            code="DONEBAT1",
            owner_id="owner-1",
            batch_id="batch-complete",
            is_used=True,
            redemption_status="redeemed",
        ),
        unused_voucher(
            id="already-revoked",
            code="DONEBAT2",
            owner_id="owner-1",
            batch_id="batch-complete",
            redemption_status="revoked",
        ),
    ]

    response = client.post(
        "/api/vouchers/batches/batch-complete/revoke",
        json={"reason": "Nothing left"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Batch has no unused vouchers to revoke"
    )


def test_batch_revocation_requires_valid_reason(environment):
    client, fake_db = environment

    fake_db.vouchers.documents = [
        unused_voucher(
            id="reason-test",
            code="REASON01",
            owner_id="owner-1",
            batch_id="batch-reason",
        )
    ]

    response = client.post(
        "/api/vouchers/batches/batch-reason/revoke",
        json={"reason": "x"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 422
    assert (
        fake_db.vouchers.documents[0]["redemption_status"]
        == "unused"
    )
