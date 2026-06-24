from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from repositories.base_repository import BaseRepository


class HotspotRepository(BaseRepository):
    collection_name = "hotspots"

    @classmethod
    async def create(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        hotspot = {
            "id": str(uuid.uuid4()),
            "name": data.get("name"),
            "owner_id": data.get("owner_id"),
            "location": data.get("location"),
            "status": "pending_setup",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "hotspot_cidr": data.get("hotspot_cidr"),
            "hotspot_gateway": data.get("hotspot_gateway"),
            "hotspot_network": data.get("hotspot_network"),
        }

        await cls.collection().insert_one(hotspot)
        return hotspot

    @classmethod
    async def find_by_id(cls, hotspot_id: str) -> Optional[Dict[str, Any]]:
        return await cls.collection().find_one(
            {"id": hotspot_id},
            {"_id": 0}
        )

    @classmethod
    async def list(cls, owner_id: Optional[str] = None):
        query = {}
        if owner_id:
            query["owner_id"] = owner_id

        return await cls.collection().find(query, {"_id": 0}).to_list(100)

    @classmethod
    async def update(cls, hotspot_id: str, updates: Dict[str, Any]):
        updates["updated_at"] = datetime.utcnow()

        await cls.collection().update_one(
            {"id": hotspot_id},
            {"$set": updates}
        )

        return await cls.find_by_id(hotspot_id)
