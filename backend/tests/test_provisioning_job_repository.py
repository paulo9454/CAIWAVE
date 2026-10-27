import asyncio

import pytest

from pymongo.errors import DuplicateKeyError

from backend.services.provisioning.repository import (
    ActiveProvisioningJobConflict,
    ProvisioningJobNotFound,
    ProvisioningJobRepository,
)


class FakeCursor:
    def __init__(self, documents):
        self.documents = list(documents)

    def sort(self, field, direction):
        reverse = direction == -1
        self.documents.sort(
            key=lambda document: document.get(field),
            reverse=reverse,
        )
        return self

    async def to_list(self, length):
        return self.documents[:length]


class FakeResult:
    def __init__(self, deleted_count=0, matched_count=0):
        self.deleted_count = deleted_count
        self.matched_count = matched_count


class FakeCollection:
    def __init__(self):
        self.documents = []
        self.indexes = []

    async def create_index(self, *args, **kwargs):
        self.indexes.append((args, kwargs))
        return kwargs.get("name")

    async def find_one(self, query, projection=None):
        for document in self.documents:
            matches = True

            for key, value in query.items():
                if isinstance(value, dict) and "$in" in value:
                    if document.get(key) not in value["$in"]:
                        matches = False
                        break

                elif document.get(key) != value:
                    matches = False
                    break

            if matches:
                return dict(document)

        return None

    def find(self, query, projection=None):
        matches = []

        for document in self.documents:
            matches_document = True

            for key, value in query.items():
                if isinstance(value, dict) and "$in" in value:
                    if document.get(key) not in value["$in"]:
                        matches_document = False
                        break

                elif document.get(key) != value:
                    matches_document = False
                    break

            if matches_document:
                matches.append(dict(document))

        return FakeCursor(matches)

    async def insert_one(self, document):
        self.documents.append(dict(document))

    async def update_one(self, query, update):
        for document in self.documents:
            if all(
                document.get(key) == value
                for key, value in query.items()
            ):
                document.update(update.get("$set", {}))
                return FakeResult(matched_count=1)

        return FakeResult(matched_count=0)



    async def update_many(self, query, update):
        def matches(document, filters):
            for key, expected in filters.items():
                if key == "$or":
                    if not any(matches(document, branch) for branch in expected):
                        return False
                elif isinstance(expected, dict):
                    if "$in" in expected and document.get(key) not in expected["$in"]:
                        return False
                    if "$nin" in expected and document.get(key) in expected["$nin"]:
                        return False
                    if "$exists" in expected and ((key in document) != expected["$exists"]):
                        return False
                elif document.get(key) != expected:
                    return False
            return True

        count = 0
        for document in self.documents:
            if matches(document, query):
                document.update(update.get("$set", {}))
                count += 1
        return FakeResult(matched_count=count)


def build_repository():
    return ProvisioningJobRepository(FakeCollection())


def build_job():
    return {
        "job_id": "job-123",
        "router_id": "router-123",
        "status": "queued",
        "created_at": 100,
    }


def test_ensure_indexes():
    async def scenario():
        repository = build_repository()

        await repository.ensure_indexes()

        assert len(repository.collection.indexes) == 4

        names = {
            kwargs["name"]
            for _, kwargs in repository.collection.indexes
        }

        assert "uniq_provisioning_job_id" in names
        assert "provisioning_job_router_status_created" in names
        assert "provisioning_job_status_created" in names
        assert "uniq_active_control_job_per_router" in names

        active_index = next(
            kwargs for _, kwargs in repository.collection.indexes
            if kwargs["name"] == "uniq_active_control_job_per_router"
        )
        assert active_index["unique"] is True
        assert active_index["partialFilterExpression"] == {
            "active_control_job": True
        }

    asyncio.run(scenario())


def test_create_and_get_by_id():
    async def scenario():
        repository = build_repository()
        job = build_job()

        created = await repository.create(job)
        expected = {**job, "active_control_job": True}

        assert created == expected

        loaded = await repository.get_by_id("job-123")

        assert loaded == expected

    asyncio.run(scenario())


