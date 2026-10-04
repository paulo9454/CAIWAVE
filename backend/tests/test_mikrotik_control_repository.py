import asyncio

from backend.services.mikrotik_control_plane.repository import (
    RouterControlCredentialRepository,
)


class FakeResult:
    def __init__(self, matched_count=1):
        self.matched_count = matched_count


class FakeCollection:
    def __init__(self):
        self.documents = []
        self.indexes = []

    async def create_index(self, field, **kwargs):
        self.indexes.append((field, kwargs))
        return kwargs.get("name")

    async def find_one(self, query, projection=None):
        for document in self.documents:
            if all(document.get(k) == v for k, v in query.items()):
                return dict(document)
        return None

    def find(self, query, projection=None):
        matching = [
            dict(document)
            for document in self.documents
            if all(document.get(k) == v for k, v in query.items())
        ]

        class FakeCursor:
            def __init__(self, documents):
                self.documents = documents

            async def to_list(self, length=None):
                return self.documents

        return FakeCursor(matching)

    async def insert_one(self, document):
        self.documents.append(dict(document))

    async def update_one(self, query, update):
        for document in self.documents:
            if all(document.get(k) == v for k, v in query.items()):
                document.update(update.get("$set", {}))
                return FakeResult(1)

        return FakeResult(0)


def test_repository_creates_required_indexes():
    async def run():
        collection = FakeCollection()
        repository = RouterControlCredentialRepository(collection)

        await repository.ensure_indexes()

        names = [options["name"] for _, options in collection.indexes]

        assert "uniq_router_control_credential_id" in names
        assert "uniq_active_router_control_router_id" in names
        assert "router_control_credential_expiry" in names

    asyncio.run(run())


def test_create_and_get_by_id():
    async def run():
        collection = FakeCollection()
        repository = RouterControlCredentialRepository(collection)

        document = {
            "credential_id": "credential-1",
            "router_id": "router-1",
            "secret_hash": "hash-1",
            "status": "active",
            "created_at": "2026-09-06T12:00:00+00:00",
            "expires_at": "2026-10-06T12:00:00+00:00",
        }

        created = await repository.create(document)

        assert created["credential_id"] == "credential-1"
        assert created["router_id"] == "router-1"

        found = await repository.get_by_id("credential-1")

        assert found["credential_id"] == "credential-1"

    asyncio.run(run())


def test_get_by_router_id():
    async def run():
        collection = FakeCollection()
        repository = RouterControlCredentialRepository(collection)

        document = {
            "credential_id": "credential-2",
            "router_id": "router-2",
            "secret_hash": "hash-2",
            "status": "active",
            "created_at": "2026-09-06T12:00:00+00:00",
            "expires_at": "2026-10-06T12:00:00+00:00",
        }

        await repository.create(document)

        found = await repository.get_by_router_id("router-2")

        assert found["credential_id"] == "credential-2"

    asyncio.run(run())

def test_get_active_credentials():
    async def run():
        collection = FakeCollection()
        repository = RouterControlCredentialRepository(collection)

        active = {
            "credential_id": "credential-active",
            "router_id": "router-active",
            "secret_hash": "active-hash",
            "status": "active",
            "created_at": "2026-09-06T12:00:00+00:00",
            "expires_at": "2026-10-06T12:00:00+00:00",
        }

        revoked = {
            "credential_id": "credential-revoked",
            "router_id": "router-revoked",
            "secret_hash": "revoked-hash",
            "status": "revoked",
            "created_at": "2026-09-06T12:00:00+00:00",
            "expires_at": "2026-10-06T12:00:00+00:00",
        }

        await repository.create(active)
        await repository.create(revoked)

        credentials = await repository.get_active_credentials()

        assert len(credentials) == 1
        assert credentials[0]["credential_id"] == "credential-active"

    asyncio.run(run())

def test_get_active_and_pending_credentials():
    async def run():
        collection = FakeCollection()
        repository = RouterControlCredentialRepository(collection)

        active = {
            "credential_id": "credential-active",
            "router_id": "router-active",
            "secret_hash": "active-hash",
            "status": "active",
            "created_at": "2026-09-06T12:00:00+00:00",
            "expires_at": "2026-10-06T12:00:00+00:00",
        }

        pending = {
            "credential_id": "credential-pending",
            "router_id": "router-pending",
            "secret_hash": "pending-hash",
            "status": "pending",
            "created_at": "2026-09-06T12:00:00+00:00",
            "expires_at": "2026-10-06T12:00:00+00:00",
        }

        revoked = {
            "credential_id": "credential-revoked",
            "router_id": "router-revoked",
            "secret_hash": "revoked-hash",
            "status": "revoked",
            "created_at": "2026-09-06T12:00:00+00:00",
            "expires_at": "2026-10-06T12:00:00+00:00",
        }

        await repository.create(active)
        await repository.create(pending)
        await repository.create(revoked)

        credentials = await repository.get_active_and_pending_credentials()

        assert len(credentials) == 2
        assert {
            credential["credential_id"]
            for credential in credentials
        } == {
            "credential-active",
            "credential-pending",
        }

    asyncio.run(run())

def test_get_missing_credential_returns_none():
    async def run():
        collection = FakeCollection()
        repository = RouterControlCredentialRepository(collection)

        assert await repository.get_by_id("missing") is None

    asyncio.run(run())


