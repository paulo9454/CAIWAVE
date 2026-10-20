"""
CAIWAVE MikroTik control-plane credentials.

This module is intentionally separate from:
- user JWT authentication
- RADIUS shared secrets
- provisioning artifact checksums

The router control-plane credential is a bearer credential used by
MikroTik devices when communicating with CAIWAVE over HTTPS.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional


DEFAULT_TTL_DAYS = 30


@dataclass(frozen=True)
class RouterControlCredential:
    """
    Newly generated router control credential.

    `secret` is returned to the caller for bootstrap and must not be
    persisted directly by this module.
    """

    credential_id: str
    secret: str
    secret_hash: str
    created_at: datetime
    expires_at: datetime


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def hash_control_secret(secret: str) -> str:
    """
    Return the SHA-256 digest used for persistent credential storage.
    """
    if not isinstance(secret, str) or not secret:
        raise ValueError("Control secret must be a non-empty string")

    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def generate_control_credential(
    ttl_days: int = DEFAULT_TTL_DAYS,
) -> RouterControlCredential:
    """
    Generate a new router control-plane credential.

    The secret is cryptographically random and is only returned to the
    caller. Persistent storage should retain `secret_hash`, not `secret`.
    """
    if ttl_days <= 0:
        raise ValueError("Credential TTL must be greater than zero")

    created_at = _utcnow()
    expires_at = created_at + timedelta(days=ttl_days)
    secret = secrets.token_urlsafe(32)

    return RouterControlCredential(
        credential_id=str(secrets.token_hex(16)),
        secret=secret,
        secret_hash=hash_control_secret(secret),
        created_at=created_at,
        expires_at=expires_at,
    )


def build_control_credential(
    ttl_days: int = DEFAULT_TTL_DAYS,
) -> RouterControlCredential:
    """
    Generate a complete credential with a matching secret hash.

    Kept separate from `generate_control_credential` so the construction
    logic remains explicit and easy to test.
    """
    if ttl_days <= 0:
        raise ValueError("Credential TTL must be greater than zero")

    created_at = _utcnow()
    expires_at = created_at + timedelta(days=ttl_days)
    secret = secrets.token_urlsafe(32)

    return RouterControlCredential(
        credential_id=secrets.token_hex(16),
        secret=secret,
        secret_hash=hash_control_secret(secret),
        created_at=created_at,
        expires_at=expires_at,
    )


def verify_control_secret(
    secret: str,
    secret_hash: str,
) -> bool:
    """
    Verify a presented router secret against its stored hash.

    Constant-time comparison is used to avoid timing-based comparison
    leaks.
    """
    if not isinstance(secret, str) or not secret:
        return False

    if not isinstance(secret_hash, str) or not secret_hash:
        return False

    try:
        computed_hash = hash_control_secret(secret)
        return hmac.compare_digest(computed_hash, secret_hash)
    except Exception:
        return False


def is_control_credential_active(
    *,
    expires_at: datetime,
    revoked_at: Optional[datetime] = None,
    now: Optional[datetime] = None,
) -> bool:
    """
    Return whether a credential is currently usable.

    A revoked credential is always inactive.
    An expired credential is always inactive.
    """
    if revoked_at is not None:
        return False

    current_time = now or _utcnow()

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    return current_time < expires_at


def serialize_credential(
    credential: RouterControlCredential,
) -> dict:
    """
    Produce the MongoDB-safe representation.

    The plaintext secret is deliberately excluded.
    """
    return {
        "credential_id": credential.credential_id,
        "secret_hash": credential.secret_hash,
        "created_at": credential.created_at.isoformat(),
        "expires_at": credential.expires_at.isoformat(),
        "status": "active",
    }
