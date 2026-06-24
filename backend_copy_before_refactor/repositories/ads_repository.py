from backend.repositories.base_repository import BaseRepository


class AdsRepository(BaseRepository):
    collection_name = "ads"

    @classmethod
    async def find_active(cls, limit: int = 50):
        return await cls.collection().find(
            {"is_active": True},
            {"_id": 0}
        ).to_list(limit)

    @classmethod
    async def find_one(cls, query: dict):
        return await cls.collection().find_one(query)

    @classmethod
    async def insert(cls, data: dict):
        return await cls.collection().insert_one(data)
