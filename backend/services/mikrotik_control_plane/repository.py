"""
Persistence boundary for MikroTik router control-plane credentials.

The repository stores only credential metadata and the SHA-256 hash of
the router secret. The plaintext router secret is never persisted.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class RouterControlCredentialNotFound(Exception):
    """Raised when a router control credential does not exist."""


class RouterControlCredentialRepository:
    def __init__(self, collection: Any):
        self.collection = collection

    async def ensure_indexes(self) -> None:
        await self.collection.create_index(
            "credential_id",
            unique=True,
            name="uniq_router_control_credential_id",
        )

        await self.collection.create_index(
            "router_id",
            unique=True,
            partialFilterExpression={"status": "active"},
            name="uniq_active_router_control_router_id",
        )


        await self.collection.create_index(
            [
                ("status", 1),
                ("expires_at", 1),
            ],
            name="router_control_credential_expiry",
        )

    async def get_by_id(
        self,
        credential_id: str,
    ) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one(
            {"credential_id": credential_id},
            {"_id": 0},
        )
    async def get_active_credentials(self) -> list[Dict[str, Any]]:
        cursor = self.collection.find(
            {"status": "active"},
            {"_id": 0},
        )
        return await cursor.to_list(length=None)

    async def get_by_router_id(self, router_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one(
            {"router_id": router_id, "status": "active"},
            {"_id": 0},
        )

    async def create(
        self,
        document: Dict[str, Any],
    ) -> Dict[str, Any]:
        await self.collection.insert_one(dict(document))

        created = await self.get_by_id(document["credential_id"])

        if not created:
            raise RuntimeError(
                "Router control credential was inserted but "
                "could not be read back."
            )

        return created

    async def revoke(
        self,
        credential_id: str,
        revoked_at: str,
    ) -> bool:
        result = await self.collection.update_one(
            {"credential_id": credential_id},
            {
                "$set": {
                    "status": "revoked",
                    "revoked_at": revoked_at,
                }
            },
        )

        return result.matched_count > 0

    async def rotate(
        self,
        router_id: str,
        document: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Replace the active credential for a router.

        The caller is responsible for generating the new credential and
        deciding the appropriate lifecycle timestamps.
        """
        await self.collection.update_one(
            {"router_id": router_id, "status": "active"},
            {
                "$set": {
                    "status": "superseded",
                    "superseded_at": document["created_at"],
                    "superseded_by": document["credential_id"],
                }
            },
        )

        return await self.create(document)
