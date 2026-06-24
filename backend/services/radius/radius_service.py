
class RadiusService:

    @staticmethod
    async def create(user):
        return await RadiusRepository.collection().insert_one(user)
