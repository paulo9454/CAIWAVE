"""
Persistence boundary for Owner Payment Engine v1.

The repository is deliberately small and depends only on a Mongo-style
collection interface. It does not import the running FastAPI application.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class OwnerPaymentProfileNotFound(Exception):
    """Raised when an owner payment profile does not exist."""


class OwnerPaymentProfileAlreadyExists(Exception):
    """Raised when an owner already has a payment profile."""


class OwnerPaymentProfileRepository:
    def __init__(self, collection: Any):
        self.collection = collection

    async def ensure_indexes(self) -> None:
        await self.collection.create_index(
            "owner_id",
            unique=True,
            name="uniq_owner_payment_profile_owner_id",
        )
        await self.collection.create_index(
            "id",
            unique=True,
            name="uniq_owner_payment_profile_id",
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
        profile_id: str,
    ) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one(
            {"id": profile_id},
            {"_id": 0},
        )

    async def create(
        self,
        document: Dict[str, Any],
    ) -> Dict[str, Any]:
        existing = await self.get_by_owner_id(document["owner_id"])
        if existing:
            raise OwnerPaymentProfileAlreadyExists(
                f"Owner {document['owner_id']} already has a payment profile."
            )

        await self.collection.insert_one(dict(document))

        created = await self.get_by_owner_id(document["owner_id"])
        if not created:
            raise RuntimeError(
                "Owner payment profile was inserted but could not be read back."
            )

        return created

    async def update_by_owner_id(
        self,
        owner_id: str,
        updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        existing = await self.get_by_owner_id(owner_id)
        if not existing:
            raise OwnerPaymentProfileNotFound(
                f"Owner payment profile not found for owner {owner_id}."
            )

        await self.collection.update_one(
            {"owner_id": owner_id},
            {"$set": dict(updates)},
        )

        updated = await self.get_by_owner_id(owner_id)
        if not updated:
            raise RuntimeError(
                "Owner payment profile was updated but could not be read back."
            )

        return updated

    async def delete_by_owner_id(self, owner_id: str) -> bool:
        result = await self.collection.delete_one({"owner_id": owner_id})
        return bool(result.deleted_count)
