from backend.core.database import db


class ProvisioningRepository:
    collection = db.provisioning_logs

    @staticmethod
    async def save(record: dict):
        """Persist a provisioning record and wait for MongoDB to acknowledge it."""
        return await db.provisioning_logs.insert_one(record)

    @staticmethod
    async def find_one(query: dict):
        return await db.provisioning_logs.find_one(query, {"_id": 0})

    @staticmethod
    async def find(query: dict, limit: int = 100):
        return await db.provisioning_logs.find(query).to_list(limit)


repository = ProvisioningRepository()
