"""
Provisioning Artifact Builder for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no route wiring
- no legacy provisioning changes

This builder packages a ProvisioningSnapshot and ResourceRegistryEntry list
into a structured ProvisioningArtifact. The artifact content is metadata-only
for now; RouterOS rendering will be handled by a future renderer module.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Iterable, List

from backend.schemas.provisioning_v2 import (
    ArtifactStatus,
    ModuleResult,
    ModuleStatus,
    ProvisioningArtifact,
    ProvisioningSnapshot,
    ResourceRegistryEntry,
    ValidationPlan,
)


class ProvisioningArtifactBuildError(ValueError):
    """Raised when a ProvisioningArtifact cannot be safely built."""


def _stable_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _resource_ids(resources: Iterable[ResourceRegistryEntry]) -> List[str]:
    return [resource.resource_id for resource in resources]


def build_provisioning_artifact(
    snapshot: ProvisioningSnapshot,
    resources: list[ResourceRegistryEntry],
    *,
    generated_by: str = "system",
    filename: str | None = None,
) -> ProvisioningArtifact:
    """
    Build a structured provisioning artifact from snapshot + resource registry.

    This intentionally does not render RouterOS commands.
    """

    if not resources:
        raise ProvisioningArtifactBuildError("At least one resource is required")

    resource_ids = _resource_ids(resources)
    if len(resource_ids) != len(set(resource_ids)):
        raise ProvisioningArtifactBuildError("Duplicate resource IDs are not allowed")

    for resource in resources:
        if resource.router_id != snapshot.router_id:
            raise ProvisioningArtifactBuildError(
                f"Resource {resource.resource_id} router_id does not match snapshot"
            )
        if resource.hotspot_id != snapshot.hotspot_id:
            raise ProvisioningArtifactBuildError(
                f"Resource {resource.resource_id} hotspot_id does not match snapshot"
            )
        if resource.snapshot_id != snapshot.snapshot_id:
            raise ProvisioningArtifactBuildError(
                f"Resource {resource.resource_id} snapshot_id does not match snapshot"
            )

    artifact_id = f"artifact:{snapshot.snapshot_id}"
    now = datetime.now(timezone.utc)

    module_versions = dict(snapshot.versioning.module_versions or {})
    if not module_versions:
        module_versions = {
            "version": "1.0.0",
            "identity": "1.0.0",
            "resource_registry": "1.0.0",
        }

    validation_plan = ValidationPlan(
        validation_plan_id=f"validation-plan:{artifact_id}",
        hooks=[],
        production_readiness_required=True,
    )

    content_payload = {
        "artifact_id": artifact_id,
        "snapshot_id": snapshot.snapshot_id,
        "router_id": snapshot.router_id,
        "hotspot_id": snapshot.hotspot_id,
        "artifact_version": "1.0.0",
        "engine_version": snapshot.versioning.engine_version,
        "module_versions": module_versions,
        "resource_ids": sorted(resource_ids),
        "resource_count": len(resources),
        "routeros_rendered": False,
        "content_type": "metadata-only",
    }

    content = _stable_json(content_payload)
    checksum = _sha256(content)

    module_result = ModuleResult(
        module_name="artifact_builder",
        module_version="1.0.0",
        status=ModuleStatus.SUCCESS,
        resources=deepcopy(resources),
        rendered_fragments=[],
        warnings=["metadata-only artifact; RouterOS rendering not implemented yet"],
        assumptions=["artifact is immutable after generation"],
        validation_hooks=[],
    )

    redacted_payload = deepcopy(content_payload)
    redacted_payload["resource_count"] = len(resources)
    redacted_content = _stable_json(redacted_payload)

    return ProvisioningArtifact(
        artifact_id=artifact_id,
        snapshot_id=snapshot.snapshot_id,
        router_id=snapshot.router_id,
        hotspot_id=snapshot.hotspot_id,
        generated_at=now,
        generated_by=generated_by,
        status=ArtifactStatus.GENERATED,
        artifact_version="1.0.0",
        engine_version=snapshot.versioning.engine_version,
        module_versions=module_versions,
        sha256=checksum,
        script_sha256=None,
        redacted_sha256=_sha256(redacted_content),
        filename=filename or f"{snapshot.router_id}-provisioning-v2.json",
        content_type="application/json",
        content=content,
        redacted_content=redacted_content,
        warnings=module_result.warnings,
        assumptions=module_result.assumptions,
        validation_plan=validation_plan,
    )
