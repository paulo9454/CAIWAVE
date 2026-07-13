import os

from backend.services.mikrotik_builder import build_mikrotik_script
from backend.services.provisioning_v2.mikrotik_builder_adapter import build_provisioning_v2_rsc_from_router
from backend.services.provisioning_v2.routeros_script_linter import lint_routeros_script


def sample_router():
    return {
        "id": "5531447b-7613-4452-92c5-1ca0c94f2dfb",
        "name": "GOODlife",
        "owner_id": "4369263d-3dd3-4f80-b151-e7a499eb2897",
        "hotspot_id": "373bdbc6-88e9-47a6-9d8e-5ef9d0e6aaaf",
        "nas_identifier": "CAIWAVE-GOODLIFE-TEST",
        "radius_secret": "test-router-specific-secret",
        "radius_host": "34.134.75.132",
        "wan_interface": "ether1",
        "lan_interfaces": ["ether2"],
        "create_bridge": True,
        "bridge_name": "bridge-hotspot",
        "effective_lan_interface": "bridge-hotspot",
        "mode": "fresh",
        "hotspot_cidr": "10.10.0.0/24",
        "hotspot_gateway": "10.10.0.1",
        "dhcp_pool": "10.10.0.10-10.10.0.254",
        "dns_name": "login.caiwave.local",
        "portal_public_url": "https://www.caiwave.com",
        "api_public_url": "https://www.caiwave.com/api",
        "heartbeat_url": (
            "https://www.caiwave.com/api/mikrotik-onboard/heartbeat"
        ),
    }


def test_adapter_builds_linted_routeros_script():
    output = build_provisioning_v2_rsc_from_router(sample_router())

    assert output.filename == "goodlife-caiwave-goodlife-test.rsc"
    assert "/system identity set" in output.content
    assert "/ip hotspot add" in output.content
    assert "/radius add" in output.content
    assert "login.caiwave.local" in output.content
    assert "wifi.caiwave.com" not in output.content
    assert (
        "https://www.caiwave.com/portal/"
        "373bdbc6-88e9-47a6-9d8e-5ef9d0e6aaaf"
    ) in output.content
    assert "/login?hotspot=" not in output.content
    assert "radius-accounting=yes" in output.content
    assert "radius-interim-update=5m" in output.content
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
