from typing import Dict, Any, List, Optional
from repositories.payments_repository import PaymentsRepository


class PaymentsService:
    @staticmethod
    async def create_payment(payment: Dict[str, Any]):
        return await PaymentsRepository.insert(payment)

    @staticmethod
    async def list_payments(limit: int = 100):
        return await PaymentsRepository.find_all(limit)

    @staticmethod
    async def get_by_phone(phone: str, limit: int = 100):
        return await PaymentsRepository.find_by_phone(phone, limit)
