
class PaymentService:

    @staticmethod
    async def insert(data):
        return await PaymentsRepository.collection().insert_one(data)

    @staticmethod
    async def list_all():
        return await PaymentsRepository.collection().find({}, {"_id": 0}).to_list(100)

    @staticmethod
    async def find_by_phone(phone):
        return await PaymentsRepository.collection().find(
            {"phone": phone},
            {"_id": 0}
        ).to_list(100)
