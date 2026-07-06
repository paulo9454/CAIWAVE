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
