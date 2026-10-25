import asyncio

from backend.services.mikrotik_control_plane.provisioning import (
    MikroTikProvisioningOrchestrationError,
    MikroTikProvisioningOrchestrator,
)


class FakeCursor:
    def __init__(self, documents):
        self.documents = documents

    def sort(self, *args, **kwargs):
        return self

    async def to_list(self, length):
        return self.documents[:length]


class FakeCollection:
    def __init__(self):
        self.documents = []

    async def insert_one(self, document):
        self.documents.append(dict(document))

    async def find_one(self, query, projection=None):
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                return dict(document)
        return None

    def find(self, query, projection=None):
        matches = []

        for document in self.documents:
            matched = True

            for key, value in query.items():
                if isinstance(value, dict) and "$in" in value:
                    if document.get(key) not in value["$in"]:
                        matched = False
                        break
                elif document.get(key) != value:
                    matched = False
                    break

            if matched:
                matches.append(dict(document))

        return FakeCursor(matches)


class FakeRepository:
    def __init__(self):
        self.collection = FakeCollection()
        self.conflict_on_conditional_update = False

    async def get_manual_verification_for_router(self, router_id):
        jobs = await self.collection.find(
            {
                "router_id": router_id,
                "requires_manual_verification": True,
            }
        ).to_list(1)
        return jobs[0] if jobs else None

    async def get_active_for_router(self, router_id):
        jobs = await self.collection.find(
            {
                "router_id": router_id,
                "status": {
                    "$in": [
                        "queued",
                        "dispatched",
                        "running",
                    ],
                },
            }
        ).to_list(1)

        return jobs[0] if jobs else None

    async def create(self, document):
        await self.collection.insert_one(document)
        return document

    async def update(self, job_id, updates):
        for index, existing in enumerate(self.collection.documents):
            if existing.get("job_id") == job_id:
                updated = dict(existing)
                updated.update(updates)
                self.collection.documents[index] = updated
                return updated

        raise AssertionError("job not found")

    async def update_if_status(self, job_id, expected_status, updates):
        for index, existing in enumerate(self.collection.documents):
            if existing.get("job_id") != job_id:
                continue

            # Simulate another process changing the job after it was read.
            if self.conflict_on_conditional_update:
                changed = dict(existing)
                changed["status"] = "succeeded"
                self.collection.documents[index] = changed
                return None

            if existing.get("status") != expected_status:
                return None

            updated = dict(existing)
            updated.update(updates)
            self.collection.documents[index] = updated
            return updated

        return None

def test_creates_queued_job_when_no_active_job_exists():
    async def scenario():
        repository = FakeRepository()
        orchestrator = MikroTikProvisioningOrchestrator(repository)

        job = await orchestrator.get_or_create_provisioning_job(
            router_id="router-1",
            artifact_id="artifact-1",
            bundle_id="bundle-1",
            snapshot_id="snapshot-1",
            artifact_checksum="checksum-1",
        )

        assert job["router_id"] == "router-1"
        assert job["artifact_id"] == "artifact-1"
        assert job["bundle_id"] == "bundle-1"
        assert job["snapshot_id"] == "snapshot-1"
        assert job["artifact_checksum"] == "checksum-1"
        assert job["status"] == "queued"
        assert job["attempts"] == 0
        assert len(repository.collection.documents) == 1

    asyncio.run(scenario())


def test_reuses_active_job_when_artifact_checksum_is_unchanged():
    async def scenario():
        repository = FakeRepository()
        orchestrator = MikroTikProvisioningOrchestrator(repository)

        first_job = await orchestrator.get_or_create_provisioning_job(
            router_id="router-1",
            artifact_id="artifact-1",
            bundle_id="bundle-1",
            snapshot_id="snapshot-1",
            artifact_checksum="checksum-1",
        )

        second_job = await orchestrator.get_or_create_provisioning_job(
            router_id="router-1",
            artifact_id="artifact-1",
            bundle_id="bundle-1",
            snapshot_id="snapshot-1",
            artifact_checksum="checksum-1",
        )

        assert second_job["job_id"] == first_job["job_id"]
        assert second_job["artifact_checksum"] == "checksum-1"
        assert second_job["status"] == "queued"
        assert len(repository.collection.documents) == 1

    asyncio.run(scenario())


