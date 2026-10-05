import asyncio

from backend.services.mikrotik_control_plane.provisioning import (
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

    async def update(self, document):
        for index, existing in enumerate(self.collection.documents):
            if existing.get("job_id") == document.get("job_id"):
                self.collection.documents[index] = dict(document)
                return document

        raise AssertionError("job not found")


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
