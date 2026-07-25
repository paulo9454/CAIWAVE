from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SERVER = (ROOT / "backend/server.py").read_text()


def registration_block() -> str:
    start = SERVER.index("PUBLIC_REGISTRATION_ROLES =")
    end = SERVER.index(
        '@auth_router.post("/login", response_model=dict)',
        start,
    )
    return SERVER[start:end]


def test_public_registration_allows_hotspot_owners_only():
    block = registration_block()

    assert "PUBLIC_REGISTRATION_ROLES = frozenset({" in block
    assert "UserRole.HOTSPOT_OWNER," in block

    role_set = block.split(
        "PUBLIC_REGISTRATION_ROLES = frozenset({",
        1,
    )[1].split("})", 1)[0]

    assert "UserRole.ADVERTISER" not in role_set
    assert "UserRole.SUPER_ADMIN" not in role_set
    assert "UserRole.END_USER" not in role_set


def test_register_rejects_disallowed_roles_with_403():
    block = registration_block()

    assert (
        "if user_data.role not in PUBLIC_REGISTRATION_ROLES:"
        in block
    )
    assert "raise HTTPException(" in block
    assert "status_code=403" in block
    assert (
        '"Public registration is currently available "'
        in block
    )
    assert '"to hotspot owners only."' in block


def test_role_rejection_happens_before_database_lookup():
    block = registration_block()

    role_check = block.index(
        "if user_data.role not in PUBLIC_REGISTRATION_ROLES:"
    )
    database_lookup = block.index(
        'existing = await db.users.find_one({"email": user_data.email})'
    )

    assert role_check < database_lookup


def test_register_route_remains_publicly_registered():
    block = registration_block()

    assert (
        '@auth_router.post("/register", response_model=dict)'
        in block
    )
    assert "async def register(user_data: UserCreate):" in block
