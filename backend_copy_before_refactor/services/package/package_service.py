
class PackageService:

    @staticmethod
    async def list_active():
        return await PackagesRepository.collection().find(
            {"is_active": True},
            {"_id": 0}
        ).sort("price", 1).to_list(100)

    @staticmethod
    async def get_one(query):
        return await PackagesRepository.collection().find_one(query, {"_id": 0})
