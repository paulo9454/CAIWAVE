import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from backend import server


@pytest.mark.parametrize(
    "role",
    [
        server.UserRole.SUPER_ADMIN,
        server.UserRole.ADVERTISER,
        server.UserRole.END_USER,
    ],
)
def test_public_registration_rejects_non_owner_roles(monkeypatch, role):
    # The role check must reject the request before accessing the database.
    monkeypatch.setattr(server, "db", object())

    payload = server.UserCreate(
        email=f"{role.value}@example.com",
        name="Staging Test",
        password="test-only-password",
        role=role,
    )

    with pytest.raises(HTTPException) as exc:
        asyncio.run(server.register(payload))

    assert exc.value.status_code == 403
    assert exc.value.detail == (
        "Public registration is currently available "
        "to hotspot owners only."
    )


def test_public_registration_allows_hotspot_owner(monkeypatch):
    class FakeUsers:
        def __init__(self):
            self.document = None

        async def find_one(self, query):
            return None

        async def insert_one(self, document):
            self.document = dict(document)

    fake_users = FakeUsers()
    monkeypatch.setattr(
        server, "db", SimpleNamespace(users=fake_users)
    )
    monkeypatch.setattr(
        server, "hash_password", lambda password: "test-password-hash"
    )
    monkeypatch.setattr(
        server, "create_token", lambda user_id, role: "test-staging-token"
    )

    payload = server.UserCreate(
        email="staging-owner@example.com",
        name="Staging Owner",
        password="test-only-password",
        role=server.UserRole.HOTSPOT_OWNER,
    )

    result = asyncio.run(server.register(payload))

    assert fake_users.document is not None
    assert fake_users.document["role"] == server.UserRole.HOTSPOT_OWNER
    assert result["token"] == "test-staging-token"
    assert result["user"]["email"] == "staging-owner@example.com"
