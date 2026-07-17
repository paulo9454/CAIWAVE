from backend.services.provisioning_v2.mikrotik_builder_adapter import (
    build_provisioning_v2_rsc_from_router,
)
from backend.services.provisioning_v2.routeros_script_linter import (
    ProductionRouterOSLintContext,
    lint_production_routeros_script,
)
from backend.tests.test_mikrotik_builder_provisioning_v2_adapter import (
    sample_router,
)


def context():
    router = sample_router()

    return ProductionRouterOSLintContext(
        router_id=router["id"],
        hotspot_id=router["hotspot_id"],
        nas_identifier=router["nas_identifier"],
        captive_dns_name=router["dns_name"],
        portal_public_url=router["portal_public_url"],
        radius_host=router["radius_host"],
        heartbeat_url=router["heartbeat_url"],
    )


def production_script():
    return build_provisioning_v2_rsc_from_router(
        sample_router()
    ).content


def test_accepts_complete_production_script():
    result = lint_production_routeros_script(
        production_script(),
        context=context(),
    )

    assert result.valid is True
    assert result.errors == []


def test_rejects_stale_captive_dns():
    content = production_script().replace(
        "login.caiwave.local",
        "wifi.caiwave.com",
    )

    result = lint_production_routeros_script(
        content,
        context=context(),
    )

    assert result.valid is False
    assert any(
        "wifi.caiwave.com" in error
        for error in result.errors
    )


def test_rejects_wrong_portal_route():
    content = production_script().replace(
        (
            "https://www.caiwave.com/portal/"
            + sample_router()["hotspot_id"]
        ),
        (
            "https://www.caiwave.com/"
            "portal/login?hotspot="
            + sample_router()["hotspot_id"]
        ),
    )

    result = lint_production_routeros_script(
        content,
        context=context(),
    )

    assert result.valid is False
    assert any(
        "portal" in error.lower()
        for error in result.errors
    )


def test_rejects_missing_radius_accounting():
    content = production_script().replace(
        "radius-accounting=yes",
        "radius-accounting=no",
    )

    result = lint_production_routeros_script(
        content,
        context=context(),
    )

    assert result.valid is False
    assert any(
        "radius-accounting=yes" in error
        for error in result.errors
    )


def test_rejects_missing_heartbeat_scheduler():
    content = production_script().replace(
        'name="caiwave-heartbeat"',
        'name="removed-heartbeat"',
    )

    result = lint_production_routeros_script(
        content,
        context=context(),
    )

    assert result.valid is False
    assert any(
        "caiwave-heartbeat" in error
        for error in result.errors
    )


def test_rejects_wrong_router_identity_contract():
    content = production_script().replace(
        sample_router()["nas_identifier"],
        "WRONG-NAS",
    )

    result = lint_production_routeros_script(
        content,
        context=context(),
    )

    assert result.valid is False
    assert any(
        sample_router()["nas_identifier"] in error
        for error in result.errors
    )


def test_production_artifact_includes_wan_dhcp_client():
    content = production_script()

    assert "/ip dhcp-client add" in content
    assert 'interface="ether1"' in content
    assert "disabled=no" in content


def test_production_artifact_allows_established_forwarding_before_drop():
    content = production_script()

    established_position = content.find("established,related")
    final_drop_position = content.find(
        "CAIWAVE default drop unmatched forward"
    )

    assert established_position >= 0
    assert final_drop_position >= 0
    assert established_position < final_drop_position


def test_production_artifact_allows_authenticated_hotspot_before_drop():
    content = production_script()

    authenticated_position = content.find('hotspot="auth"')
    final_drop_position = content.find(
        "CAIWAVE default drop unmatched forward"
    )

    assert authenticated_position >= 0
    assert final_drop_position >= 0
    assert authenticated_position < final_drop_position


def test_production_artifact_uses_real_radius_secret():
    router = sample_router()
    content = production_script()

    assert router["radius_secret"] in content
    assert "router-radius-secret:" not in content


def test_interface_section_is_rendered_not_planned():
    content = production_script()

    assert "# CAIWAVE Interfaces" in content
    assert "# section planned: interfaces" not in content


def test_production_artifact_disables_radius_message_auth_requirement():
    content = production_script()

    assert 'require-message-auth=no' in content


def test_production_artifact_allows_preauth_portal_before_drop():
    content = production_script()

    allow_position = content.find(
        'dst-address-list="CAIWAVE-PREAUTH"'
    )
    drop_position = content.find(
        "CAIWAVE default drop unmatched forward"
    )

    assert 'list="CAIWAVE-PREAUTH"' in content
    assert 'address="www.caiwave.com"' in content
    assert 'address="checkout.paystack.com"' in content
    assert 'hotspot="from-client,!auth"' in content
    assert 'dst-port="80,443"' in content
    assert allow_position >= 0
    assert drop_position >= 0
    assert allow_position < drop_position


def test_linter_rejects_radius_message_auth_requirement():
    content = production_script().replace(
        "require-message-auth=no",
        "require-message-auth=yes-for-request-resp",
    )

    result = lint_production_routeros_script(
        content,
        context=context(),
    )

    assert result.valid is False
    assert any(
        "require-message-auth=no" in error
        for error in result.errors
    )


def test_linter_rejects_missing_preauth_forward_allowance():
    content = production_script().replace(
        'dst-address-list="CAIWAVE-PREAUTH"',
        'dst-address-list="BROKEN-PREAUTH"',
    )

    result = lint_production_routeros_script(
        content,
        context=context(),
    )

    assert result.valid is False
    assert any(
        "CAIWAVE-PREAUTH" in error
        for error in result.errors
    )


def test_linter_rejects_preauth_allowance_after_final_drop():
    content = production_script()

    lines = content.splitlines()

    allow_index = next(
        index
        for index, line in enumerate(lines)
        if 'dst-address-list="CAIWAVE-PREAUTH"' in line
        and line.startswith("/ip firewall filter add")
    )

    drop_index = next(
        index
        for index, line in enumerate(lines)
        if "CAIWAVE default drop unmatched forward" in line
    )

    allow_line = lines.pop(allow_index)

    if allow_index < drop_index:
        drop_index -= 1

    lines.insert(drop_index + 1, allow_line)

    broken_content = "\n".join(lines) + "\n"

    result = lint_production_routeros_script(
        broken_content,
        context=context(),
    )

    assert result.valid is False
    assert any(
        "before" in error.lower()
        and "drop" in error.lower()
        for error in result.errors
    )