def test_revoke_marks_credential_revoked():
    async def run():
        collection = FakeCollection()
        repository = RouterControlCredentialRepository(collection)

        document = {
            "credential_id": "credential-3",
            "router_id": "router-3",
            "secret_hash": "hash-3",
            "status": "active",
            "created_at": "2026-09-06T12:00:00+00:00",
            "expires_at": "2026-10-06T12:00:00+00:00",
        }

        await repository.create(document)

        result = await repository.revoke(
            "credential-3",
            "2026-09-06T13:00:00+00:00",
        )

        assert result is True

        found = await repository.get_by_id("credential-3")

        assert found["status"] == "revoked"
        assert found["revoked_at"] == "2026-09-06T13:00:00+00:00"

    asyncio.run(run())


def test_revoke_missing_credential_returns_false():
    async def run():
        collection = FakeCollection()
        repository = RouterControlCredentialRepository(collection)

        result = await repository.revoke(
            "missing",
            "2026-09-06T13:00:00+00:00",
        )

        assert result is False

    asyncio.run(run())


def test_rotate_supersedes_existing_credential():
    async def run():
        collection = FakeCollection()
        repository = RouterControlCredentialRepository(collection)

        first = {
            "credential_id": "credential-old",
            "router_id": "router-4",
            "secret_hash": "old-hash",
            "status": "active",
            "created_at": "2026-09-06T12:00:00+00:00",
            "expires_at": "2026-10-06T12:00:00+00:00",
        }

        second = {
            "credential_id": "credential-new",
            "router_id": "router-4",
            "secret_hash": "new-hash",
            "status": "active",
            "created_at": "2026-09-06T13:00:00+00:00",
            "expires_at": "2026-10-06T13:00:00+00:00",
        }

        await repository.create(first)

        created = await repository.rotate(
            "router-4",
            second,
        )

        assert created["credential_id"] == "credential-new"

        old = await repository.get_by_id("credential-old")

        assert old["status"] == "superseded"
        assert old["superseded_by"] == "credential-new"

    asyncio.run(run())

def test_replace_pending_supersedes_old_pending_and_keeps_active():
    async def run():
        collection = FakeCollection()
        repository = RouterControlCredentialRepository(collection)

        active = {
            "credential_id": "credential-active",
            "router_id": "router-replace",
            "secret_hash": "active-hash",
            "status": "active",
            "created_at": "2026-10-01T10:00:00+00:00",
            "expires_at": "2026-10-31T10:00:00+00:00",
        }

        old_pending = {
            "credential_id": "credential-pending-old",
            "router_id": "router-replace",
            "secret_hash": "old-pending-hash",
            "status": "pending",
            "created_at": "2026-10-02T10:00:00+00:00",
            "expires_at": "2026-11-01T10:00:00+00:00",
        }

        new_pending = {
            "credential_id": "credential-pending-new",
            "router_id": "router-replace",
            "secret_hash": "new-pending-hash",
            "status": "pending",
            "created_at": "2026-10-03T10:00:00+00:00",
            "expires_at": "2026-11-02T10:00:00+00:00",
        }

        await repository.create(active)
        await repository.create(old_pending)

        created = await repository.replace_pending(
            router_id="router-replace",
            document=new_pending,
            replaced_at="2026-10-03T10:00:00+00:00",
        )

        assert created["credential_id"] == "credential-pending-new"
        assert created["status"] == "pending"

        stored_active = await repository.get_by_id("credential-active")
        stored_old_pending = await repository.get_by_id(
            "credential-pending-old"
        )
        stored_new_pending = await repository.get_by_id(
            "credential-pending-new"
        )

        assert stored_active["status"] == "active"

        assert stored_old_pending["status"] == "superseded"
        assert stored_old_pending["superseded_at"] == (
            "2026-10-03T10:00:00+00:00"
        )
        assert stored_old_pending["superseded_by"] == (
            "credential-pending-new"
        )

        assert stored_new_pending["status"] == "pending"

    asyncio.run(run())

def test_promote_pending_supersedes_active_and_activates_pending():
    async def run():
        collection = FakeCollection()
        repository = RouterControlCredentialRepository(collection)

        active = {
            "credential_id": "credential-old",
            "router_id": "router-1",
            "secret_hash": "old-hash",
            "status": "active",
            "created_at": "2026-09-20T10:00:00+00:00",
            "expires_at": "2026-10-20T10:00:00+00:00",
        }

        pending = {
            "credential_id": "credential-new",
            "router_id": "router-1",
            "secret_hash": "new-hash",
            "status": "pending",
            "created_at": "2026-09-20T11:00:00+00:00",
            "expires_at": "2026-10-20T11:00:00+00:00",
        }

        await repository.create(active)
        await repository.create(pending)

        promoted = await repository.promote_pending(
            "router-1",
            "credential-new",
            "2026-09-20T12:00:00+00:00",
        )

        assert promoted["credential_id"] == "credential-new"
        assert promoted["status"] == "active"
        assert promoted["activated_at"] == "2026-09-20T12:00:00+00:00"

        old = await repository.get_by_id("credential-old")

        assert old["status"] == "superseded"
        assert old["superseded_at"] == "2026-09-20T12:00:00+00:00"
        assert old["superseded_by"] == "credential-new"

    asyncio.run(run())
