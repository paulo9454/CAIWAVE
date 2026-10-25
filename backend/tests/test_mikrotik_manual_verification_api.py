from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import server


class FakeCollection:
    def __init__(self, documents=None):
        self.documents = [dict(item) for item in (documents or [])]

    async def find_one(self, query, projection=None):
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                return dict(document)
        return None

    async def insert_one(self, document):
        self.documents.append(dict(document))
        return SimpleNamespace(inserted_id="fake-event-id")


class FakeJobRepository:
    def __init__(self, flagged_job):
        self.flagged_job = dict(flagged_job) if flagged_job else None

    async def get_manual_verification_for_router(self, router_id):
        if (
            self.flagged_job
            and self.flagged_job.get("router_id") == router_id
            and self.flagged_job.get("requires_manual_verification") is True
        ):
            return dict(self.flagged_job)
        return None

    async def update_if_status(self, job_id, expected_status, updates):
        if (
            not self.flagged_job
            or self.flagged_job.get("job_id") != job_id
            or self.flagged_job.get("status") != expected_status
        ):
            return None
        self.flagged_job.update(updates)
        return dict(self.flagged_job)


def build_client(monkeypatch, *, role=None, with_gate=True):
    router_id = "router-manual-review-1"
    router = {
        "id": router_id,
        "nas_identifier": "CAIWAVE-REVIEW-001",
    }
    job = {
        "job_id": "job-manual-review-1",
        "router_id": router_id,
        "status": "failed",
        "requires_manual_verification": True,
    } if with_gate else None

    fake_db = SimpleNamespace(
        mikrotik_routers=FakeCollection([router]),
        router_events=FakeCollection(),
    )
    fake_repository = FakeJobRepository(job)

    monkeypatch.setattr(server, "db", fake_db)
    monkeypatch.setattr(
        server,
        "provisioning_job_repository",
        fake_repository,
    )

    app = FastAPI()
    app.include_router(server.mikrotik_onboard_router, prefix="/api")

    async def fake_current_user():
        return {
            "id": "admin-reviewer-1",
            "role": role or server.UserRole.SUPER_ADMIN.value,
        }

    app.dependency_overrides[server.get_current_user] = fake_current_user
    return TestClient(app), fake_repository, fake_db, router_id


def test_super_admin_can_resolve_manual_verification_with_audit(monkeypatch):
    client, repository, fake_db, router_id = build_client(monkeypatch)

    with client:
        response = client.post(
            f"/api/mikrotik-onboard/routers/{router_id}/resolve-manual-verification",
            json={"verification_note": "Verified router state in Winbox."},
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert body["requires_manual_verification"] is False
    assert body["job_id"] == "job-manual-review-1"

    assert repository.flagged_job["requires_manual_verification"] is False
    assert repository.flagged_job["manual_verification_resolved_by"] == "admin-reviewer-1"
    assert repository.flagged_job["manual_verification_note"] == "Verified router state in Winbox."

    events = fake_db.router_events.documents
    assert len(events) == 1
    assert events[0]["event_type"] == "provisioning_manual_verification_resolved"
    assert events[0]["details"]["job_id"] == "job-manual-review-1"


def test_resolution_rejects_note_with_too_few_non_space_characters(monkeypatch):
    client, repository, _, router_id = build_client(monkeypatch)

    with client:
        response = client.post(
            f"/api/mikrotik-onboard/routers/{router_id}/resolve-manual-verification",
            json={"verification_note": "         x"},
        )

    assert response.status_code == 422
    assert repository.flagged_job["requires_manual_verification"] is True


def test_resolution_rejects_when_no_gate_exists(monkeypatch):
    client, _, _, router_id = build_client(monkeypatch, with_gate=False)

    with client:
        response = client.post(
            f"/api/mikrotik-onboard/routers/{router_id}/resolve-manual-verification",
            json={"verification_note": "Verified router state in Winbox."},
        )

    assert response.status_code == 409


def test_non_super_admin_cannot_resolve_manual_verification(monkeypatch):
    client, repository, _, router_id = build_client(
        monkeypatch,
        role=server.UserRole.HOTSPOT_OWNER.value,
    )

    with client:
        response = client.post(
            f"/api/mikrotik-onboard/routers/{router_id}/resolve-manual-verification",
            json={"verification_note": "Verified router state in Winbox."},
        )

    assert response.status_code == 403
    assert repository.flagged_job["requires_manual_verification"] is True


def test_resolution_rejects_unknown_router(monkeypatch):
    client, _, _, router_id = build_client(monkeypatch)

    with client:
        response = client.post(
            "/api/mikrotik-onboard/routers/unknown-router/resolve-manual-verification",
            json={"verification_note": "Verified router state in Winbox."},
        )

    assert response.status_code == 404
