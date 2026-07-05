from copy import deepcopy

from backend.schemas.provisioning_v2 import (
    ResourceLifecycleState,
    ResourceOwner,
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


def test_deterministic_resource_ids():
    first = build_resource_registry(snapshot())
    second = build_resource_registry(snapshot())

    assert [item.resource_id for item in first] == [item.resource_id for item in second]


def test_expected_number_of_resources():
    resources = build_resource_registry(snapshot())

    # Base resources are 17 plus one bridge-port per LAN interface.
    assert len(resources) == 19


def test_no_duplicate_resource_ids():
    resources = build_resource_registry(snapshot())
    resource_ids = [item.resource_id for item in resources]

    assert len(resource_ids) == len(set(resource_ids))


def test_owner_always_caiwave():
    resources = build_resource_registry(snapshot())

    assert all(item.owner == ResourceOwner.CAIWAVE for item in resources)


def test_lifecycle_is_planned():
    resources = build_resource_registry(snapshot())

    assert all(item.lifecycle_state == ResourceLifecycleState.PLANNED for item in resources)


def test_dependency_correctness():
    resources = {item.resource_id: item for item in build_resource_registry(snapshot())}

    assert "bridge:router-1" in resources["dhcp-server:router-1"].dependencies
    assert "ip-address:router-1" in resources["dhcp-server:router-1"].dependencies
    assert "dhcp-pool:router-1" in resources["dhcp-server:router-1"].dependencies

    assert "dhcp-server:router-1" in resources["hotspot-server:router-1"].dependencies
    assert "radius:router-1" in resources["hotspot-server:router-1"].dependencies


def test_does_not_mutate_snapshot():
    snap = snapshot()
    before = deepcopy(snap.model_dump())

    build_resource_registry(snap)

    assert snap.model_dump() == before
