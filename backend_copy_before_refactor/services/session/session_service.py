
class SessionService:

    @staticmethod
    async def count_documents(query):
        return await SessionRepository.collection().count_documents(query)

    @staticmethod
    async def insert(session):
        return await SessionRepository.collection().insert_one(session)
