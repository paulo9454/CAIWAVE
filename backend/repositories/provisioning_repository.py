from repositories.base_repository import BaseRepository


class ProvisioningRepository(BaseRepository):
    collection_name = "provisioning_logs"

    @classmethod
    async def insert(cls, record: dict):
        return await cls.collection().insert_one(record)

    @classmethod
    async def find_one(cls, query: dict):
        return await cls.collection().find_one(query, {"_id": 0})

    @classmethod
    async def find(cls, query: dict, limit: int = 100):
        return await cls.collection().find(query, {"_id": 0}).to_list(limit)
