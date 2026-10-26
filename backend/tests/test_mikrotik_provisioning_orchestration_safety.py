import asyncio
from datetime import datetime, timezone

import pytest

from backend.services.provisioning.repository import ActiveProvisioningJobConflict

from backend.services.mikrotik_control_plane.provisioning import (
    MikroTikProvisioningOrchestrationError,
    MikroTikProvisioningOrchestrator,
)


class FakeRepository:
    def __init__(self, active_job=None, manual_job=None):
        self.active_job = dict(active_job) if active_job else None
        self.manual_job = dict(manual_job) if manual_job else None
        self.created = []
        self.active_lookup_calls = 0

    async def get_manual_verification_for_router(self, router_id):
        return dict(self.manual_job) if self.manual_job else None

    async def get_active_for_router(self, router_id, job_type=None):
        self.active_lookup_calls += 1
        if (
            self.active_job
            and self.active_job.get("router_id") == router_id
            and self.active_job.get("status") in {"queued", "dispatched", "running"}
            and (
                job_type is None
                or self.active_job.get("job_type") == job_type
                or (
                    job_type == "provisioning"
                    and "job_type" not in self.active_job
                )
            )
        ):
            return dict(self.active_job)
        return None

    async def update_if_status(self, job_id, expected_status, updates):
        if (
            not self.active_job
            or self.active_job.get("job_id") != job_id
            or self.active_job.get("status") != expected_status
        ):
            return None
        self.active_job.update(updates)
        return dict(self.active_job)

    async def create(self, document):
        created = dict(document)
        self.created.append(created)
        return created


def run(coro):
    return asyncio.run(coro)


def make_active_job(status="queued", checksum="old-checksum"):
    return {
        "job_id": "old-job",
        "router_id": "router-1",
        "job_type": "provisioning",
        "artifact_id": "old-artifact",
        "bundle_id": "old-bundle",
        "snapshot_id": "old-snapshot",
        "artifact_checksum": checksum,
        "status": status,
        "attempts": 1 if status == "running" else 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


async def create_replacement(orchestrator):
    return await orchestrator.get_or_create_provisioning_job(
        router_id="router-1",
        artifact_id="new-artifact",
        bundle_id="new-bundle",
        snapshot_id="new-snapshot",
        artifact_checksum="new-checksum",
    )


def test_existing_manual_verification_gate_blocks_orchestration():
    async def scenario():
        repository = FakeRepository(
            manual_job={
                "job_id": "review-job",
                "requires_manual_verification": True,
            }
        )
        orchestrator = MikroTikProvisioningOrchestrator(repository)

        with pytest.raises(
            MikroTikProvisioningOrchestrationError,
            match="manual router verification",
        ):
            await create_replacement(orchestrator)

        assert repository.active_lookup_calls == 0
        assert repository.created == []

    run(scenario())


def test_different_artifact_for_running_job_requires_manual_review():
    async def scenario():
        repository = FakeRepository(active_job=make_active_job("running"))
        orchestrator = MikroTikProvisioningOrchestrator(repository)

        with pytest.raises(
            MikroTikProvisioningOrchestrationError,
            match="Manual verification is required",
        ):
            await create_replacement(orchestrator)

        assert repository.active_job["status"] == "failed"
        assert repository.active_job["requires_manual_verification"] is True
        assert repository.created == []

    run(scenario())


def test_queued_job_can_be_superseded_without_manual_review():
    async def scenario():
        repository = FakeRepository(active_job=make_active_job("queued"))
        orchestrator = MikroTikProvisioningOrchestrator(repository)

        replacement = await create_replacement(orchestrator)

        assert repository.active_job["status"] == "failed"
        assert not repository.active_job.get("requires_manual_verification")
        assert replacement["artifact_checksum"] == "new-checksum"
        assert len(repository.created) == 1

    run(scenario())


def test_same_artifact_reuses_existing_active_job():
    async def scenario():
        active = make_active_job("dispatched", checksum="same-checksum")
        repository = FakeRepository(active_job=active)
        orchestrator = MikroTikProvisioningOrchestrator(repository)

        result = await orchestrator.get_or_create_provisioning_job(
            router_id="router-1",
            artifact_id="replacement-artifact",
            bundle_id="replacement-bundle",
            snapshot_id="replacement-snapshot",
            artifact_checksum="same-checksum",
        )

        assert result["job_id"] == "old-job"
        assert repository.created == []
        assert repository.active_job["status"] == "dispatched"

    run(scenario())

class ConcurrentCreateRepository(FakeRepository):
    """Simulate the database unique-index conflict for active router jobs."""

    def __init__(self):
        super().__init__()
        self.both_lookups_complete = asyncio.Event()

    async def get_active_for_router(self, router_id, job_type=None):
        # Snapshot before waiting so both racing requests see no active job.
        snapshot = None
        if (
            self.active_job
            and self.active_job.get("router_id") == router_id
            and self.active_job.get("status") in {"queued", "dispatched", "running"}
        ):
            snapshot = dict(self.active_job)

        self.active_lookup_calls += 1
        if self.active_lookup_calls >= 2:
            self.both_lookups_complete.set()
        await self.both_lookups_complete.wait()
        return snapshot

    async def create(self, document):
        if (
            self.active_job
            and self.active_job.get("router_id") == document.get("router_id")
            and self.active_job.get("status") in {"queued", "dispatched", "running"}
        ):
            raise ActiveProvisioningJobConflict(self.active_job)

        self.active_job = dict(document)
        self.created.append(dict(document))
        return dict(document)


def test_concurrent_same_artifact_requests_reuse_database_winner():
    async def scenario():
        repository = ConcurrentCreateRepository()
        orchestrator = MikroTikProvisioningOrchestrator(repository)

        results = await asyncio.gather(
            create_replacement(orchestrator),
            create_replacement(orchestrator),
        )

        assert len(repository.created) == 1
        assert results[0]["job_id"] == results[1]["job_id"]
        assert results[0]["artifact_checksum"] == "new-checksum"
        assert results[1]["artifact_checksum"] == "new-checksum"

    run(scenario())
