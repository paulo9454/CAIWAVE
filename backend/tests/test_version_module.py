from copy import deepcopy

import pytest

from backend.schemas.provisioning_v2 import VersionManifest
from backend.services.provisioning_v2.snapshot_builder import build_provisioning_snapshot
from backend.services.provisioning_v2.versioning import (
    ARTIFACT_SCHEMA_VERSION,
    ENGINE_VERSION,
    SNAPSHOT_SCHEMA_VERSION,
    VersionModuleError,
    current_version_manifest,
    merge_snapshot_with_current_versions,
    validate_snapshot_versions,
    validate_version_manifest,
)


def snapshot(module_versions=None, routeros_compatibility=None):
    router = {
        "id": "router-1",
        "name": "GOODlife",
        "owner_id": "owner-1",
        "hotspot_id": "hotspot-1",
        "nas_identifier": "CAIWAVE-GOODLIFE",
        "wan_interface": "ether1",
        "lan_interfaces": ["ether2"],
        "create_bridge": True,
        "bridge_name": "bridge-hotspot",
        "effective_lan_interface": "bridge-hotspot",
        "mode": "fresh",
        "hotspot_cidr": "10.10.0.0/24",
        "hotspot_gateway": "10.10.0.1",
        "dhcp_pool": "10.10.0.10-10.10.0.254",
        "dns_name": "wifi.caiwave.com",
    }
    hotspot = {"id": "hotspot-1", "owner_id": "owner-1"}
    config = {
        "radius_host": "radius.caiwave.com",
        "portal_public_url": "https://caiwave.com/portal",
        "api_public_url": "https://caiwave.com/api",
        "heartbeat_url": "https://caiwave.com/api/mikrotik-onboard/heartbeat",
        "module_versions": module_versions or {},
        "routeros_compatibility": routeros_compatibility or ["routeros-7"],
    }
    return build_provisioning_snapshot(router, hotspot, config)


def test_current_version_manifest():
    manifest = current_version_manifest()

    assert manifest.engine_version == ENGINE_VERSION
    assert manifest.snapshot_schema_version == SNAPSHOT_SCHEMA_VERSION
    assert manifest.artifact_schema_version == ARTIFACT_SCHEMA_VERSION
    assert manifest.module_versions["identity"] == "1.0.0"


def test_current_version_manifest_allows_module_override():
    manifest = current_version_manifest({"identity": "1.0.1"})

    assert manifest.module_versions["identity"] == "1.0.1"


def test_rejects_bad_module_semver():
    with pytest.raises(VersionModuleError):
        current_version_manifest({"identity": "1.0"})


def test_validate_version_manifest_accepts_current():
    manifest = current_version_manifest()

    assert validate_version_manifest(manifest) == manifest


def test_validate_version_manifest_rejects_bad_schema():
    manifest = VersionManifest(
        snapshot_schema_version="9.0",
        artifact_schema_version="1.0",
        engine_version="2.0.0",
        module_versions={"identity": "1.0.0"},
        routeros_compatibility=["routeros-7"],
    )

    with pytest.raises(VersionModuleError):
        validate_version_manifest(manifest)


def test_validate_version_manifest_rejects_unsupported_routeros():
    manifest = current_version_manifest(routeros_compatibility=["routeros-6"])

    with pytest.raises(VersionModuleError):
        validate_version_manifest(manifest)


def test_validate_snapshot_versions():
    snap = snapshot()

    assert validate_snapshot_versions(snap).engine_version == "2.0.0"


def test_merge_snapshot_with_current_versions_does_not_mutate():
    snap = snapshot(module_versions={"identity": "1.0.1"})
    before = deepcopy(snap.model_dump())

    updated = merge_snapshot_with_current_versions(snap)

    assert snap.model_dump() == before
    assert updated.versioning.module_versions["identity"] == "1.0.1"
    assert updated.versioning.module_versions["version"] == "1.0.0"
