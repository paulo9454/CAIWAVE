import hashlib
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import server
from backend.services.mikrotik_control_plane.credentials import hash_control_secret


@pytest.fixture
def poll_harness(monkeypatch):
    now = datetime.now(timezone.utc)
    content = "/system identity set name=CAIWAVE"
    checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()

    router = {
        "id": "router-poll-safety",
        "nas_identifier": "CAIWAVE-POLL-SAFETY",
    }
    credential = {
        "credential_id": "credential-poll-safety",
        "router_id": router["id"],
        "secret_hash": hash_control_secret("poll-safety-secret"),
        "expires_at": (now + timedelta(days=365)).isoformat(),
        "status": "active",
    }
    artifact = {
        "artifact_id": "artifact-poll-safety",
        "router_id": router["id"],
        "bundle_id": "bundle-poll-safety",
        "snapshot_id": "snapshot-poll-safety",
        "filename": "poll-safety.rsc",
        "content_type": "text/routeros-script",
        "checksum": checksum,
        "content": content,
    }
    job = {
        "job_id": "job-poll-safety",
        "router_id": router["id"],
        "artifact_id": artifact["artifact_id"],
        "bundle_id": artifact["bundle_id"],
        "snapshot_id": artifact["snapshot_id"],
        "artifact_checksum": checksum,
        "status": "dispatched",
        "created_at": now,
        "dispatched_at": now,
        "updated_at": now,
    }

    class FakeRouters:
        async def find_one(self, query, projection=None):
            if query.get("nas_identifier") == router["nas_identifier"]:
                return dict(router)
            return None

    class FakeDB:
        mikrotik_routers = FakeRouters()

    class FakeCredentialRepository:
        async def get_active_credentials(self):
            return [credential]

        async def get_active_and_pending_credentials(self):
            return [credential]

    class FakeJobRepository:
        def __init__(self):
            self.current_job = dict(job)
            self.claim_next_calls = 0
            self.exact_claim_calls = []

        async def get_manual_verification_for_router(self, router_id):
            current = self.current_job
            if (
                current.get("router_id") == router_id
                and current.get("requires_manual_verification") is True
            ):
                return dict(current)
            return None

        async def get_active_for_router(self, router_id, job_type=None):
            current = self.current_job
            if (
                current.get("router_id") != router_id
                or current.get("status") not in {"queued", "dispatched", "running"}
            ):
                return None

            current_type = current.get("job_type")
            if (
                job_type is None
                or current_type == job_type
                or (job_type == "provisioning" and "job_type" not in current)
            ):
                return dict(current)
            return None

        async def claim_next_for_router(self, router_id, job_type=None):
            self.claim_next_calls += 1
            return None

        async def claim_queued_job_for_router(
            self, router_id, job_id, job_type=None
        ):
            self.exact_claim_calls.append((router_id, job_id, job_type))
            current = self.current_job
            if (
                current.get("router_id") != router_id
                or current.get("job_id") != job_id
                or current.get("status") != "queued"
            ):
                return None

            current.update({
                "status": "dispatched",
                "dispatched_at": now,
                "updated_at": now,
            })
            return dict(current)

        async def update_if_status(self, job_id, expected_status, updates):
            current = self.current_job
            if (
                current.get("job_id") != job_id
                or current.get("status") != expected_status
            ):
                return None

            current.update(updates)
            return dict(current)

        async def get_by_id(self, job_id):
            if self.current_job.get("job_id") == job_id:
                return dict(self.current_job)
            return None

        async def update(self, job_id, updates):
            if self.current_job.get("job_id") != job_id:
                return None
            self.current_job.update(updates)
            return dict(self.current_job)

    class FakeArtifactRepository:
        async def get_by_id(self, artifact_id):
            if artifact_id == artifact["artifact_id"]:
                return dict(artifact)
            return None

    jobs = FakeJobRepository()

    monkeypatch.setattr(server, "db", FakeDB())
    monkeypatch.setattr(
        server, "router_control_credential_repository", FakeCredentialRepository()
    )
    monkeypatch.setattr(server, "provisioning_job_repository", jobs)
    monkeypatch.setattr(
        server, "provisioning_artifact_repository", FakeArtifactRepository()
    )
    monkeypatch.setattr(
        server, "mikrotik_provisioning_orchestrator", SimpleNamespace()
    )

    app = FastAPI()
    app.include_router(server.mikrotik_onboard_router, prefix="/api")

    with TestClient(app) as client:
        yield SimpleNamespace(
            client=client,
            jobs=jobs,
            now=now,
            router=router,
        )


