from repositories.base_repository import BaseRepository


class RadiusRepository(BaseRepository):
    collection_name = "radius_users"

    @classmethod
    async def insert(cls, user: dict):
        return await cls.collection().insert_one(user)

    @classmethod
    async def find_one(cls, query: dict):
        return await cls.collection().find_one(query)

    @classmethod
    async def find_all(cls, limit: int = 100):
        return await cls.collection().find(
            {},
            {"_id": 0}
        ).to_list(limit)
