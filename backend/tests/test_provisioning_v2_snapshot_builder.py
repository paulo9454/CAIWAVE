from copy import deepcopy

import pytest

from backend.schemas.provisioning_v2 import Environment
from backend.services.provisioning_v2.snapshot_builder import (
    ProvisioningSnapshotBuildError,
    build_provisioning_snapshot,
)


def router_dict():
    return {
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
        "radius_secret": "plaintext-should-not-appear",
    }


def hotspot_dict():
    return {
        "id": "hotspot-1",
        "owner_id": "owner-1",
        "name": "GOODlife Hotspot",
    }


def config_dict():
    return {
        "environment": "lab",
        "radius_host": "radius.caiwave.com",
        "portal_public_url": "https://caiwave.com/portal",
        "api_public_url": "https://caiwave.com/api",
        "heartbeat_url": "https://caiwave.com/api/mikrotik-onboard/heartbeat",
        "module_versions": {"identity": "1.0.0"},
    }


def test_builds_snapshot_from_realistic_dicts():
    snapshot = build_provisioning_snapshot(
        router_dict(), hotspot_dict(), config_dict(), created_by="test"
    )

    assert snapshot.router_id == "router-1"
    assert snapshot.identity.nas_identifier == "CAIWAVE-GOODLIFE"
    assert snapshot.topology.wan_interface == "ether1"
    assert snapshot.topology.client_interface == "bridge-hotspot"
    assert snapshot.networking.dhcp_pool_start == "10.10.0.10"
    assert snapshot.networking.dhcp_pool_end == "10.10.0.254"
    assert snapshot.radius.radius_host == "radius.caiwave.com"


def test_does_not_mutate_inputs():
    router = router_dict()
    hotspot = hotspot_dict()
    config = config_dict()

    original_router = deepcopy(router)
    original_hotspot = deepcopy(hotspot)
    original_config = deepcopy(config)

    build_provisioning_snapshot(router, hotspot, config)

    assert router == original_router
    assert hotspot == original_hotspot
    assert config == original_config


def test_rejects_missing_wan_interface():
    router = router_dict()
    router.pop("wan_interface")

    with pytest.raises(ProvisioningSnapshotBuildError):
        build_provisioning_snapshot(router, hotspot_dict(), config_dict())


def test_rejects_missing_lan_interfaces():
    router = router_dict()
    router["lan_interfaces"] = []

    with pytest.raises(ProvisioningSnapshotBuildError):
        build_provisioning_snapshot(router, hotspot_dict(), config_dict())


def test_rejects_wan_lan_overlap():
    router = router_dict()
    router["lan_interfaces"] = ["ether1", "ether2"]

    with pytest.raises(ProvisioningSnapshotBuildError):
        build_provisioning_snapshot(router, hotspot_dict(), config_dict())


def test_rejects_invalid_dhcp_pool():
    router = router_dict()
    router["dhcp_pool"] = "10.10.0.10"

    with pytest.raises(ProvisioningSnapshotBuildError):
        build_provisioning_snapshot(router, hotspot_dict(), config_dict())


def test_uses_secret_references_not_plaintext_secret():
    snapshot = build_provisioning_snapshot(
        router_dict(), hotspot_dict(), config_dict()
    )

    assert snapshot.radius.radius_secret_ref == "router-radius-secret:router-1"
    assert "plaintext" not in snapshot.model_dump_json()


def test_defaults_environment_to_lab():
    config = config_dict()
    config.pop("environment")

    snapshot = build_provisioning_snapshot(router_dict(), hotspot_dict(), config)

    assert snapshot.environment == Environment.LAB