def poll(harness, safe_replay=False):
    return harness.client.post(
        "/api/mikrotik-onboard/poll",
        json={
            "nas_identifier": harness.router["nas_identifier"],
            "supports_safe_dispatched_replay": safe_replay,
        },
        headers={"Authorization": "Bearer poll-safety-secret"},
    )


def test_running_job_is_never_replayed(poll_harness):
    h = poll_harness
    h.jobs.current_job.update({
        "status": "running",
        "updated_at": h.now - timedelta(minutes=5),
    })

    response = poll(h, safe_replay=True)

    assert response.status_code == 200, response.text
    assert response.json()["job_available"] is False
    assert h.jobs.claim_next_calls == 0


@pytest.mark.parametrize(
    ("safe_replay", "expected_available"),
    [(False, False), (True, True)],
)
def test_dispatched_job_replay_requires_explicit_support(
    poll_harness, safe_replay, expected_available
):
    h = poll_harness

    response = poll(h, safe_replay=safe_replay)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["job_available"] is expected_available
    assert h.jobs.claim_next_calls == 0

    if expected_available:
        assert data["job"]["job_id"] == "job-poll-safety"
        assert data["artifact"]["checksum"] == h.jobs.current_job["artifact_checksum"]
    else:
        assert data.get("artifact") is None


def test_timed_out_dispatched_job_requires_manual_verification(poll_harness):
    h = poll_harness
    h.jobs.current_job["updated_at"] = h.now - timedelta(minutes=31)

    response = poll(h, safe_replay=True)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["job_available"] is False
    assert data["requires_manual_verification"] is True
    assert h.jobs.current_job["status"] == "failed"
    assert h.jobs.current_job["requires_manual_verification"] is True
    assert h.jobs.claim_next_calls == 0


def test_missing_job_timestamp_fails_closed(poll_harness):
    h = poll_harness
    h.jobs.current_job["status"] = "running"
    h.jobs.current_job.pop("updated_at", None)
    h.jobs.current_job.pop("dispatched_at", None)
    h.jobs.current_job.pop("created_at", None)

    response = poll(h, safe_replay=True)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["job_available"] is False
    assert data["requires_manual_verification"] is True
    assert h.jobs.current_job["status"] == "failed"
    assert h.jobs.current_job["requires_manual_verification"] is True
    assert h.jobs.claim_next_calls == 0


def test_existing_manual_verification_gate_blocks_poll(poll_harness):
    h = poll_harness
    h.jobs.current_job.update({
        "status": "failed",
        "requires_manual_verification": True,
        "last_error": "Needs router inspection",
    })

    response = poll(h, safe_replay=True)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["job_available"] is False
    assert data["requires_manual_verification"] is True
    assert "Super Admin" in data["blocked_reason"]
    assert h.jobs.claim_next_calls == 0


def test_queued_job_is_claimed_by_exact_job_id(poll_harness):
    h = poll_harness
    h.jobs.current_job.update({
        "status": "queued",
        "updated_at": h.now,
        "created_at": h.now,
    })

    response = poll(h)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["job_available"] is True
    assert data["job"]["job_id"] == "job-poll-safety"
    assert data["job"]["status"] == "dispatched"
    assert h.jobs.exact_claim_calls == [
        (h.router["id"], "job-poll-safety", "provisioning")
    ]
    assert h.jobs.claim_next_calls == 0
