"""
Identity Module for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no route wiring
- no legacy provisioning changes

This module normalizes and validates CAIWAVE router identity and produces
a stable identity fingerprint for artifact traceability.
"""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from typing import Any, Dict

from backend.schemas.provisioning_v2 import ProvisioningSnapshot


class IdentityModuleError(ValueError):
    """Raised when router identity is invalid or unsafe."""


_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.,:-]{0,127}$")
_SAFE_NAS_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{2,127}$")


def _require_safe(value: str, field: str, pattern: re.Pattern[str]) -> str:
    if not isinstance(value, str) or not value.strip():
        raise IdentityModuleError(f"{field} is required")
    normalized = value.strip()
    if not pattern.match(normalized):
        raise IdentityModuleError(f"{field} contains unsafe characters or length")
    return normalized


def _stable_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def identity_fingerprint(identity: Dict[str, Any]) -> str:
    """Return a stable SHA256 fingerprint for normalized identity fields."""
    return hashlib.sha256(_stable_json(identity).encode("utf-8")).hexdigest()


def normalize_identity(snapshot: ProvisioningSnapshot) -> Dict[str, Any]:
    """
    Normalize and validate identity from a ProvisioningSnapshot.

    Does not mutate the snapshot.
    """

    snap = deepcopy(snapshot)

    router_id = _require_safe(snap.identity.router_id, "router_id", _SAFE_ID_RE)
    owner_id = _require_safe(snap.identity.owner_id, "owner_id", _SAFE_ID_RE)
    hotspot_id = _require_safe(snap.identity.hotspot_id, "hotspot_id", _SAFE_ID_RE)
    router_name = _require_safe(snap.identity.router_name, "router_name", _SAFE_NAME_RE)
    nas_identifier = _require_safe(
        snap.identity.nas_identifier, "nas_identifier", _SAFE_NAS_RE
    )

    if snap.router_id != router_id:
        raise IdentityModuleError("snapshot.router_id does not match identity.router_id")
    if snap.owner_id != owner_id:
        raise IdentityModuleError("snapshot.owner_id does not match identity.owner_id")
    if snap.hotspot_id != hotspot_id:
        raise IdentityModuleError("snapshot.hotspot_id does not match identity.hotspot_id")
    if snap.radius.nas_identifier != nas_identifier:
        raise IdentityModuleError(
            "snapshot.radius.nas_identifier does not match identity.nas_identifier"
        )

    normalized = {
        "router_id": router_id,
        "router_name": router_name,
        "owner_id": owner_id,
        "hotspot_id": hotspot_id,
        "nas_identifier": nas_identifier,
        "snapshot_id": snap.snapshot_id,
        "environment": snap.environment.value,
    }
    normalized["identity_fingerprint"] = identity_fingerprint(normalized)
    return normalized
