"""
Persistence boundary for executable CAIWAVE RouterOS provisioning artifacts.

A provisioning artifact is the executable RouterOS script produced by the
V2 rendering pipeline. It is stored separately from provisioning jobs so
multiple control-plane operations can reference the same immutable artifact.

The repository does not generate RouterOS configuration and does not execute
commands on MikroTik routers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


class ProvisioningArtifactNotFound(Exception):
    """Raised when a provisioning artifact does not exist."""


class ProvisioningArtifactRepository:
    def __init__(self, collection: Any):
        self.collection = collection

    async def ensure_indexes(self) -> None:
        await self.collection.create_index(
            "artifact_id",
            unique=True,
            name="uniq_provisioning_artifact_id",
        )
        await self.collection.create_index(
            [
                ("router_id", 1),
                ("created_at", -1),
            ],
            name="provisioning_artifact_router_created",
        )
        await self.collection.create_index(
            "checksum",
            name="provisioning_artifact_checksum",
        )

    async def get_by_id(
        self,
        artifact_id: str,
    ) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one(
            {"artifact_id": artifact_id},
            {"_id": 0},
        )

    async def get_by_checksum(
        self,
        checksum: str,
    ) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one(
            {"checksum": checksum},
            {"_id": 0},
        )

    async def create(
        self,
        document: Dict[str, Any],
    ) -> Dict[str, Any]:
        artifact = dict(document)

        if "created_at" not in artifact:
            artifact["created_at"] = datetime.now(timezone.utc)

        await self.collection.insert_one(artifact)

        created = await self.get_by_id(artifact["artifact_id"])

        if not created:
            raise RuntimeError(
                "Provisioning artifact was inserted but could not be read back."
            )

        return created

    async def list_by_router(
        self,
        router_id: str,
        limit: int = 100,
    ) -> list[Dict[str, Any]]:
        return await self.collection.find(
            {"router_id": router_id},
            {"_id": 0},
        ).sort("created_at", -1).to_list(limit)