def test_get_by_id_returns_none_for_missing_job():
    async def scenario():
        repository = build_repository()

        result = await repository.get_by_id("missing")

        assert result is None

    asyncio.run(scenario())


def test_get_latest_for_router():
    async def scenario():
        repository = build_repository()

        await repository.create(
            {
                "job_id": "job-old",
                "router_id": "router-123",
                "status": "failed",
                "created_at": 100,
            }
        )

        await repository.create(
            {
                "job_id": "job-new",
                "router_id": "router-123",
                "status": "queued",
                "created_at": 200,
            }
        )

        latest = await repository.get_latest_for_router("router-123")

        assert latest["job_id"] == "job-new"

    asyncio.run(scenario())

def test_get_active_for_router():
    async def scenario():
        repository = build_repository()

        await repository.create(
            {
                "job_id": "job-failed",
                "router_id": "router-123",
                "status": "failed",
                "created_at": 300,
            }
        )

        await repository.create(
            {
                "job_id": "job-running",
                "router_id": "router-123",
                "status": "running",
                "created_at": 200,
            }
        )

        await repository.create(
            {
                "job_id": "job-queued",
                "router_id": "router-123",
                "status": "queued",
                "created_at": 100,
            }
        )

        active = await repository.get_active_for_router("router-123")

        assert active is not None
        assert active["job_id"] == "job-running"

        no_active = await repository.get_active_for_router("router-456")

        assert no_active is None

    asyncio.run(scenario())

def test_update_job():
    async def scenario():
        repository = build_repository()
        job = build_job()

        await repository.create(job)

        updated = await repository.update(
            "job-123",
            {
                "status": "running",
                "attempts": 1,
            },
        )

        assert updated["status"] == "running"
        assert updated["attempts"] == 1

    asyncio.run(scenario())


def test_update_if_status_updates_only_when_expected_status_matches():
    async def scenario():
        repository = build_repository()
        await repository.create(build_job())

        updated = await repository.update_if_status(
            "job-123",
            "queued",
            {"status": "dispatched"},
        )

        assert updated is not None
        assert updated["status"] == "dispatched"

        stale_update = await repository.update_if_status(
            "job-123",
            "queued",
            {"status": "failed"},
        )

        assert stale_update is None
        stored = await repository.get_by_id("job-123")
        assert stored["status"] == "dispatched"

    asyncio.run(scenario())


def test_update_if_status_returns_none_for_missing_job():
    async def scenario():
        repository = build_repository()

        updated = await repository.update_if_status(
            "missing",
            "queued",
            {"status": "failed"},
        )

        assert updated is None

    asyncio.run(scenario())


def test_update_missing_job_raises():
    async def scenario():
        repository = build_repository()

        with pytest.raises(ProvisioningJobNotFound):
            await repository.update(
                "missing",
                {
                    "status": "failed",
                },
            )

    asyncio.run(scenario())


def test_list_by_status():
    async def scenario():
        repository = build_repository()

        await repository.create(
            {
                "job_id": "job-1",
                "router_id": "router-1",
                "status": "queued",
                "created_at": 100,
            }
        )

        await repository.create(
            {
                "job_id": "job-2",
                "router_id": "router-2",
                "status": "failed",
                "created_at": 200,
            }
        )

        await repository.create(
            {
                "job_id": "job-3",
                "router_id": "router-3",
                "status": "queued",
                "created_at": 300,
            }
        )

        queued = await repository.list_by_status("queued")

        assert [item["job_id"] for item in queued] == [
            "job-1",
            "job-3",
        ]

    asyncio.run(scenario())

def test_claim_next_for_router():
    import asyncio
    from datetime import datetime, timezone

    class FakeCollection:
        def __init__(self):
            now = datetime.now(timezone.utc)
            self.jobs = [
                {
                    "job_id": "job-claim-1",
                    "router_id": "router-1",
                    "status": "queued",
                    "created_at": now,
                }
            ]

        async def find_one_and_update(
            self,
            query,
            update,
            sort=None,
            projection=None,
            return_document=None,
        ):
            for job in self.jobs:
                if (
                    job["router_id"] == query["router_id"]
                    and job["status"] == query["status"]
                ):
                    job.update(update["$set"])
                    return dict(job)
            return None

    async def run():
        repository = ProvisioningJobRepository(FakeCollection())

        claimed = await repository.claim_next_for_router("router-1")

        assert claimed is not None
        assert claimed["job_id"] == "job-claim-1"
        assert claimed["status"] == "dispatched"
        assert "dispatched_at" in claimed

        second_claim = await repository.claim_next_for_router("router-1")
        assert second_claim is None

    asyncio.run(run())

