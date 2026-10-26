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
from backend.services.provisioning.repository import (
    ActiveProvisioningJobConflict,
    ProvisioningJobRepository,
)


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

        manual_lookup = getattr(
            self.repository,
            "get_manual_verification_for_router",
            None,
        )
        if not callable(manual_lookup):
            raise MikroTikProvisioningOrchestrationError(
                "Manual-verification safety check is unavailable; "
                "provisioning is blocked."
            )

        manual_verification_job = await manual_lookup(router_id)
        if manual_verification_job:
            raise MikroTikProvisioningOrchestrationError(
                "Provisioning is blocked because job "
                f"{manual_verification_job.get('job_id', 'unknown')} requires "
                "manual router verification. A Super Admin must record a "
                "verification note before provisioning can resume."
            )

        active_job = await self.repository.get_active_for_router(
            router_id,
            job_type="provisioning",
        )

        if active_job:
            if active_job.get("artifact_checksum") == artifact_checksum:
                return active_job

            active_status = active_job.get("status")
            if active_status not in {"queued", "dispatched", "running"}:
                raise MikroTikProvisioningOrchestrationError(
                    "The active provisioning job has an unexpected status; "
                    "no replacement job was created."
                )

            superseded_job = job_service.transition(
                active_job,
                status="failed",
                error="Superseded by newer provisioning artifact",
            )
            updates = {
                "status": superseded_job["status"],
                "updated_at": superseded_job["updated_at"],
                "completed_at": superseded_job["completed_at"],
                "last_error": superseded_job["last_error"],
            }

            # A dispatched/running job may already have changed the router.
            # Fail it conditionally and require an explicit manual review.
            needs_manual_verification = active_status in {
                "dispatched",
                "running",
            }
            if needs_manual_verification:
                updates["requires_manual_verification"] = True
                updates["last_error"] = (
                    "A newer artifact arrived while this job was already "
                    "dispatched or running. Verify the router before retrying."
                )

            updated_job = await self.repository.update_if_status(
                active_job["job_id"],
                active_status,
                updates,
            )
            if updated_job is None:
                raise MikroTikProvisioningOrchestrationError(
                    "Active provisioning job changed concurrently; "
                    "no replacement job was created."
                )

            if needs_manual_verification:
                raise MikroTikProvisioningOrchestrationError(
                    "The previous provisioning job may already have changed "
                    "the router. Manual verification is required before "
                    "a replacement job can be created."
                )

        job = job_service.create_job(
            router_id=router_id,
            artifact_id=artifact_id,
            bundle_id=bundle_id,
            snapshot_id=snapshot_id,
            artifact_checksum=artifact_checksum,
            job_type="provisioning",
            payload=payload,
        )

        try:
            return await self.repository.create(job)
        except ActiveProvisioningJobConflict as exc:
            existing = exc.active_job
            if (
                existing
                and existing.get("status") in {"queued", "dispatched", "running"}
                and existing.get("artifact_checksum") == artifact_checksum
                and existing.get("job_type") in {None, "provisioning"}
            ):
                return existing
            raise MikroTikProvisioningOrchestrationError(
                "Another active control-plane job was created concurrently. "
                "No duplicate job was created; review the active job before retrying."
            ) from exc
