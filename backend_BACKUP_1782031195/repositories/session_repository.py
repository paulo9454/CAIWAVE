from backend.repositories.base_repository import BaseRepository


class SessionRepository(BaseRepository):
    collection_name = "sessions"

    @classmethod
    async def insert(cls, session: dict):
        return await cls.collection().insert_one(session)

    @classmethod
    async def count(cls, query: dict):
        return await cls.collection().count_documents(query)

    @classmethod
    async def find(cls, query: dict, limit: int = 100):
        return await cls.collection().find(query, {"_id": 0}).to_list(limit)
