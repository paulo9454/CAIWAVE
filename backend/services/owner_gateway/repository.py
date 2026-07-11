"""
Persistence boundary for owner automated payment gateways.

One owner may have only one gateway profile.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class OwnerGatewayNotFound(Exception):
    """Raised when an owner gateway profile does not exist."""


class OwnerGatewayAlreadyExists(Exception):
    """Raised when an owner already has a gateway profile."""


class OwnerGatewayRepository:
    def __init__(self, collection: Any):
        self.collection = collection

    async def ensure_indexes(self) -> None:
        await self.collection.create_index(
            "owner_id",
            unique=True,
            name="uniq_owner_gateway_owner_id",
        )
        await self.collection.create_index(
            "id",
            unique=True,
            name="uniq_owner_gateway_id",
        )

    async def get_by_owner_id(
        self,
        owner_id: str,
    ) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one(
            {"owner_id": owner_id},
            {"_id": 0},
        )

    async def get_by_id(
        self,
        gateway_id: str,
    ) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one(
            {"id": gateway_id},
            {"_id": 0},
        )

    async def create(
        self,
        document: Dict[str, Any],
    ) -> Dict[str, Any]:
        existing = await self.get_by_owner_id(document["owner_id"])

        if existing:
            raise OwnerGatewayAlreadyExists(
                f"Owner {document['owner_id']} already has a gateway profile."
            )

        await self.collection.insert_one(dict(document))

        created = await self.get_by_owner_id(document["owner_id"])

        if not created:
            raise RuntimeError(
                "Owner gateway profile was inserted but could not be read back."
            )

        return created

    async def update_by_owner_id(
        self,
        owner_id: str,
        updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        existing = await self.get_by_owner_id(owner_id)

        if not existing:
            raise OwnerGatewayNotFound(
                f"Owner gateway profile not found for owner {owner_id}."
            )

        await self.collection.update_one(
            {"owner_id": owner_id},
            {"$set": dict(updates)},
        )

        updated = await self.get_by_owner_id(owner_id)

        if not updated:
            raise RuntimeError(
                "Owner gateway profile was updated but could not be read back."
            )

        return updated