def test_claim_provisioning_job_accepts_legacy_missing_job_type():
    import asyncio
    from datetime import datetime, timezone

    class FakeCollection:
        def __init__(self):
            self.jobs = [
                {
                    "job_id": "legacy-provisioning",
                    "router_id": "router-legacy",
                    "status": "queued",
                    "created_at": datetime.now(timezone.utc),
                }
            ]

        async def find_one_and_update(
            self,
            query,
            update,
            sort=None,
            projection=None,
            return_document=None,
        ):
            for job in self.jobs:
                if (
                    job["router_id"] != query["router_id"]
                    or job["status"] != query["status"]
                ):
                    continue

                if "job_type" in query:
                    expected = query["job_type"]

                    if isinstance(expected, dict):
                        if "$exists" in expected:
                            exists = "job_type" in job
                            if exists != expected["$exists"]:
                                continue
                    elif job.get("job_type") != expected:
                        continue

                job.update(update["$set"])
                return dict(job)

            return None

    async def run():
        repository = ProvisioningJobRepository(FakeCollection())

        claimed = await repository.claim_next_for_router(
            "router-legacy",
            job_type="provisioning",
        )

        assert claimed is not None
        assert claimed["job_id"] == "legacy-provisioning"
        assert claimed["status"] == "dispatched"
        assert claimed["job_type"] == "provisioning"

    asyncio.run(run())


def test_claim_provisioning_job_does_not_claim_rotation_job():
    import asyncio
    from datetime import datetime, timezone

    class FakeCollection:
        def __init__(self):
            self.jobs = [
                {
                    "job_id": "rotation-job",
                    "router_id": "router-rotation",
                    "job_type": "control_credential_rotation",
                    "status": "queued",
                    "created_at": datetime.now(timezone.utc),
                }
            ]

        async def find_one_and_update(
            self,
            query,
            update,
            sort=None,
            projection=None,
            return_document=None,
        ):
            for job in self.jobs:
                if (
                    job["router_id"] == query["router_id"]
                    and job["status"] == query["status"]
                    and job.get("job_type") == query.get("job_type")
                ):
                    job.update(update["$set"])
                    return dict(job)

            return None

    async def run():
        repository = ProvisioningJobRepository(FakeCollection())

        claimed = await repository.claim_next_for_router(
            "router-rotation",
            job_type="provisioning",
        )

        assert claimed is None

    asyncio.run(run())


def test_get_active_for_router_includes_legacy_provisioning_jobs():
    async def scenario():
        repository = build_repository()

        await repository.create({
            "job_id": "rotation-job",
            "router_id": "router-legacy-check",
            "job_type": "control_credential_rotation",
            "status": "running",
            "created_at": 300,
        })
        await repository.create({
            "job_id": "legacy-provisioning",
            "router_id": "router-legacy-check",
            "status": "dispatched",
            "created_at": 200,
        })
        await repository.create({
            "job_id": "typed-provisioning",
            "router_id": "router-legacy-check",
            "job_type": "provisioning",
            "status": "queued",
            "created_at": 100,
        })

        active = await repository.get_active_for_router(
            "router-legacy-check",
            job_type="provisioning",
        )

        assert active is not None
        assert active["job_id"] == "legacy-provisioning"

    asyncio.run(scenario())


