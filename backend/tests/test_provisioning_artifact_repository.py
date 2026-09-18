import asyncio
from datetime import datetime, timezone

from backend.services.provisioning.artifact_repository import (
    ProvisioningArtifactRepository,
    ProvisioningArtifactNotFound,
)


class FakeCursor:
    def __init__(self, documents):
        self.documents = list(documents)

    def sort(self, field, direction):
        reverse = direction == -1
        self.documents.sort(
            key=lambda item: item.get(field),
            reverse=reverse,
        )
        return self

    async def to_list(self, length):
        return self.documents[:length]


class FakeCollection:
    def __init__(self):
        self.documents = []
        self.indexes = []

    async def create_index(self, *args, **kwargs):
        self.indexes.append((args, kwargs))

    async def find_one(self, query, projection=None):
        for document in self.documents:
            if all(document.get(k) == v for k, v in query.items()):
                return {
                    key: value
                    for key, value in document.items()
                    if key != "_id"
                }
        return None

    async def insert_one(self, document):
        self.documents.append(dict(document))

    def find(self, query, projection=None):
        matches = [
            {
                key: value
                for key, value in document.items()
                if key != "_id"
            }
            for document in self.documents
            if all(document.get(k) == v for k, v in query.items())
        ]
        return FakeCursor(matches)


def test_ensure_indexes():
    async def run():
        collection = FakeCollection()
        repository = ProvisioningArtifactRepository(collection)

        await repository.ensure_indexes()

        assert len(collection.indexes) == 3
        assert collection.indexes[0][1]["unique"] is True

    asyncio.run(run())


def test_create_and_get_by_id():
    async def run():
        collection = FakeCollection()
        repository = ProvisioningArtifactRepository(collection)

        document = {
            "artifact_id": "artifact:test-1",
            "router_id": "router-1",
            "bundle_id": "bundle:test-1",
            "snapshot_id": "snapshot:test-1",
            "content": "/ip address print",
            "checksum": "abc123",
            "filename": "router-1.rsc",
            "content_type": "text/routeros-script",
            "created_at": datetime.now(timezone.utc),
        }

        created = await repository.create(document)

        assert created["artifact_id"] == "artifact:test-1"
        assert created["content"] == "/ip address print"

        fetched = await repository.get_by_id("artifact:test-1")

        assert fetched is not None
        assert fetched["checksum"] == "abc123"

    asyncio.run(run())


def test_create_adds_created_at_when_missing():
    async def run():
        collection = FakeCollection()
        repository = ProvisioningArtifactRepository(collection)

        document = {
            "artifact_id": "artifact:test-2",
            "router_id": "router-1",
            "checksum": "def456",
        }

        created = await repository.create(document)

        assert "created_at" in created
        assert created["created_at"].tzinfo is not None

    asyncio.run(run())


def test_get_by_checksum():
    async def run():
        collection = FakeCollection()
        repository = ProvisioningArtifactRepository(collection)

        await repository.create({
            "artifact_id": "artifact:test-3",
            "router_id": "router-1",
            "checksum": "checksum-123",
        })

        result = await repository.get_by_checksum("checksum-123")

        assert result is not None
        assert result["artifact_id"] == "artifact:test-3"

        missing = await repository.get_by_checksum("does-not-exist")

        assert missing is None

    asyncio.run(run())


def test_list_by_router_returns_newest_first():
    async def run():
        collection = FakeCollection()
        repository = ProvisioningArtifactRepository(collection)

        older = datetime(2026, 1, 1, tzinfo=timezone.utc)
        newer = datetime(2026, 1, 2, tzinfo=timezone.utc)

        await repository.create({
            "artifact_id": "artifact:old",
            "router_id": "router-1",
            "checksum": "old",
            "created_at": older,
        })

        await repository.create({
            "artifact_id": "artifact:new",
            "router_id": "router-1",
            "checksum": "new",
            "created_at": newer,
        })

        results = await repository.list_by_router("router-1")

        assert len(results) == 2
        assert results[0]["artifact_id"] == "artifact:new"
        assert results[1]["artifact_id"] == "artifact:old"

    asyncio.run(run())
