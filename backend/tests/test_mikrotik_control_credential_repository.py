import asyncio

from backend.services.mikrotik_control_plane.repository import (
    RouterControlCredentialRepository,
)


class RecordingCollection:
    def __init__(self):
        self.indexes = []

    async def create_index(self, keys, **kwargs):
        self.indexes.append((keys, kwargs))


def test_ensure_indexes_enforces_unique_pending_credential_per_router():
    async def run():
        collection = RecordingCollection()
        repository = RouterControlCredentialRepository(collection)

        await repository.ensure_indexes()

        pending_indexes = [
            (keys, options)
            for keys, options in collection.indexes
            if options.get("name") == "uniq_pending_router_control_router_id"
        ]

        assert len(pending_indexes) == 1
        keys, options = pending_indexes[0]
        assert keys == "router_id"
        assert options["unique"] is True
        assert options["partialFilterExpression"] == {"status": "pending"}

    asyncio.run(run())
