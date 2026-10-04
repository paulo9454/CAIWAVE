from backend.services.provisioning_v2.routeros_discovery_renderer import (
    RouterOSDiscoveryRendererError,
    render_discovery_script,
)


def test_discovery_renderer_generates_read_only_collection_script():
    section = render_discovery_script(
        discovery_url="https://caiwave.com/api/mikrotik-onboard/discovery",
        nas_identifier="CAIWAVE-TEST",
        control_secret="TEST-CONTROL-SECRET",
    )

    assert section.status.value == "rendered"
    assert "/interface print as-value" in section.content
    assert "/system resource get board-name" in section.content
    assert "/system resource get version" in section.content
    assert "/system package print as-value" in section.content
    assert "/interface print as-value" in section.content
    assert "/interface wireless print as-value" not in section.content
    assert ":local nasid" in section.content
    assert ":local nas_identifier" not in section.content
    assert '"nas_identifier"=$nasid' in section.content
    assert ":serialize to=json" in section.content
    assert "/tool fetch url=" in section.content
    assert "/system script add" not in section.content
    assert "/system script run" not in section.content
    assert "CAIWAVE observational router discovery" in section.content
    assert '[:len $json] <= 60000' in section.content
    assert ':if ([:len $json] <= 60000) do={' in section.content
    assert "/interface bridge port print as-value" in section.content
    assert "/ip dhcp-server print as-value" in section.content
    assert "/ip hotspot print as-value" in section.content
    assert '"bridge_ports"=$bridgeports' in section.content
    assert '"dhcp_servers"=$dhcpservers' in section.content
    assert '"hotspots"=$hotspots' in section.content
    assert ":local bridgeports" in section.content
    assert ":local dhcpservers" in section.content
    assert ":local bridge_ports" not in section.content
    assert ":local dhcp_servers" not in section.content
    assert ":local boardname" in section.content
    assert ":local rosver" in section.content
    assert ":local arch" in section.content

    assert ":local board " not in section.content
    assert ":local version " not in section.content
    assert ":local architecture " not in section.content

    assert '"board_name"=$boardname;' in section.content
    assert '"routeros_version"=$rosver;' in section.content
    assert '"architecture"=$arch };' in section.content
    assert section.content.count("/tool fetch url=") == 1
    assert ":onerror discoveryError in={" in section.content
    assert "} do={" in section.content
    assert 'CAIWAVE discovery execution failed: " . [:tostr $discoveryError]' in section.content
    assert section.content.endswith(
        '} do={ :log warning ("CAIWAVE discovery execution failed: " . [:tostr $discoveryError]); };'
    )


def test_discovery_renderer_rejects_non_https_url():
    try:
        render_discovery_script(
            discovery_url="http://caiwave.com/api/mikrotik-onboard/discovery",
            nas_identifier="CAIWAVE-TEST",
            control_secret="TEST-CONTROL-SECRET",
)
    except RouterOSDiscoveryRendererError:
        return

    raise AssertionError("Expected non-HTTPS URL to be rejected")


def test_discovery_renderer_rejects_blank_nas_identifier():
    try:
        render_discovery_script(
            discovery_url="https://caiwave.com/api/mikrotik-onboard/discovery",
            nas_identifier="   ",
            control_secret="TEST-CONTROL-SECRET",
    )
    except RouterOSDiscoveryRendererError:
        return

    raise AssertionError("Expected blank NAS identifier to be rejected")


def test_discovery_script_posts_observed_router_state():
    section = render_discovery_script(
        discovery_url="https://caiwave.com/api/mikrotik-onboard/discovery",
        nas_identifier="CAIWAVE-TEST",
        control_secret="TEST-CONTROL-SECRET",
    )

    assert section.status.value == "rendered"
    assert "https://caiwave.com/api/mikrotik-onboard/discovery" in section.content
    assert "nas_identifier" in section.content
    assert "interfaces" in section.content
    assert "bridges" in section.content
    assert "vlans" in section.content
    assert "addresses" in section.content
    assert "routes" in section.content
    assert "packages" in section.content
    assert "dhcp_clients" in section.content
    assert ":local dhcpclients" in section.content
    assert "/ip dhcp-client print as-value" in section.content
    assert ":serialize to=json" in section.content
    assert '/tool fetch url="' in section.content
    assert ':local nasid "CAIWAVE-TEST";' in section.content
    assert ':local nas_identifier "CAIWAVE-TEST";' not in section.content
    assert '"nas_identifier"=$nasid' in section.content
    assert '"architecture"=$arch };' in section.content
    assert '"packages"=$packages };' in section.content
    assert '"architecture"=$architecture; };' not in section.content
    assert '"packages"=$packages; };' not in section.content
