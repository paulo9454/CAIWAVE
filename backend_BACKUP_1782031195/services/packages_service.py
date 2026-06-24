from typing import List, Dict, Any, Optional
from backend.repositories.packages_repository import PackagesRepository


class PackagesService:
    @staticmethod
    async def list_packages(limit: int = 100) -> List[Dict[str, Any]]:
        return await PackagesRepository.find_active_sorted(limit)

    @staticmethod
    async def get_package(package_id: str) -> Optional[Dict[str, Any]]:
        return await PackagesRepository.find_one({"id": package_id, "is_active": True})
