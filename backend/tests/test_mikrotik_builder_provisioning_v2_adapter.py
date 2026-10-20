import os
import pytest
from backend.services.mikrotik_builder import build_mikrotik_script
from backend.services.provisioning_v2.routeros_script_linter import lint_routeros_script
from backend.services.provisioning_v2.mikrotik_builder_adapter import (
    build_provisioning_v2_artifact_from_router,
    build_provisioning_v2_rsc_from_router,
)
from backend.services.provisioning_v2.provisioning_intent import (
    ProvisioningIntent,
)
from backend.services.provisioning_v2.routeros_renderer_contracts import (
    RouterOSSectionName,
)

def sample_router():
    return {
        "id": "5531447b-7613-4452-92c5-1ca0c94f2dfb",
        "name": "GOODlife",
        "owner_id": "4369263d-3dd3-4f80-b151-e7a499eb2897",
        "hotspot_id": "373bdbc6-88e9-47a6-9d8e-5ef9d0e6aaaf",
        "nas_identifier": "CAIWAVE-GOODLIFE-TEST",
        "radius_secret": "test-router-specific-secret",
        "radius_host": "radius.caiwave.com",
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

def test_adapter_returns_persistable_rendered_artifact():
    artifact = build_provisioning_v2_artifact_from_router(
        sample_router(),
        control_secret="test-control-secret-123",
    )

    assert artifact.artifact_id
    assert artifact.bundle_id
    assert artifact.router_id == sample_router()["id"]
    assert artifact.manifest.snapshot_id
    assert artifact.content
    assert artifact.checksum
    assert artifact.filename
    assert artifact.content_type == "text/routeros-script"
    assert artifact.status.value == "rendered"
    assert artifact.manifest.model_dump()
    assert artifact.sections
    assert RouterOSSectionName.SCHEDULERS in artifact.manifest.sections
    assert "CAIWAVE Heartbeat and Confirmation" in artifact.content
    assert 'name="caiwave-heartbeat"' in artifact.content
    assert 'name="caiwave-confirm"' in artifact.content

    assert "Authorization: Bearer test-control-secret-123" not in artifact.content
    assert r"Authorization: Bearer \$caiwaveControlSecret" in artifact.content
    assert ":global caiwaveControlSecret" in artifact.content
    assert "CAIWAVE managed provisioning control agent" not in artifact.content
    assert 'name="caiwave-control"' not in artifact.content

def sample_router_with_wireless():
    router = sample_router()
    router.update(
        {
            "wifi_enabled": True,
            "wifi_ssid": "CAIWAVE",
            "discovery": {
                "capabilities": {
                    "router_id": router["id"],
                    "board_name": "RB951Ui-2HnD",
                    "routeros_version": "7.22",
                    "architecture": "mipsbe",
                    "interface_count": 8,
                    "ethernet_interfaces": [
                        "ether1",
                        "ether2",
                        "ether3",
                        "ether4",
                        "ether5",
                    ],
                    "wireless_interfaces": ["wlan1"],
                    "bridge_count": 1,
                    "vlan_count": 0,
                    "route_count": 3,
                    "dhcp_server_count": 1,
                    "hotspot_count": 1,
                    "supports_wireless": True,
                }
            },
        }
    )
    return router

def test_adapter_provisions_verified_wireless_interface():
    output = build_provisioning_v2_rsc_from_router(
        sample_router_with_wireless()
    )

    assert "/interface wireless" in output.content
    assert 'wlan1' in output.content
    assert "ap-bridge" in output.content
    assert "CAIWAVE" in output.content
    assert 'interface="wlan1"' in output.content
    assert lint_routeros_script(output.content).valid is True

def test_adapter_rejects_wifi_when_router_has_no_wireless_capability():
    router = sample_router()
    router.update(
        {
            "wifi_enabled": True,
            "wifi_ssid": "CAIWAVE",
            "discovery": {
                "capabilities": {
                    "router_id": router["id"],
                    "board_name": "RB750",
                    "routeros_version": "7.21.4",
                    "architecture": "mipsbe",
                    "interface_count": 7,
                    "ethernet_interfaces": [
                        "ether1",
                        "ether2",
                        "ether3",
                        "ether4",
                        "ether5",
                    ],
                    "wireless_interfaces": [],
                    "bridge_count": 1,
                    "vlan_count": 0,
                    "route_count": 3,
                    "dhcp_server_count": 1,
                    "hotspot_count": 1,
                    "supports_wireless": False,
                }
            },
        }
    )

    with pytest.raises(
        ValueError,
        match="does not support wireless",
    ):
        build_provisioning_v2_rsc_from_router(router)

def test_adapter_builds_linted_routeros_script():
    output = build_provisioning_v2_rsc_from_router(sample_router())

    assert output.filename == "goodlife-caiwave-goodlife-test.rsc"
    assert "/system identity set" in output.content
    assert "/ip hotspot add" in output.content
    assert "/radius add" in output.content
    assert 'name="hotspot/redirect.html"' in output.content
    assert (
        'contents="\\$(if http-status == 302)Hotspot login required\\$(endif)'
        '\\$(if http-header == \\"Location\\")\\$(link-redirect)\\$(endif)"'
    ) in output.content
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

def test_adapter_includes_control_authorization_header():
    output = build_provisioning_v2_rsc_from_router(
        sample_router(),
        control_secret="test-control-secret-123",
    )

    assert "Authorization: Bearer test-control-secret-123" not in output.content
    assert "CAIWAVE managed provisioning control agent" not in output.content
    assert 'name="caiwave-control"' not in output.content
    assert lint_routeros_script(output.content).valid is True

def test_existing_builder_always_uses_engine_v2(monkeypatch):
    monkeypatch.delenv("CAIWAVE_PROVISIONING_ENGINE_V2", raising=False)
    monkeypatch.delenv("CAIWAVE_MIKROTIK_V2", raising=False)

    content = build_mikrotik_script(sample_router())

    assert "# CAIWAVE Identity" in content
    assert "/ip hotspot add" in content
    assert "/radius add" in content
    assert 'name="hotspot/redirect.html"' in content
    assert (
        'contents="\\$(if http-status == 302)Hotspot login required\\$(endif)'
        '\\$(if http-header == \\"Location\\")\\$(link-redirect)\\$(endif)"'
    ) in content
    assert lint_routeros_script(content).valid is True

def test_discovery_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("CAIWAVE_DISCOVERY_ENABLED", raising=False)

    output = build_provisioning_v2_rsc_from_router(sample_router())

    assert "CAIWAVE observational router discovery" not in output.content
    assert 'name="caiwave-control"' not in output.content
    assert "CAIWAVE managed provisioning control agent" not in output.content


def test_discovery_is_not_embedded_in_production_artifact(monkeypatch):
    monkeypatch.setenv("CAIWAVE_DISCOVERY_ENABLED", "true")

    output = build_provisioning_v2_rsc_from_router(sample_router())

    assert "CAIWAVE observational router discovery" not in output.content
    assert "/api/mikrotik-onboard/discovery" not in output.content

def test_adapter_returns_complete_rendered_artifact():
    from backend.services.provisioning_v2.mikrotik_builder_adapter import (
        build_provisioning_v2_artifact_from_router,
    )

    artifact = build_provisioning_v2_artifact_from_router(
        sample_router(),
        control_secret="test-control-secret-123",
    )

    assert artifact.artifact_id
    assert artifact.bundle_id
    assert artifact.manifest.snapshot_id
    assert artifact.checksum
    assert artifact.content
    assert artifact.content_type == "text/routeros-script"
    assert "Authorization: Bearer test-control-secret-123" not in artifact.content
    assert "CAIWAVE managed provisioning control agent" not in artifact.content
    assert 'name="caiwave-control"' not in artifact.content


def test_intent_aware_router_uses_discovered_topology_over_persisted_interfaces():
    from backend.services.provisioning_v2.mikrotik_builder_adapter import (
        _prepare_intent_aware_router,
    )
    from backend.services.provisioning_v2.provisioning_intent import (
        ProvisioningIntent,
    )

    router = sample_router()

    # Deliberately stale persisted topology.
    router["wan_interface"] = "ether1"
    router["lan_interfaces"] = [
        "ether2",
        "ether3",
        "ether4",
        "ether5",
    ]

    # Verified discovery describes a completely different physical topology.
    router["discovery"] = {
        "capabilities": {
            "router_id": router["id"],
            "board_name": "test-board",
            "routeros_version": "7.21.4",
            "architecture": "mipsbe",
            "interface_count": 4,
            "ethernet_interfaces": [
                "sfp-sfpplus1",
                "ether7",
                "ether8",
                "ether9",
            ],
            "wireless_interfaces": [],
            "bridge_count": 0,
            "vlan_count": 0,
            "route_count": 1,
            "dhcp_server_count": 0,
            "hotspot_count": 0,
            "supports_wireless": False,
        },
        "topology": {
            "status": "INFERRED",
            "wan_interface": "sfp-sfpplus1",
            "client_interfaces": [
                "ether7",
                "ether8",
            ],
            "client_bridge_interfaces": [],
            "confidence": "HIGH",
            "evidence": [],
            "warnings": [],
        },
    }

    intent = ProvisioningIntent(
        hotspot_enabled=True,
        wifi_enabled=False,
        wired_enabled=True,
    )

    prepared, plan = _prepare_intent_aware_router(
        router,
        intent,
    )

    assert plan.wan_interface == "sfp-sfpplus1"
    assert plan.client_interfaces == ["ether7", "ether8"]

    assert prepared["wan_interface"] == "sfp-sfpplus1"
    assert prepared["lan_interfaces"] == ["ether7", "ether8"]

    assert prepared["wan_interface"] != "ether1"
    assert prepared["lan_interfaces"] != [
        "ether2",
        "ether3",
        "ether4",
        "ether5",
    ]

def test_rendered_artifact_uses_discovered_topology_over_stale_persisted_interfaces():
    router = sample_router()

    # Deliberately stale persisted topology.
    router["wan_interface"] = "ether1"
    router["lan_interfaces"] = [
        "ether2",
        "ether3",
        "ether4",
        "ether5",
    ]

    # Verified discovery describes the actual physical topology.
    router["discovery"] = {
        "capabilities": {
            "router_id": router["id"],
            "board_name": "test-board",
            "routeros_version": "7.21.4",
            "architecture": "mipsbe",
            "interface_count": 4,
            "ethernet_interfaces": [
                "sfp-sfpplus1",
                "ether7",
                "ether8",
                "ether9",
            ],
            "wireless_interfaces": [],
            "bridge_count": 0,
            "vlan_count": 0,
            "route_count": 1,
            "dhcp_server_count": 0,
            "hotspot_count": 0,
            "supports_wireless": False,
        },
        "topology": {
            "status": "INFERRED",
            "wan_interface": "sfp-sfpplus1",
            "client_interfaces": [
                "ether7",
                "ether8",
            ],
            "client_bridge_interfaces": [],
            "confidence": "HIGH",
            "evidence": [],
            "warnings": [],
        },
    }

    artifact = build_provisioning_v2_rsc_from_router(
        router,
        provisioning_intent=ProvisioningIntent(
            hotspot_enabled=True,
            wifi_enabled=False,
            wired_enabled=True,
        ),
        control_secret="test-control-secret-123",
    )

    content = artifact.content

    # The actual rendered production artifact must use discovered topology.
    assert 'interface="sfp-sfpplus1"' in content
    assert 'interface="ether7"' in content
    assert 'interface="ether8"' in content

    # Verify WAN-specific renderer output follows discovered WAN.
    assert (
        '/ip dhcp-client add '
        'add-default-route=yes '
        'comment="CAIWAVE managed WAN DHCP client" '
        'default-route-distance="1" '
        'disabled=no '
        'interface="sfp-sfpplus1"'
    ) in content

    # Verify NAT follows discovered WAN.
    assert (
        'out-interface="sfp-sfpplus1"'
    ) in content

    # The stale persisted WAN must not become the rendered WAN.
    assert (
        'interface="ether1"'
        not in content
    )

    assert lint_routeros_script(content).valid is True


def test_adapter_reuses_existing_bridge_reported_by_discovery():
    router = sample_router()
    router["discovery"] = {
        "snapshot": {
            "bridges": [
                {"name": "bridge-hotspot", "running": True},
            ],
            "bridge_ports": [
                {"bridge": "bridge-hotspot", "interface": "ether2"},
            ],
        },
    }

    artifact = build_provisioning_v2_artifact_from_router(
        router,
        control_secret="test-control-secret-123",
    )

    assert artifact.content
    assert artifact.checksum
    assert "# Bridge action: reuse" in artifact.content
    assert "/interface bridge add" not in artifact.content
    assert lint_routeros_script(
        artifact.content, require_bridge_add=False
    ).valid is True

def test_adapter_rejects_existing_client_services_until_reconciled():
    router = sample_router()
    router["discovery"] = {
        "snapshot": {
            "bridges": [{"name": "bridge-hotspot", "running": True}],
            "bridge_ports": [
                {"bridge": "bridge-hotspot", "interface": "ether2"},
            ],
            "addresses": [
                {"interface": "bridge-hotspot", "address": "10.10.0.1/24"},
            ],
            "dhcp_servers": [
                {"name": "existing-dhcp", "interface": "bridge-hotspot"},
            ],
            "hotspots": [
                {"name": "existing-hotspot", "interface": "bridge-hotspot"},
            ],
        },
    }

    with pytest.raises(
        ValueError,
        match="require reconciliation before provisioning",
    ):
        build_provisioning_v2_artifact_from_router(
            router,
            control_secret="test-control-secret-123",
        )