def test_supersedes_active_job_when_artifact_checksum_changes():
    async def scenario():
        repository = FakeRepository()
        orchestrator = MikroTikProvisioningOrchestrator(repository)

        first_job = await orchestrator.get_or_create_provisioning_job(
            router_id="router-1",
            artifact_id="artifact-1",
            bundle_id="bundle-1",
            snapshot_id="snapshot-1",
            artifact_checksum="checksum-1",
        )

        second_job = await orchestrator.get_or_create_provisioning_job(
            router_id="router-1",
            artifact_id="artifact-2",
            bundle_id="bundle-2",
            snapshot_id="snapshot-2",
            artifact_checksum="checksum-2",
        )

        assert second_job["job_id"] != first_job["job_id"]
        assert second_job["artifact_id"] == "artifact-2"
        assert second_job["bundle_id"] == "bundle-2"
        assert second_job["snapshot_id"] == "snapshot-2"
        assert second_job["artifact_checksum"] == "checksum-2"
        assert second_job["status"] == "queued"

        stored_jobs = repository.collection.documents
        assert len(stored_jobs) == 2

        old_job = next(
            job for job in stored_jobs
            if job["job_id"] == first_job["job_id"]
        )

        assert old_job["status"] == "failed"
        assert old_job["last_error"] == (
            "Superseded by newer provisioning artifact"
        )

    asyncio.run(scenario())


def test_does_not_create_replacement_if_active_job_changes_concurrently():
    async def scenario():
        repository = FakeRepository()
        orchestrator = MikroTikProvisioningOrchestrator(repository)

        first_job = await orchestrator.get_or_create_provisioning_job(
            router_id="router-1",
            artifact_id="artifact-1",
            bundle_id="bundle-1",
            snapshot_id="snapshot-1",
            artifact_checksum="checksum-1",
        )

        repository.conflict_on_conditional_update = True

        try:
            await orchestrator.get_or_create_provisioning_job(
                router_id="router-1",
                artifact_id="artifact-2",
                bundle_id="bundle-2",
                snapshot_id="snapshot-2",
                artifact_checksum="checksum-2",
            )
        except MikroTikProvisioningOrchestrationError as exc:
            assert "changed during supersession" in str(exc)
        else:
            raise AssertionError("Expected supersession conflict")

        stored_jobs = repository.collection.documents
        assert len(stored_jobs) == 1
        assert stored_jobs[0]["job_id"] == first_job["job_id"]
        assert stored_jobs[0]["status"] == "succeeded"

    asyncio.run(scenario())


def test_manual_verification_gate_blocks_new_provisioning_jobs():
    async def scenario():
        repository = FakeRepository()
        repository.collection.documents.append({
            "job_id": "job-needs-check",
            "router_id": "router-1",
            "status": "failed",
            "requires_manual_verification": True,
            "created_at": 100,
        })
        orchestrator = MikroTikProvisioningOrchestrator(repository)

        try:
            await orchestrator.get_or_create_provisioning_job(
                router_id="router-1",
                artifact_id="new-artifact",
                bundle_id="new-bundle",
                snapshot_id="new-snapshot",
                artifact_checksum="new-checksum",
            )
        except MikroTikProvisioningOrchestrationError as exc:
            assert "manual router verification" in str(exc).lower()
        else:
            raise AssertionError("Expected manual verification to block creation")

        assert len(repository.collection.documents) == 1
        assert repository.collection.documents[0]["requires_manual_verification"] is True

    asyncio.run(scenario())
