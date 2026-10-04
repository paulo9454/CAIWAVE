from backend.core.database import db


class ProvisioningRepository:
    collection = db.provisioning_logs

    @classmethod
    async def insert(cls, record: dict):
        return await cls.collection.insert_one(record)

    @classmethod
    async def find_one(cls, query: dict):
        return await cls.collection.find_one(query, {"_id": 0})

    @classmethod
    async def find(cls, query: dict, limit: int = 100):
        return await cls.collection.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).to_list(limit)

    @classmethod
    async def list_all(cls, limit: int = 100):
        return await cls.find({}, limit)

    @classmethod
    async def get(cls, router_id: str):
        return await cls.find_one(
            {
                "$or": [
                    {"router_id": router_id},
                    {"nas_identifier": router_id},
                ]
            }
        )


repository = ProvisioningRepository()
