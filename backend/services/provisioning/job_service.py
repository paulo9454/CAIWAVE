"""
CAIWAVE provisioning job service.

This module defines the persistent job contract used by the MikroTik
control plane. It does not execute RouterOS commands and does not
communicate with routers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid


PROVISIONING_JOB_TYPES = {
    "provisioning",
    "control_credential_rotation",
}


PROVISIONING_JOB_STATUSES = {
    "queued",
    "dispatched",
    "running",
    "succeeded",
    "failed",
    "cancelled",
}


class ProvisioningJobError(ValueError):
    """Raised when a provisioning job cannot be created or updated."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProvisioningJobService:
    """
    Builds provisioning job records.

    Persistence will be connected separately through the provisioning
    repository/control-plane flow.
    """

    def create_job(
        self,
        *,
        router_id: str,
        artifact_id: str,
        bundle_id: str,
        snapshot_id: str,
        artifact_checksum: str,
        job_type: str = "provisioning",
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not router_id:
            raise ProvisioningJobError("router_id is required")

        if not artifact_id:
            raise ProvisioningJobError("artifact_id is required")

        if not bundle_id:
            raise ProvisioningJobError("bundle_id is required")

        if not snapshot_id:
            raise ProvisioningJobError("snapshot_id is required")

        if not artifact_checksum:
            raise ProvisioningJobError("artifact_checksum is required")

        if job_type not in PROVISIONING_JOB_TYPES:
            raise ProvisioningJobError(
                f"Invalid provisioning job type: {job_type}"
            )

        now = _utcnow()

        return {
            "job_id": str(uuid.uuid4()),
            "router_id": router_id,
            "artifact_id": artifact_id,
            "bundle_id": bundle_id,
            "snapshot_id": snapshot_id,
            "artifact_checksum": artifact_checksum,
            "job_type": job_type,
            "status": "queued",
            "attempts": 0,
            "payload": payload or {},
            "created_at": now,
            "updated_at": now,
            "started_at": None,
            "completed_at": None,
            "last_error": None,
            "result": None,
        }

    def transition(
        self,
        job: Dict[str, Any],
        *,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        if status not in PROVISIONING_JOB_STATUSES:
            raise ProvisioningJobError(
                f"Invalid provisioning job status: {status}"
            )

        current_status = job.get("status")
        allowed_transitions = {
            "queued": {"dispatched", "running", "failed", "cancelled"},
            "dispatched": {"running", "succeeded", "failed", "cancelled"},
            "running": {"succeeded", "failed", "cancelled"},
            "succeeded": set(),
            "failed": set(),
            "cancelled": set(),
        }

        # Duplicate callbacks must not reset timestamps, overwrite results,
        # or increment attempts again.
        if status == current_status:
            return dict(job)

        if status not in allowed_transitions.get(current_status, set()):
            raise ProvisioningJobError(
                f"Invalid provisioning job transition: "
                f"{current_status} -> {status}"
            )

        updated = dict(job)
        now = _utcnow()

        updated["status"] = status
        updated["updated_at"] = now

        if status == "running":
            updated["started_at"] = updated.get("started_at") or now
            updated["attempts"] = int(updated.get("attempts", 0)) + 1

        if status in {"succeeded", "failed", "cancelled"}:
            updated["completed_at"] = now

        if error is not None:
            updated["last_error"] = error

        if result is not None:
            updated["result"] = result

        return updated


job_service = ProvisioningJobService()
