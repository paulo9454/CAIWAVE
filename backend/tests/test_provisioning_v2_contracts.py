from datetime import datetime, timezone

import pytest

try:
    from pydantic import ValidationError
    from backend.schemas.provisioning_v2 import (
        ArtifactStatus,
        DriftStatus,
        Environment,
        ModuleResult,
        ModuleStatus,
        ProvisioningArtifact,
        ProvisioningSnapshot,
        ResourceLifecycleState,
        ResourceRegistryEntry,
        ValidationHook,
        ValidationLevel,
        VersionManifest,
    )
except Exception as exc:  # pragma: no cover
    pytest.skip(f"pydantic/provisioning_v2 contracts unavailable: {exc}", allow_module_level=True)


def sample_snapshot() -> ProvisioningSnapshot:
    return ProvisioningSnapshot(
        snapshot_id="snap-1",
        router_id="router-1",
        owner_id="owner-1",
        hotspot_id="hotspot-1",
        created_at=datetime.now(timezone.utc),
        created_by="test",
        environment=Environment.LAB,
        identity={
            "router_id": "router-1",
            "router_name": "Test Router",
            "owner_id": "owner-1",
            "hotspot_id": "hotspot-1",
            "nas_identifier": "CAIWAVE-TEST",
        },
        topology={
            "deployment_mode": "fresh",
            "wan_interface": "ether1",
            "lan_interfaces": ["ether2"],
            "client_interface": "bridge-hotspot",
            "create_bridge": True,
            "bridge_name": "bridge-hotspot",
        },
        networking={
            "hotspot_cidr": "10.10.0.0/24",
            "hotspot_gateway": "10.10.0.1",
            "dhcp_pool_start": "10.10.0.10",
            "dhcp_pool_end": "10.10.0.254",
            "client_dns_servers": ["10.10.0.1"],
            "router_dns_upstreams": ["1.1.1.1"],
        },
        hotspot={
            "server_name": "caiwave-hotspot",
            "profile_name": "caiwave-profile",
            "dns_name": "wifi.caiwave.com",
            "login_methods": ["http-pap"],
        },
        portal={
            "portal_public_url": "https://caiwave.com/portal",
            "api_public_url": "https://caiwave.com/api",
            "portal_strategy": "redirect",
        },
        radius={
            "radius_host": "radius.caiwave.com",
            "radius_secret_ref": "secret-radius-1",
            "nas_identifier": "CAIWAVE-TEST",
        },
        heartbeat={
            "heartbeat_url": "https://caiwave.com/api/mikrotik-onboard/heartbeat",
            "heartbeat_token_ref": "secret-heartbeat-1",
        },
        diagnostics={"required_checks": ["heartbeat", "radius", "portal"]},
        security={"secret_policy": "redact"},
        versioning=VersionManifest(module_versions={"identity": "1.0.0"}),
    )


def test_snapshot_requires_sections():
    snap = sample_snapshot()
    assert snap.router_id == "router-1"
    assert snap.identity.nas_identifier == "CAIWAVE-TEST"
    assert snap.versioning.module_versions["identity"] == "1.0.0"


def test_resource_registry_defaults():
    entry = ResourceRegistryEntry(
        resource_id="res-1",
        router_id="router-1",
        hotspot_id="hotspot-1",
        artifact_id="artifact-1",
        snapshot_id="snap-1",
        resource_type="bridge",
        logical_name="hotspot bridge",
        module="bridge",
        module_version="1.0.0",
    )
    assert entry.lifecycle_state == ResourceLifecycleState.PLANNED
    assert entry.drift_status == DriftStatus.UNKNOWN


def test_validation_hook_contract():
    hook = ValidationHook(
        validation_id="val-1",
        module="identity",
        level=ValidationLevel.EXPECTED,
        evidence_source="snapshot",
        failure_message="identity missing",
    )
    assert hook.blocking is True


def test_module_result_contract():
    result = ModuleResult(
        module_name="identity",
        module_version="1.0.0",
        status=ModuleStatus.SUCCESS,
    )
    assert result.resources == []


def test_artifact_contract():
    artifact = ProvisioningArtifact(
        artifact_id="artifact-1",
        snapshot_id="snap-1",
        router_id="router-1",
        hotspot_id="hotspot-1",
        generated_at=datetime.now(timezone.utc),
        generated_by="test",
        artifact_version="1.0.0",
        engine_version="2.0.0",
        filename="router.rsc",
        content="/system identity print",
    )
    assert artifact.status == ArtifactStatus.GENERATED


def test_unknown_fields_rejected():
    with pytest.raises(ValidationError):
        VersionManifest(unknown_field=True)
