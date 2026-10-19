from datetime import datetime

import pytest

from backend.services.provisioning.job_service import (
    ProvisioningJobError,
    ProvisioningJobService,
)


def build_service():
    return ProvisioningJobService()


def build_job(service):
    return service.create_job(
        router_id="router-123",
        artifact_id="routeros-artifact:router-123",
        bundle_id="bundle:snapshot-123",
        snapshot_id="snapshot-123",
        artifact_checksum="abc123",
        payload={
            "operation": "provision",
        },
    )


def test_create_job_builds_queued_job():
    service = build_service()

    job = build_job(service)

    assert job["job_id"]
    assert job["router_id"] == "router-123"
    assert job["artifact_id"] == "routeros-artifact:router-123"
    assert job["bundle_id"] == "bundle:snapshot-123"
    assert job["snapshot_id"] == "snapshot-123"
    assert job["artifact_checksum"] == "abc123"
    assert job["status"] == "queued"
    assert job["attempts"] == 0
    assert job["payload"] == {"operation": "provision"}

    assert isinstance(job["created_at"], datetime)
    assert isinstance(job["updated_at"], datetime)

    assert job["started_at"] is None
    assert job["completed_at"] is None
    assert job["last_error"] is None
    assert job["result"] is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("router_id", ""),
        ("artifact_id", ""),
        ("bundle_id", ""),
        ("snapshot_id", ""),
        ("artifact_checksum", ""),
    ],
)
def test_create_job_requires_core_identity(field, value):
    service = build_service()

    kwargs = {
        "router_id": "router-123",
        "artifact_id": "artifact-123",
        "bundle_id": "bundle-123",
        "snapshot_id": "snapshot-123",
        "artifact_checksum": "checksum-123",
    }
    kwargs[field] = value

    with pytest.raises(ProvisioningJobError):
        service.create_job(**kwargs)


def test_transition_to_running_increments_attempts():
    service = build_service()
    job = build_job(service)

    updated = service.transition(
        job,
        status="running",
    )

    assert updated["status"] == "running"
    assert updated["attempts"] == 1
    assert updated["started_at"] is not None
    assert updated["completed_at"] is None


def test_transition_to_succeeded_stores_result():
    service = build_service()
    job = build_job(service)

    running = service.transition(
        job,
        status="running",
    )

    succeeded = service.transition(
        running,
        status="succeeded",
        result={
            "router_status": "provisioned",
        },
    )

    assert succeeded["status"] == "succeeded"
    assert succeeded["completed_at"] is not None
    assert succeeded["result"] == {
        "router_status": "provisioned",
    }


def test_transition_to_failed_stores_error():
    service = build_service()
    job = build_job(service)

    failed = service.transition(
        job,
        status="failed",
        error="Router did not acknowledge command",
    )

    assert failed["status"] == "failed"
    assert failed["completed_at"] is not None
    assert failed["last_error"] == "Router did not acknowledge command"


@pytest.mark.parametrize(
    ("current_status", "requested_status"),
    [
        ("queued", "succeeded"),
        ("dispatched", "queued"),
        ("succeeded", "failed"),
        ("failed", "succeeded"),
        ("cancelled", "running"),
    ],
)
def test_transition_rejects_invalid_transition(
    current_status,
    requested_status,
):
    service = build_service()
    job = build_job(service)
    job["status"] = current_status

    with pytest.raises(ProvisioningJobError, match="Invalid provisioning job transition"):
        service.transition(job, status=requested_status)


def test_duplicate_running_transition_does_not_increment_attempts():
    service = build_service()
    job = build_job(service)

    running = service.transition(job, status="running")
    repeated = service.transition(running, status="running")

    assert repeated["attempts"] == 1
    assert repeated["started_at"] == running["started_at"]
    assert repeated["updated_at"] == running["updated_at"]


def test_duplicate_terminal_transition_preserves_original_result():
    service = build_service()
    job = build_job(service)
    running = service.transition(job, status="running")

    succeeded = service.transition(
        running,
        status="succeeded",
        result={"router_status": "provisioned"},
    )
    repeated = service.transition(
        succeeded,
        status="succeeded",
        result={"router_status": "different"},
        error="Late duplicate callback",
    )

    assert repeated["completed_at"] == succeeded["completed_at"]
    assert repeated["result"] == {"router_status": "provisioned"}
    assert repeated.get("last_error") == succeeded.get("last_error")

def test_transition_rejects_invalid_status():
    service = build_service()
    job = build_job(service)

    with pytest.raises(ProvisioningJobError):
        service.transition(
            job,
            status="invalid-status",
        )


def test_transition_does_not_mutate_original_job():
    service = build_service()
    job = build_job(service)

    updated = service.transition(
        job,
        status="running",
    )

    assert job["status"] == "queued"
    assert job["attempts"] == 0
    assert job["started_at"] is None

    assert updated["status"] == "running"
    assert updated["attempts"] == 1
