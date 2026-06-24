from typing import Dict, Any, Optional

from backend.repositories.hotspot_repository import HotspotRepository


class HotspotService:
    @staticmethod
    async def create_hotspot(data: Dict[str, Any]):
        return await HotspotRepository.create(data)

    @staticmethod
    async def get_hotspot(hotspot_id: str) -> Optional[Dict[str, Any]]:
        return await HotspotRepository.find_by_id(hotspot_id)

    @staticmethod
    async def list_hotspots(owner_id: Optional[str] = None):
        return await HotspotRepository.list(owner_id)

    @staticmethod
    async def update_hotspot(hotspot_id: str, updates: Dict[str, Any]):
        return await HotspotRepository.update(hotspot_id, updates)

    @staticmethod
    async def change_status(hotspot_id: str, status: str):
        return await HotspotRepository.update(hotspot_id, {"status": status})
