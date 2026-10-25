"""
RouterOS Command Builder for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no route wiring
- no legacy provisioning changes

This module provides safe, deterministic RouterOS command construction.
It does not decide what to configure; section renderers will use this
builder to translate validated plans into RouterOS syntax.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List


class RawRouterOSValue(str):
    """A RouterOS value that should be emitted without quotes."""


class RouterOSCommandBuilderError(ValueError):
    """Raised when a RouterOS command cannot be safely built."""


_SAFE_PATH_RE = re.compile(r"^/[A-Za-z0-9 _/-]+$")
_SAFE_KEY_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def quote_routeros_value(value: Any) -> str:
    """
    Quote and escape a RouterOS value deterministically.

    RouterOS strings use double quotes. Backslashes and double quotes must be
    escaped. Newlines are rejected because generated scripts must remain
    one command per line.
    """

    if value is None:
        raise RouterOSCommandBuilderError("RouterOS value cannot be None")

    if isinstance(value, bool):
        return "yes" if value else "no"

    text = str(value)

    if "\n" in text or "\r" in text:
        raise RouterOSCommandBuilderError("RouterOS values must not contain newlines")

    text = text.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$")
    return f'"{text}"'


def build_set_arg(key: str, value: Any) -> str:
    if not _SAFE_KEY_RE.match(key):
        raise RouterOSCommandBuilderError(f"Unsafe RouterOS argument key: {key}")
    if isinstance(value, RawRouterOSValue):
        return f"{key}={value}"
    return f"{key}={quote_routeros_value(value)}"


def build_command(path: str, action: str, args: Dict[str, Any] | None = None) -> str:
    """
    Build a deterministic RouterOS command.

    Example:
    /interface bridge add name="bridge-hotspot"
    """

    if not _SAFE_PATH_RE.match(path):
        raise RouterOSCommandBuilderError(f"Unsafe RouterOS path: {path}")
    if not _SAFE_KEY_RE.match(action):
        raise RouterOSCommandBuilderError(f"Unsafe RouterOS action: {action}")

    parts: List[str] = [path.strip(), action.strip()]

    for key in sorted((args or {}).keys()):
        value = args[key]
        if value is None:
            continue
        parts.append(build_set_arg(key, value))

    return " ".join(parts)



def build_guarded_add(
    path: str,
    action: str,
    args: Dict[str, Any] | None = None,
    *,
    selector_keys: tuple[str, ...] | None = None,
) -> str:
    """Build an add command guarded against creating the same managed entry twice."""
    if action != "add":
        raise RouterOSCommandBuilderError(
            "build_guarded_add only supports the add action"
        )

    values = args or {}

    preferred_selectors = {
        "/ip dns static": ("name", "comment"),
        "/ip firewall nat": (
            "chain", "action", "src-address", "out-interface", "comment"
        ),
        "/ip firewall address-list": ("list", "address", "comment"),
        "/radius": ("comment",),
        "/ip hotspot walled-garden": ("dst-host", "comment"),
    }

    if selector_keys is None:
        selector_keys = preferred_selectors.get(path)

    if selector_keys is None:
        selector_keys = tuple(
            key for key, value in values.items() if value is not None
        )

    if not selector_keys:
        raise RouterOSCommandBuilderError(
            f"No stable selectors supplied for guarded RouterOS add: {path}"
        )

    selector_parts = []
    for key in selector_keys:
        if key not in values or values[key] is None:
            raise RouterOSCommandBuilderError(
                f"Missing selector {key!r} for guarded RouterOS add: {path}"
            )
        selector_parts.append(build_set_arg(key, values[key]))

    selector = " and ".join(selector_parts)
    command = build_command(path, action, values)

    return (
        f":if ([:len [{path} find where {selector}]] = 0) "
        f"do={{ {command}; }}"
    )


def build_comment(text: str) -> str:
    if "\n" in text or "\r" in text:
        raise RouterOSCommandBuilderError("Comment must be a single line")
    return f"# {text}"


def build_section(title: str, commands: List[str]) -> str:
    if not title.strip():
        raise RouterOSCommandBuilderError("Section title is required")

    lines = [
        build_comment("=" * 72),
        build_comment(title.strip()),
        build_comment("=" * 72),
    ]
    lines.extend(command for command in commands if command.strip())
    return "\n".join(lines)


def join_script(sections: List[str]) -> str:
    return "\n\n".join(section.strip() for section in sections if section.strip()) + "\n"
