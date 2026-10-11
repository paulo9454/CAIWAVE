from backend.core.database import db
from pymongo.errors import DuplicateKeyError


class ProvisioningRepository:
    collection = db.provisioning_logs

    @staticmethod
    async def save(record: dict):
        """Persist a record idempotently and return the authoritative stored record."""
        try:
            await db.provisioning_logs.insert_one(record)
            return record
        except DuplicateKeyError:
            # A prior insert may have succeeded before its caller was cancelled.
            existing = await db.provisioning_logs.find_one(
                {"_id": record["_id"]}
            )
            if existing is None:
                raise
            return existing

    @staticmethod
    async def find_one(query: dict):
        return await db.provisioning_logs.find_one(query, {"_id": 0})

    @staticmethod
    async def find(query: dict, limit: int = 100):
        return await db.provisioning_logs.find(query).to_list(limit)


repository = ProvisioningRepository()
