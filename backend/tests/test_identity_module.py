from copy import deepcopy

import pytest

from backend.services.provisioning_v2.identity import (
    IdentityModuleError,
    identity_fingerprint,
    normalize_identity,
)
from backend.services.provisioning_v2.snapshot_builder import build_provisioning_snapshot


def snapshot():
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
    }
    return build_provisioning_snapshot(router, hotspot, config)


def test_normalizes_identity():
    result = normalize_identity(snapshot())

    assert result["router_id"] == "router-1"
    assert result["router_name"] == "GOODlife"
    assert result["nas_identifier"] == "CAIWAVE-GOODLIFE"
    assert result["identity_fingerprint"]


def test_fingerprint_is_stable():
    result = normalize_identity(snapshot())

    identity_without_fingerprint = dict(result)
    identity_without_fingerprint.pop("identity_fingerprint")

    assert result["identity_fingerprint"] == identity_fingerprint(identity_without_fingerprint)


def test_does_not_mutate_snapshot():
    snap = snapshot()
    before = deepcopy(snap.model_dump())

    normalize_identity(snap)

    assert snap.model_dump() == before


def test_rejects_invalid_router_name():
    snap = snapshot()
    snap.identity.router_name = "../bad"

    with pytest.raises(IdentityModuleError):
        normalize_identity(snap)


def test_rejects_invalid_nas_identifier():
    snap = snapshot()
    snap.identity.nas_identifier = "bad nas with spaces"
    snap.radius.nas_identifier = "bad nas with spaces"

    with pytest.raises(IdentityModuleError):
        normalize_identity(snap)


def test_rejects_snapshot_identity_mismatch():
    snap = snapshot()
    snap.identity.router_id = "router-2"

    with pytest.raises(IdentityModuleError):
        normalize_identity(snap)


def test_rejects_radius_nas_mismatch():
    snap = snapshot()
    snap.radius.nas_identifier = "CAIWAVE-OTHER"

    with pytest.raises(IdentityModuleError):
        normalize_identity(snap)