def test_get_manual_verification_for_router_returns_flagged_job():
    async def scenario():
        repository = build_repository()

        await repository.create({
            "job_id": "normal-job",
            "router_id": "router-review-check",
            "status": "failed",
            "requires_manual_verification": False,
            "created_at": 300,
        })
        await repository.create({
            "job_id": "flagged-job",
            "router_id": "router-review-check",
            "status": "failed",
            "requires_manual_verification": True,
            "created_at": 200,
        })
        await repository.create({
            "job_id": "other-router-flagged",
            "router_id": "another-router",
            "status": "failed",
            "requires_manual_verification": True,
            "created_at": 400,
        })

        flagged = await repository.get_manual_verification_for_router(
            "router-review-check"
        )

        assert flagged is not None
        assert flagged["job_id"] == "flagged-job"
        assert flagged["requires_manual_verification"] is True

    asyncio.run(scenario())


def test_claim_queued_job_for_router_claims_only_the_requested_legacy_job():
    from datetime import datetime, timezone

    class ClaimCollection:
        def __init__(self):
            self.jobs = [
                {
                    "job_id": "another-queued-job",
                    "router_id": "router-exact-claim",
                    "job_type": "provisioning",
                    "status": "queued",
                    "created_at": 100,
                },
                {
                    "job_id": "requested-legacy-job",
                    "router_id": "router-exact-claim",
                    "status": "queued",
                    "created_at": 200,
                },
            ]

        async def find_one_and_update(
            self,
            query,
            update,
            sort=None,
            projection=None,
            return_document=None,
        ):
            for job in self.jobs:
                matches = True

                for key, expected in query.items():
                    if isinstance(expected, dict) and "$exists" in expected:
                        if (key in job) != expected["$exists"]:
                            matches = False
                            break
                    elif job.get(key) != expected:
                        matches = False
                        break

                if matches:
                    job.update(update["$set"])
                    return dict(job)

            return None

    async def scenario():
        repository = ProvisioningJobRepository(ClaimCollection())

        claimed = await repository.claim_queued_job_for_router(
            "router-exact-claim",
            "requested-legacy-job",
            job_type="provisioning",
        )

        assert claimed is not None
        assert claimed["job_id"] == "requested-legacy-job"
        assert claimed["job_type"] == "provisioning"
        assert claimed["status"] == "dispatched"

        jobs = repository.collection.jobs
        other_job = next(
            job for job in jobs
            if job["job_id"] == "another-queued-job"
        )
        assert other_job["status"] == "queued"

        # The same job cannot be claimed again after it has been dispatched.
        second_claim = await repository.claim_queued_job_for_router(
            "router-exact-claim",
            "requested-legacy-job",
            job_type="provisioning",
        )
        assert second_claim is None

    asyncio.run(scenario())

def test_active_job_unique_conflict_returns_existing_job():
    class UniqueIndexFakeCollection(FakeCollection):
        async def insert_one(self, document):
            if document.get("active_control_job"):
                for existing in self.documents:
                    if (
                        existing.get("active_control_job") is True
                        and existing.get("router_id") == document.get("router_id")
                    ):
                        raise DuplicateKeyError(
                            "E11000 duplicate key error "
                            "index: uniq_active_control_job_per_router",
                            details={"keyPattern": {"router_id": 1}},
                        )
            await super().insert_one(document)

    async def scenario():
        repository = ProvisioningJobRepository(UniqueIndexFakeCollection())

        first = {
            "job_id": "winner-job",
            "router_id": "router-unique-test",
            "job_type": "provisioning",
            "status": "queued",
            "artifact_checksum": "same-checksum",
            "created_at": 100,
        }
        second = {
            "job_id": "racing-job",
            "router_id": "router-unique-test",
            "job_type": "provisioning",
            "status": "queued",
            "artifact_checksum": "same-checksum",
            "created_at": 101,
        }

        await repository.create(first)

        with pytest.raises(ActiveProvisioningJobConflict) as caught:
            await repository.create(second)

        assert caught.value.active_job is not None
        assert caught.value.active_job["job_id"] == "winner-job"
        assert len(repository.collection.documents) == 1

        # A terminal transition releases the router's active-job slot.
        updated = await repository.update_if_status(
            "winner-job",
            "queued",
            {"status": "failed"},
        )
        assert updated is not None
        assert updated["active_control_job"] is False

        replacement = await repository.create(second)
        assert replacement["job_id"] == "racing-job"
        assert replacement["active_control_job"] is True

    asyncio.run(scenario())
