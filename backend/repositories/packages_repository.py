from repositories.base_repository import BaseRepository


class PackagesRepository(BaseRepository):
    collection_name = "packages"

    @classmethod
    async def find_active_sorted(cls, limit: int = 100):
        return await cls.collection().find(
            {"is_active": True},
            {"_id": 0}
        ).sort("price", 1).to_list(limit)

    @classmethod
    async def find_one(cls, query: dict):
        return await cls.collection().find_one(query)

    @classmethod
    async def insert(cls, data: dict):
        return await cls.collection().insert_one(data)
