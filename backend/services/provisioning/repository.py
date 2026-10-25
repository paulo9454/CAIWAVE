"""
Persistence boundary for CAIWAVE provisioning jobs.

Provisioning jobs represent live control-plane work and are deliberately
stored separately from provisioning_logs, which remains an audit/history
collection.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pymongo import ReturnDocument


class ProvisioningJobNotFound(Exception):
    """Raised when a provisioning job does not exist."""


class ProvisioningJobRepository:
    def __init__(self, collection: Any):
        self.collection = collection

    async def ensure_indexes(self) -> None:
        await self.collection.create_index(
            "job_id",
            unique=True,
            name="uniq_provisioning_job_id",
        )
        await self.collection.create_index(
            [
                ("router_id", 1),
                ("status", 1),
                ("created_at", -1),
            ],
            name="provisioning_job_router_status_created",
        )
        await self.collection.create_index(
            [
                ("status", 1),
                ("created_at", 1),
            ],
            name="provisioning_job_status_created",
        )

    async def get_by_id(
        self,
        job_id: str,
    ) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one(
            {"job_id": job_id},
            {"_id": 0},
        )

    async def get_latest_for_router(
        self,
        router_id: str,
    ) -> Optional[Dict[str, Any]]:
        jobs = await self.collection.find(
            {"router_id": router_id},
            {"_id": 0},
        ).sort("created_at", -1).to_list(1)

        return jobs[0] if jobs else None

    async def get_active_for_router(
        self,
        router_id: str,
        job_type: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Find the newest active job, including legacy untyped jobs."""
        query = {
            "router_id": router_id,
            "status": {"$in": ["queued", "dispatched", "running"]},
        }

        jobs = await self.collection.find(
            query,
            {"_id": 0},
        ).sort("created_at", -1).to_list(1000)

        for job in jobs:
            if job_type is None or job.get("job_type") == job_type:
                return job
            if job_type == "provisioning" and "job_type" not in job:
                return job

        return None

    async def get_manual_verification_for_router(
        self,
        router_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Return the newest job that still blocks provisioning."""
        jobs = await self.collection.find(
            {
                "router_id": router_id,
                "requires_manual_verification": True,
            },
            {"_id": 0},
        ).sort("created_at", -1).to_list(1)

        return jobs[0] if jobs else None

    async def create(
        self,
        document: Dict[str, Any],
    ) -> Dict[str, Any]:
        await self.collection.insert_one(dict(document))

        created = await self.get_by_id(document["job_id"])

        if not created:
            raise RuntimeError(
                "Provisioning job was inserted but could not be read back."
            )

        return created
    async def claim_next_for_router(
        self,
        router_id: str,
        job_type: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Atomically claim the oldest queued job for a router.

        When claiming a provisioning job, legacy queued jobs without a
        job_type are treated as provisioning jobs for backward compatibility.
        Explicitly typed non-provisioning jobs are never claimed by this path.

        The MongoDB find_one_and_update operation ensures that two
        simultaneous router polls cannot claim the same queued job.
        """
        now = datetime.now(timezone.utc)

        query = {
            "router_id": router_id,
            "status": "queued",
        }

        if job_type is not None:
            query["job_type"] = job_type

        job = await self.collection.find_one_and_update(
            query,
            {
                "$set": {
                    "status": "dispatched",
                    "updated_at": now,
                    "dispatched_at": now,
                },
            },
            sort=[("created_at", 1)],
            projection={"_id": 0},
            return_document=ReturnDocument.AFTER,
        )

        if job is not None or job_type != "provisioning":
            return job

        # Backward compatibility for the existing pre-job-type provisioning
        # job format. Keep this as a separate query so the repository remains
        # compatible with the lightweight fake collections used by tests.
        legacy_query = {
            "router_id": router_id,
            "status": "queued",
            "job_type": {"$exists": False},
        }

        return await self.collection.find_one_and_update(
            legacy_query,
            {
                "$set": {
                    "status": "dispatched",
                    "updated_at": now,
                    "dispatched_at": now,
                    "job_type": "provisioning",
                },
            },
            sort=[("created_at", 1)],
            projection={"_id": 0},
            return_document=ReturnDocument.AFTER,
        )
    async def claim_queued_job_for_router(
        self,
        router_id: str,
        job_id: str,
        job_type: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Atomically claim one specific queued job, preserving legacy support."""
        now = datetime.now(timezone.utc)
        base_query = {
            "router_id": router_id,
            "job_id": job_id,
            "status": "queued",
        }

        async def claim(query, *, mark_provisioning: bool = False):
            updates = {
                "status": "dispatched",
                "updated_at": now,
                "dispatched_at": now,
            }
            if mark_provisioning:
                updates["job_type"] = "provisioning"

            return await self.collection.find_one_and_update(
                query,
                {"$set": updates},
                projection={"_id": 0},
                return_document=ReturnDocument.AFTER,
            )

        if job_type is None:
            return await claim(base_query)

        typed_query = {**base_query, "job_type": job_type}
        claimed = await claim(typed_query)
        if claimed is not None or job_type != "provisioning":
            return claimed

        # A legacy fallback is limited to the same router, job and queued state.
        legacy_query = {
            **base_query,
            "job_type": {"$exists": False},
        }
        return await claim(legacy_query, mark_provisioning=True)

    async def update(
        self,
        job_id: str,
        updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        existing = await self.get_by_id(job_id)

        if not existing:
            raise ProvisioningJobNotFound(
                f"Provisioning job {job_id} not found."
            )

        await self.collection.update_one(
            {"job_id": job_id},
            {"$set": dict(updates)},
        )

        updated = await self.get_by_id(job_id)

        if not updated:
            raise RuntimeError(
                "Provisioning job was updated but could not be read back."
            )

        return updated

    async def update_if_status(
        self,
        job_id: str,
        expected_status: str,
        updates: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Update a job only if its status still matches the caller's snapshot.

        The status predicate and write are one MongoDB operation, preventing
        a stale callback from overwriting a newer job state.
        Returns None if the status no longer matches or the job is missing.
        """
        result = await self.collection.update_one(
            {
                "job_id": job_id,
                "status": expected_status,
            },
            {"$set": dict(updates)},
        )

        if result.matched_count == 0:
            return None

        updated = await self.get_by_id(job_id)
        if updated is None:
            raise RuntimeError(
                "Provisioning job matched conditional update but could not "
                "be read back."
            )

        return updated

    async def list_by_status(
        self,
        status: str,
        limit: int = 100,
    ) -> list[Dict[str, Any]]:
        return await self.collection.find(
            {"status": status},
            {"_id": 0},
        ).sort("created_at", 1).to_list(limit)
