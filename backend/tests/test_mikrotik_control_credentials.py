from datetime import datetime, timedelta, timezone

import pytest

from backend.services.mikrotik_control_plane.credentials import (
    build_control_credential,
    hash_control_secret,
    is_control_credential_active,
    serialize_credential,
    verify_control_secret,
)


def test_generate_control_credential_generates_matching_secret_and_hash():
    from backend.services.mikrotik_control_plane.credentials import (
        generate_control_credential,
    )

    credential = generate_control_credential()

    assert credential.credential_id
    assert credential.secret
    assert credential.secret_hash
    assert credential.secret_hash == hash_control_secret(
        credential.secret
    )


def test_build_control_credential_generates_secret_and_hash():
    credential = build_control_credential()

    assert credential.credential_id
    assert credential.secret
    assert credential.secret_hash

    assert credential.secret_hash == hash_control_secret(
        credential.secret
    )


def test_control_credentials_are_unique():
    first = build_control_credential()
    second = build_control_credential()

    assert first.credential_id != second.credential_id
    assert first.secret != second.secret
    assert first.secret_hash != second.secret_hash


def test_verify_control_secret_accepts_correct_secret():
    credential = build_control_credential()

    assert verify_control_secret(
        credential.secret,
        credential.secret_hash,
    )


def test_verify_control_secret_rejects_wrong_secret():
    credential = build_control_credential()

    assert not verify_control_secret(
        "wrong-secret",
        credential.secret_hash,
    )


def test_verify_control_secret_rejects_empty_values():
    assert not verify_control_secret("", "abc")
    assert not verify_control_secret("abc", "")
    assert not verify_control_secret("", "")


def test_credential_is_active_before_expiry():
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=10)

    assert is_control_credential_active(
        expires_at=expires_at,
        now=now,
    )


def test_credential_is_inactive_after_expiry():
    now = datetime.now(timezone.utc)
    expires_at = now - timedelta(seconds=1)

    assert not is_control_credential_active(
        expires_at=expires_at,
        now=now,
    )


def test_revoked_credential_is_inactive():
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=1)
    revoked_at = now

    assert not is_control_credential_active(
        expires_at=expires_at,
        revoked_at=revoked_at,
        now=now,
    )


def test_credential_serialization_does_not_expose_secret():
    credential = build_control_credential()

    stored = serialize_credential(credential)

    assert credential.secret not in stored.values()
    assert "secret" not in stored
    assert stored["secret_hash"] == credential.secret_hash
    assert stored["credential_id"] == credential.credential_id
    assert stored["status"] == "active"


def test_invalid_ttl_is_rejected():
    with pytest.raises(ValueError):
        build_control_credential(ttl_days=0)

    with pytest.raises(ValueError):
        build_control_credential(ttl_days=-1)
