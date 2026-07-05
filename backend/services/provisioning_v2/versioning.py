"""
Version Module for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no route wiring
- no legacy provisioning changes

This module is the compatibility authority for snapshots, artifacts,
engine versions, module versions, and RouterOS compatibility metadata.
"""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Dict, List

from backend.schemas.provisioning_v2 import ProvisioningSnapshot, VersionManifest


class VersionModuleError(ValueError):
    """Raised when version metadata is invalid or incompatible."""


ENGINE_VERSION = "2.0.0"
SNAPSHOT_SCHEMA_VERSION = "1.0"
ARTIFACT_SCHEMA_VERSION = "1.0"

DEFAULT_MODULE_VERSIONS: Dict[str, str] = {
    "version": "1.0.0",
    "identity": "1.0.0",
    "snapshot_builder": "1.0.0",
    "resource_registry": "1.0.0",
    "artifact_builder": "1.0.0",
}

SUPPORTED_ROUTEROS_COMPATIBILITY: List[str] = [
    "routeros-7",
]

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
_SCHEMA_RE = re.compile(r"^\d+\.\d+$")


def _validate_semver(value: str, field: str) -> str:
    if not isinstance(value, str) or not _SEMVER_RE.match(value):
        raise VersionModuleError(f"{field} must be semantic version MAJOR.MINOR.PATCH")
    return value


def _validate_schema_version(value: str, field: str) -> str:
    if not isinstance(value, str) or not _SCHEMA_RE.match(value):
        raise VersionModuleError(f"{field} must be schema version MAJOR.MINOR")
    return value


def current_version_manifest(
    module_versions: Dict[str, str] | None = None,
    routeros_compatibility: List[str] | None = None,
) -> VersionManifest:
    """Return the current canonical Provisioning Engine v2 version manifest."""

    merged_modules = dict(DEFAULT_MODULE_VERSIONS)
    if module_versions:
        merged_modules.update(module_versions)

    for module, version in merged_modules.items():
        _validate_semver(version, f"module_versions.{module}")

    compatibility = list(routeros_compatibility or SUPPORTED_ROUTEROS_COMPATIBILITY)

    return VersionManifest(
        snapshot_schema_version=SNAPSHOT_SCHEMA_VERSION,
        artifact_schema_version=ARTIFACT_SCHEMA_VERSION,
        engine_version=ENGINE_VERSION,
        module_versions=merged_modules,
        routeros_compatibility=compatibility,
    )


def validate_version_manifest(manifest: VersionManifest) -> VersionManifest:
    """Validate version manifest shape and supported compatibility."""

    checked = deepcopy(manifest)

    _validate_schema_version(
        checked.snapshot_schema_version, "snapshot_schema_version"
    )
    _validate_schema_version(
        checked.artifact_schema_version, "artifact_schema_version"
    )
    _validate_semver(checked.engine_version, "engine_version")

    for module, version in checked.module_versions.items():
        if not module:
            raise VersionModuleError("module name must not be empty")
        _validate_semver(version, f"module_versions.{module}")

    if checked.snapshot_schema_version != SNAPSHOT_SCHEMA_VERSION:
        raise VersionModuleError(
            f"Unsupported snapshot schema version: {checked.snapshot_schema_version}"
        )

    if checked.artifact_schema_version != ARTIFACT_SCHEMA_VERSION:
        raise VersionModuleError(
            f"Unsupported artifact schema version: {checked.artifact_schema_version}"
        )

    unsupported = [
        item
        for item in checked.routeros_compatibility
        if item not in SUPPORTED_ROUTEROS_COMPATIBILITY
    ]
    if unsupported:
        raise VersionModuleError(
            f"Unsupported RouterOS compatibility target(s): {', '.join(unsupported)}"
        )

    return checked


def validate_snapshot_versions(snapshot: ProvisioningSnapshot) -> VersionManifest:
    """Validate the version manifest embedded in a ProvisioningSnapshot."""

    return validate_version_manifest(snapshot.versioning)


def merge_snapshot_with_current_versions(
    snapshot: ProvisioningSnapshot,
) -> ProvisioningSnapshot:
    """
    Return a copy of the snapshot with canonical current module versions filled in.

    Does not mutate the input snapshot.
    """

    updated = snapshot.model_copy(deep=True)
    manifest = current_version_manifest(
        module_versions=updated.versioning.module_versions,
        routeros_compatibility=updated.versioning.routeros_compatibility,
    )
    updated.versioning = manifest
    return updated
