from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import server


class FakeRouterCursor:
    def __init__(self, documents):
        self.documents = [dict(doc) for doc in documents]

    def sort(self, field, direction=-1):
        self.documents.sort(
            key=lambda doc: doc.get(field) or "",
            reverse=direction == -1,
        )
        return self

    async def to_list(self, length=None):
        if length is None:
            return self.documents
        return self.documents[:length]


class FakeRouterCollection:
    def __init__(self, documents):
        self.documents = [dict(doc) for doc in documents]
        self.last_query = None

    def find(self, query, projection=None):
        self.last_query = dict(query)
        matching = [
            doc for doc in self.documents
            if all(doc.get(key) == value for key, value in query.items())
        ]
        return FakeRouterCursor(matching)


class FakeJobRepository:
    def __init__(self, flagged_jobs=None):
        self.flagged_jobs = flagged_jobs or {}

    async def get_manual_verification_for_router(self, router_id):
        job = self.flagged_jobs.get(router_id)
        return dict(job) if job else None


class RepositoryWithoutSafetyLookup:
    pass


class RepositoryWithFailingSafetyLookup:
    async def get_manual_verification_for_router(self, router_id):
        raise RuntimeError("Safety status store unavailable")


@pytest.fixture
def router_documents():
    return [
        {
            "id": "router-owner-a",
            "owner_id": "owner-a",
            "hotspot_id": "hotspot-a",
            "nas_identifier": "CAIWAVE-OWNER-A",
            "name": "Owner A Router",
            "created_at": "2026-10-24T10:00:00+00:00",
        },
        {
            "id": "router-owner-b",
            "owner_id": "owner-b",
            "hotspot_id": "hotspot-b",
            "nas_identifier": "CAIWAVE-OWNER-B",
            "name": "Owner B Router",
            "created_at": "2026-10-25T10:00:00+00:00",
        },
    ]


def make_client(monkeypatch, routers, repository, user):
    router_collection = FakeRouterCollection(routers)
    monkeypatch.setattr(
        server,
        "db",
        SimpleNamespace(mikrotik_routers=router_collection),
    )
    monkeypatch.setattr(
        server,
        "provisioning_job_repository",
        repository,
    )

    app = FastAPI()
    app.include_router(server.mikrotik_onboard_router, prefix="/api")

    async def fake_current_user():
        return user

    app.dependency_overrides[server.get_current_user] = fake_current_user
    return app, router_collection


def test_super_admin_router_list_reports_blocked_and_clear_status(
    monkeypatch, router_documents
):
    flagged_job = {
        "job_id": "job-requires-review",
        "router_id": "router-owner-a",
        "status": "failed",
        "requires_manual_verification": True,
        "last_error": "Router must be inspected before retrying.",
        "created_at": "2026-10-25T09:00:00+00:00",
    }
    repository = FakeJobRepository({
        "router-owner-a": flagged_job,
    })
    app, _ = make_client(
        monkeypatch,
        router_documents,
        repository,
        {
            "id": "admin-a",
            "role": server.UserRole.SUPER_ADMIN.value,
        },
    )

    with TestClient(app) as client:
        response = client.get("/api/mikrotik-onboard/routers")

    assert response.status_code == 200, response.text
    routers = {router["id"]: router for router in response.json()}

    blocked = routers["router-owner-a"]
    assert blocked["manual_verification_status_available"] is True
    assert blocked["requires_manual_verification"] is True
    assert blocked["manual_verification"]["job_id"] == "job-requires-review"
    assert blocked["manual_verification"]["status"] == "failed"
    assert "inspected" in blocked["manual_verification"]["reason"]

    clear = routers["router-owner-b"]
    assert clear["manual_verification_status_available"] is True
    assert clear["requires_manual_verification"] is False
    assert clear["manual_verification"] is None


def test_owner_router_list_is_scoped_to_that_owner(
    monkeypatch, router_documents
):
    repository = FakeJobRepository({
        "router-owner-a": {
            "job_id": "job-owner-a-review",
            "status": "failed",
            "last_error": "Verification required.",
        },
        "router-owner-b": {
            "job_id": "job-owner-b-review",
            "status": "failed",
            "last_error": "Another owner's router.",
        },
    })
    app, router_collection = make_client(
        monkeypatch,
        router_documents,
        repository,
        {
            "id": "owner-a",
            "role": server.UserRole.HOTSPOT_OWNER.value,
        },
    )

    with TestClient(app) as client:
        response = client.get("/api/mikrotik-onboard/routers")

    assert response.status_code == 200, response.text
    routers = response.json()

    assert [router["id"] for router in routers] == ["router-owner-a"]
    assert router_collection.last_query == {"owner_id": "owner-a"}
    assert routers[0]["requires_manual_verification"] is True


@pytest.mark.parametrize(
    "repository",
    [
        RepositoryWithoutSafetyLookup(),
        RepositoryWithFailingSafetyLookup(),
    ],
    ids=["lookup-missing", "lookup-fails"],
)
def test_router_list_fails_closed_when_safety_status_is_unavailable(
    monkeypatch, router_documents, repository
):
    app, _ = make_client(
        monkeypatch,
        router_documents[:1],
        repository,
        {
            "id": "admin-a",
            "role": server.UserRole.SUPER_ADMIN.value,
        },
    )

    with TestClient(app) as client:
        response = client.get("/api/mikrotik-onboard/routers")

    assert response.status_code == 200, response.text
    router = response.json()[0]

    assert router["manual_verification_status_available"] is False
    assert router["requires_manual_verification"] is None
    assert router["manual_verification"] is None
