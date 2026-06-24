from typing import Dict, Any, Optional
from repositories.radius_repository import RadiusRepository


class RadiusService:
    @staticmethod
    async def create_user(user: Dict[str, Any]):
        return await RadiusRepository.insert(user)

    @staticmethod
    async def get_user(query: Dict[str, Any]):
        return await RadiusRepository.find_one(query)

    @staticmethod
    async def list_users(limit: int = 100):
        return await RadiusRepository.find_all(limit)
