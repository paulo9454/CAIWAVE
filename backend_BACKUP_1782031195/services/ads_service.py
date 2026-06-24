from typing import List, Dict, Any
from backend.repositories.ads_repository import AdsRepository


class AdsService:
    @staticmethod
    async def get_active_ads(limit: int = 50) -> List[Dict[str, Any]]:
        return await AdsRepository.find_active(limit)

    @staticmethod
    async def get_ad(ad_id: str):
        return await AdsRepository.find_one({"id": ad_id, "is_active": True})
