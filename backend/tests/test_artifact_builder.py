import json
from copy import deepcopy

import pytest

from backend.schemas.provisioning_v2 import ArtifactStatus
from backend.services.provisioning_v2.artifact_builder import (
    ProvisioningArtifactBuildError,
    build_provisioning_artifact,
)
from backend.services.provisioning_v2.resource_registry import build_resource_registry
from backend.services.provisioning_v2.snapshot_builder import build_provisioning_snapshot


def snapshot():
    router = {
        "id": "router-1",
        "name": "GOODlife",
        "owner_id": "owner-1",
        "hotspot_id": "hotspot-1",
        "nas_identifier": "CAIWAVE-GOODLIFE",
        "wan_interface": "ether1",
        "lan_interfaces": ["ether2", "wlan1"],
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
        "module_versions": {
            "identity": "1.0.0",
            "bridge": "1.0.0",
            "dhcp": "1.0.0",
            "hotspot": "1.0.0",
            "radius": "1.0.0",
        },
    }
    return build_provisioning_snapshot(router, hotspot, config)


def resources_for_snapshot(snap):
    return build_resource_registry(snap)


def test_builds_metadata_only_artifact():
    snap = snapshot()
    resources = resources_for_snapshot(snap)

    artifact = build_provisioning_artifact(snap, resources, generated_by="test")

    assert artifact.artifact_id == f"artifact:{snap.snapshot_id}"
    assert artifact.snapshot_id == snap.snapshot_id
    assert artifact.status == ArtifactStatus.GENERATED
    assert artifact.content_type == "application/json"
    assert artifact.sha256
    assert artifact.validation_plan is not None


def test_artifact_content_is_metadata_not_routeros():
    snap = snapshot()
    artifact = build_provisioning_artifact(snap, resources_for_snapshot(snap))

    payload = json.loads(artifact.content)

    assert payload["routeros_rendered"] is False
    assert payload["content_type"] == "metadata-only"
    assert payload["resource_count"] == 19
    assert sorted(payload["resource_ids"]) == payload["resource_ids"]


def test_artifact_is_deterministic_except_generated_timestamp():
    snap = snapshot()
    resources = resources_for_snapshot(snap)

    first = build_provisioning_artifact(snap, resources)
    second = build_provisioning_artifact(snap, resources)

    assert first.content == second.content
    assert first.sha256 == second.sha256


def test_rejects_empty_resources():
    with pytest.raises(ProvisioningArtifactBuildError):
        build_provisioning_artifact(snapshot(), [])


def test_rejects_duplicate_resources():
    snap = snapshot()
    resources = resources_for_snapshot(snap)

    with pytest.raises(ProvisioningArtifactBuildError):
        build_provisioning_artifact(snap, resources + [resources[0]])


def test_rejects_resource_router_mismatch():
    snap = snapshot()
    resources = resources_for_snapshot(snap)
    bad = resources[0].model_copy(update={"router_id": "other-router"})

    with pytest.raises(ProvisioningArtifactBuildError):
        build_provisioning_artifact(snap, [bad] + resources[1:])


def test_does_not_mutate_inputs():
    snap = snapshot()
    resources = resources_for_snapshot(snap)

    before_snapshot = deepcopy(snap.model_dump())
    before_resources = deepcopy([resource.model_dump() for resource in resources])

    build_provisioning_artifact(snap, resources)

    assert snap.model_dump() == before_snapshot
    assert [resource.model_dump() for resource in resources] == before_resources
