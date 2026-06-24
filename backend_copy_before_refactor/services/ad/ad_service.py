
class AdService:

    @staticmethod
    async def list_active():
        return await AdsRepository.collection().find(
            {"is_active": True},
            {"_id": 0}
        ).to_list(50)

    @staticmethod
    async def get_active_one(query):
        return await AdsRepository.collection().find_one(query)
