import os

from backend.services.mikrotik_builder import build_mikrotik_script
from backend.services.provisioning_v2.mikrotik_builder_adapter import build_provisioning_v2_rsc_from_router
from backend.services.provisioning_v2.routeros_script_linter import lint_routeros_script


def sample_router():
    return {
        "id": "router-1",
        "name": "GOODlife",
        "owner_id": "owner-1",
        "hotspot_id": "hotspot-1",
        "nas_identifier": "CAIWAVE-GOODLIFE",
        "radius_secret": "test-secret",
        "radius_host": "radius.caiwave.com",
        "wan_interface": "ether1",
        "lan_interfaces": ["ether2"],
        "bridge_name": "bridge-hotspot",
        "hotspot_cidr": "10.10.0.0/24",
        "hotspot_gateway": "10.10.0.1",
        "dhcp_pool": "10.10.0.10-10.10.0.254",
        "dns_name": "wifi.caiwave.com",
    }


def test_adapter_builds_linted_routeros_script():
    output = build_provisioning_v2_rsc_from_router(sample_router())

    assert output.filename == "goodlife-caiwave-goodlife.rsc"
    assert "/system identity set" in output.content
    assert "/ip hotspot add" in output.content
    assert "/radius add" in output.content
    assert lint_routeros_script(output.content).valid is True


def test_existing_builder_uses_engine_v2_when_flag_enabled(monkeypatch):
    monkeypatch.setenv("CAIWAVE_PROVISIONING_ENGINE_V2", "true")

    content = build_mikrotik_script(sample_router())

    assert "# CAIWAVE Identity" in content
    assert "/ip hotspot add" in content
    assert "/radius add" in content


def test_existing_builder_keeps_legacy_path_when_engine_v2_disabled(monkeypatch):
    monkeypatch.delenv("CAIWAVE_PROVISIONING_ENGINE_V2", raising=False)
    monkeypatch.delenv("CAIWAVE_MIKROTIK_V2", raising=False)

    content = build_mikrotik_script(sample_router())

    assert "# CAIWAVE Identity" not in content
    assert "CAIWAVE" in content
