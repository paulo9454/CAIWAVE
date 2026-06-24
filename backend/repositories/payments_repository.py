from repositories.base_repository import BaseRepository


class PaymentsRepository(BaseRepository):
    collection_name = "payments"

    @classmethod
    async def insert(cls, payment: dict):
        return await cls.collection().insert_one(payment)

    @classmethod
    async def find_all(cls, limit: int = 100):
        return await cls.collection().find(
            {},
            {"_id": 0}
        ).to_list(limit)

    @classmethod
    async def find_by_phone(cls, phone: str, limit: int = 100):
        return await cls.collection().find(
            {"phone": phone},
            {"_id": 0}
        ).to_list(limit)
