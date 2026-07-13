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

    forbidden_tokens = ["{{", "}}", "${", "<TODO", "TODO:", "None"]
    for token in forbidden_tokens:
        if token in content:
            errors.append(f"Unresolved or forbidden token found: {token}")

    for index, line in enumerate(command_lines, start=1):
        if not line.startswith("/"):
            errors.append(f"Command line {index} does not start with RouterOS path: {line}")
        if "\t" in line:
            warnings.append(f"Command line {index} contains a tab character")
        if line.count('"') % 2 != 0:
            errors.append(f"Command line {index} has unbalanced quotes: {line}")

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
    heartbeat_url: str


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
        context.heartbeat_url,
        "/file add",
        'name="hotspot/login.html"',
        "radius-accounting=yes",
        "radius-interim-update=5m",
        "/system script add",
        'name="caiwave-heartbeat"',
        'name="caiwave-confirm"',
        "/system scheduler add",
        "/system script run caiwave-confirm",
        "/system script run caiwave-heartbeat",
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
        "/system script remove",
        "/system script add",
        "/system scheduler remove",
        "/system scheduler add",
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

    if context.heartbeat_url.startswith("http://"):
        errors.append(
            "Production heartbeat_url must use HTTPS"
        )

    return RouterOSLintResult(
        valid=not errors,
        errors=errors,
        warnings=warnings,
    )
