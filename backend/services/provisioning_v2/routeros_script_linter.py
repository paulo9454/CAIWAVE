"""
RouterOS Script Linter for CAIWAVE Provisioning Engine v2.

Safety:
- no RouterOS execution
- no database access
- no route wiring
- no legacy provisioning changes

This linter performs static checks on rendered RouterOS scripts before CHR
or physical-router validation.
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RouterOSLintResult(StrictModel):
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

def _find_unresolved_template_tokens(content: str) -> List[str]:
    """
    Find unresolved template markers outside quoted RouterOS strings.

    JSON payloads embedded inside RouterOS strings may legitimately contain
    adjacent braces such as `}}`, so template-token detection must not treat
    quoted JSON as an unresolved template.
    """
    tokens = ["{{", "}}", "${", "<TODO", "TODO:"]
    found: List[str] = []

    for token in tokens:
        in_string = False
        escaped = False
        index = 0

        while index < len(content):
            char = content[index]

            if escaped:
                escaped = False
                index += 1
                continue

            if char == "\\" and in_string:
                escaped = True
                index += 1
                continue

            if char == '"':
                in_string = not in_string
                index += 1
                continue

            if not in_string and content.startswith(token, index):
                found.append(token)
                break

            index += 1

    return found

def lint_routeros_script(content: str) -> RouterOSLintResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not content or not content.strip():
        errors.append("RouterOS script is empty")
        return RouterOSLintResult(valid=False, errors=errors, warnings=warnings)

    lines = [line.rstrip() for line in content.splitlines()]
    command_lines = [
        line.strip()
        for line in lines
        if line.strip() and not line.strip().startswith("#")
    ]

    required_prefixes = [
        "/system identity set",
        "/interface bridge add",
        "/ip address add",
        "/ip pool add",
        "/ip dhcp-server add",
        "/ip dhcp-server network add",
        "/ip dns set",
        "/ip firewall nat add",
        "/ip hotspot profile add",
        "/ip hotspot add",
        "/ip hotspot walled-garden add",
        "/radius add",
        "/ip firewall filter add",
    ]

    for prefix in required_prefixes:
        if not any(line.startswith(prefix) for line in command_lines):
            errors.append(f"Missing required RouterOS command: {prefix}")

    for token in _find_unresolved_template_tokens(content):
        errors.append(f"Unresolved or forbidden token found: {token}")

    for index, line in enumerate(command_lines, start=1):
        is_routeros_command = line.startswith("/")
        is_routeros_script = line.startswith(":")

        if not is_routeros_command and not is_routeros_script:
            errors.append(
                f"Command line {index} does not start with a "
                f"RouterOS path or script statement: {line}"
            )

        if "\t" in line:
            warnings.append(
                f"Command line {index} contains a tab character"
            )

        if line.count('"') % 2 != 0:
            errors.append(
                f"Command line {index} has unbalanced quotes: {line}"
            )

    seen = set()
    duplicates = []
    for line in command_lines:
        if line in seen:
            duplicates.append(line)
        seen.add(line)

    for duplicate in duplicates:
        errors.append(f"Duplicate RouterOS command found: {duplicate}")

    if not content.endswith("\n"):
        warnings.append("RouterOS script should end with a newline")

    return RouterOSLintResult(
        valid=not errors,
        errors=errors,
        warnings=warnings,
    )


class ProductionRouterOSLintContext(StrictModel):
    router_id: str
    hotspot_id: str
    nas_identifier: str
    captive_dns_name: str
    portal_public_url: str
    radius_host: str


def lint_production_routeros_script(
    content: str,
    *,
    context: ProductionRouterOSLintContext,
) -> RouterOSLintResult:
    """
    Validate a rendered RouterOS artifact against the CAIWAVE production
    provisioning contract.

    This extends the generic RouterOS linter with router-specific and
    platform-specific requirements.
    """

    base = lint_routeros_script(content)

    errors = list(base.errors)
    warnings = list(base.warnings)

    required_tokens = [
        context.router_id,
        context.hotspot_id,
        context.nas_identifier,
        context.captive_dns_name,
        context.radius_host,
        "/file add",
        'name="hotspot/login.html"',
        "radius-accounting=yes",
        "radius-interim-update=5m",
        "require-message-auth=no",
        'list="CAIWAVE-PREAUTH"',
        'address="www.caiwave.com"',
        'address="checkout.paystack.com"',
        'dst-address-list="CAIWAVE-PREAUTH"',
        'hotspot="from-client,!auth"',
        'dst-port="80,443"',
    ]

    for token in required_tokens:
        if token not in content:
            errors.append(
                f"Missing production provisioning requirement: {token}"
            )

    expected_portal_prefix = (
        context.portal_public_url.rstrip("/")
        + "/portal/"
        + context.hotspot_id
    )

    if expected_portal_prefix not in content:
        errors.append(
            "Generated portal redirect does not use the expected "
            f"hotspot route: {expected_portal_prefix}"
        )

    forbidden_tokens = [
        "wifi.caiwave.com",
        "/portal/login?hotspot=",
        "?hotspot=",
        "router-radius-secret:router-1",
        'secret="testing123"',
        "# section planned: schedulers",
        "http://caiwave.com",
    ]

    for token in forbidden_tokens:
        if token in content:
            errors.append(
                f"Forbidden production provisioning token found: {token}"
            )

    required_command_prefixes = [
        "/file remove",
        "/file add",
    ]

    command_lines = [
        line.strip()
        for line in content.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    for prefix in required_command_prefixes:
        if not any(
            line.startswith(prefix)
            for line in command_lines
        ):
            errors.append(
                f"Missing production RouterOS command: {prefix}"
            )

    if context.portal_public_url.startswith("http://"):
        errors.append(
            "Production portal_public_url must use HTTPS"
        )

    preauth_allow_position = next(
        (
            index
            for index, line in enumerate(command_lines)
            if line.startswith("/ip firewall filter add")
            and 'dst-address-list="CAIWAVE-PREAUTH"' in line
            and 'hotspot="from-client,!auth"' in line
            and 'dst-port="80,443"' in line
            and 'protocol="tcp"' in line
            and 'action="accept"' in line
            and 'chain="forward"' in line
        ),
        None,
    )

    final_forward_drop_position = next(
        (
            index
            for index, line in enumerate(command_lines)
            if line.startswith("/ip firewall filter add")
            and 'chain="forward"' in line
            and 'action="drop"' in line
            and "CAIWAVE default drop unmatched forward" in line
        ),
        None,
    )

    established_forward_position = next(
        (
            index
            for index, line in enumerate(command_lines)
            if line.startswith("/ip firewall filter add")
            and 'chain="forward"' in line
            and 'action="accept"' in line
            and 'connection-state="established,related"' in line
        ),
        None,
    )

    authenticated_forward_position = next(
        (
            index
            for index, line in enumerate(command_lines)
            if line.startswith("/ip firewall filter add")
            and 'chain="forward"' in line
            and 'action="accept"' in line
            and 'hotspot="auth"' in line
        ),
        None,
    )

    if established_forward_position is None:
        errors.append(
            "Missing production established and related forward allowance"
        )

    if authenticated_forward_position is None:
        errors.append(
            "Missing production authenticated HotSpot forward allowance"
        )

    if preauth_allow_position is None:
        errors.append(
            "Missing production pre-auth forward allowance for "
            "CAIWAVE-PREAUTH on TCP ports 80,443"
        )

    if final_forward_drop_position is None:
        errors.append(
            "Missing production final unmatched forward drop"
        )

    if (
        established_forward_position is not None
        and final_forward_drop_position is not None
        and established_forward_position > final_forward_drop_position
    ):
        errors.append(
            "Production established forwarding must appear before "
            "the final unmatched forward drop"
        )

    if (
        authenticated_forward_position is not None
        and final_forward_drop_position is not None
        and authenticated_forward_position > final_forward_drop_position
    ):
        errors.append(
            "Production authenticated HotSpot forwarding must appear "
            "before the final unmatched forward drop"
        )

    if (
        preauth_allow_position is not None
        and final_forward_drop_position is not None
        and preauth_allow_position > final_forward_drop_position
    ):
        errors.append(
            "Production pre-auth forward allowance must appear before "
            "the final unmatched forward drop"
        )

    return RouterOSLintResult(
        valid=not errors,
        errors=errors,
        warnings=warnings,
    )
