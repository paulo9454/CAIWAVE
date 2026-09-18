"""
CAIWAVE MikroTik control-plane provisioning orchestration.

This module coordinates:
- provisioning job creation
- active-job idempotency
- provisioning job persistence

It does not:
- generate RouterOS configuration
- execute RouterOS commands
- authenticate HTTP requests
"""

from __future__ import annotations

from typing import Any, Dict

from backend.services.provisioning.job_service import job_service
from backend.services.provisioning.repository import ProvisioningJobRepository


class MikroTikProvisioningOrchestrationError(ValueError):
    """Raised when a provisioning operation cannot be completed."""


class MikroTikProvisioningOrchestrator:
    """
    Coordinates creation of provisioning jobs for MikroTik routers.

    The orchestrator deliberately sits above the job service and repository:
    - job_service owns the job contract and state transitions
    - repository owns persistence
    - this class owns the control-plane workflow
    """

    def __init__(
        self,
        repository: ProvisioningJobRepository,
    ):
        self.repository = repository

    async def get_or_create_provisioning_job(
        self,
        *,
        router_id: str,
        artifact_id: str,
        bundle_id: str,
        snapshot_id: str,
        artifact_checksum: str,
        payload: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        Return the existing active job for a router or create a new queued job.

        Active jobs are:
        - queued
        - dispatched
        - running

        Terminal jobs do not prevent creation of a new provisioning job.
        """

        if not router_id:
            raise MikroTikProvisioningOrchestrationError(
                "router_id is required"
            )

        active_job = await self.repository.get_active_for_router(router_id)

        if active_job:
            return active_job

        job = job_service.create_job(
            router_id=router_id,
            artifact_id=artifact_id,
            bundle_id=bundle_id,
            snapshot_id=snapshot_id,
            artifact_checksum=artifact_checksum,
            payload=payload,
        )

        return await self.repository.create(job)
