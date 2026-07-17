from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from backend.models.voucher import (
    Voucher,
    VoucherBase,
    VoucherPurpose,
)
from backend.server import (
    HotspotStatus,
    SessionStatus,
    UserRole,
)


def test_voucher_request_defaults():
    request = VoucherBase(
        package_id="pkg-30min",
        hotspot_id="hotspot-1",
    )

    assert request.quantity == 1


def test_voucher_quantity_must_be_positive():
    with pytest.raises(ValidationError):
        VoucherBase(
            package_id="pkg-30min",
            hotspot_id="hotspot-1",
            quantity=0,
        )


def test_voucher_stores_radius_credentials():
    voucher = Voucher(
        code="CAITEST01",
        package_id="pkg-30min",
        hotspot_id="hotspot-1",
        owner_id="owner-1",
        generated_by="admin-1",
        purpose=VoucherPurpose.TEST,
        username="testuser",
        password="testpass",
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )

    assert voucher.is_used is False
    assert voucher.username == "testuser"
    assert voucher.password == "testpass"
    assert voucher.used_at is None
    assert voucher.generated_by == "admin-1"
    assert voucher.purpose == VoucherPurpose.TEST
    assert voucher.redemption_status == "unused"
    assert voucher.used_mac is None
    assert voucher.used_ip is None
    assert voucher.redeemed_session_id is None


def test_required_roles_exist():
    assert UserRole.SUPER_ADMIN.value == "super_admin"
    assert UserRole.HOTSPOT_OWNER.value == "hotspot_owner"


def test_required_hotspot_states_exist():
    assert HotspotStatus.ACTIVE.value == "active"
    assert HotspotStatus.SUSPENDED.value == "suspended"


def test_active_session_status_exists():
    assert SessionStatus.ACTIVE.value == "active"


def test_voucher_purpose_rejects_unknown_value():
    with pytest.raises(ValidationError):
        VoucherBase(
            package_id="pkg-30min",
            hotspot_id="hotspot-1",
            purpose="unknown-purpose",
        )


def test_voucher_request_validity_defaults():
    request = VoucherBase(
        package_id="pkg-30min",
        hotspot_id="hotspot-1",
    )

    assert request.validity_days == 30
    assert request.purpose == VoucherPurpose.STANDARD


def test_voucher_validity_must_be_within_bounds():
    with pytest.raises(ValidationError):
        VoucherBase(
            package_id="pkg-30min",
            hotspot_id="hotspot-1",
            validity_days=0,
        )

    with pytest.raises(ValidationError):
        VoucherBase(
            package_id="pkg-30min",
            hotspot_id="hotspot-1",
            validity_days=366,
        )


def test_voucher_quantity_has_upper_limit():
    with pytest.raises(ValidationError):
        VoucherBase(
            package_id="pkg-30min",
            hotspot_id="hotspot-1",
            quantity=1001,
        )


def test_server_uses_canonical_voucher_models():
    from backend.models.voucher import (
        Voucher as CanonicalVoucher,
        VoucherBase as CanonicalVoucherBase,
        VoucherPurpose as CanonicalVoucherPurpose,
    )
    import backend.server as server

    assert server.Voucher is CanonicalVoucher
    assert server.VoucherBase is CanonicalVoucherBase
    assert server.VoucherPurpose is CanonicalVoucherPurpose


def test_voucher_lifecycle_defaults():
    from backend.models.voucher import VoucherRedemptionStatus

    voucher = Voucher(
        code="CAIBATCH1",
        package_id="pkg-30min",
        hotspot_id="hotspot-1",
        owner_id="owner-1",
        generated_by="owner-1",
        username="voucher-user",
        password="voucher-pass",
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )

    assert voucher.batch_id
    assert voucher.batch_name is None
    assert voucher.redemption_status == VoucherRedemptionStatus.UNUSED
    assert voucher.revoked_at is None
    assert voucher.revoked_by is None
    assert voucher.revocation_reason is None


def test_voucher_accepts_batch_metadata():
    voucher = Voucher(
        code="CAIBATCH2",
        package_id="pkg-30min",
        hotspot_id="hotspot-1",
        owner_id="owner-1",
        generated_by="owner-1",
        batch_id="batch-2026-001",
        batch_name="Weekend compensation",
        username="voucher-user",
        password="voucher-pass",
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )

    assert voucher.batch_id == "batch-2026-001"
    assert voucher.batch_name == "Weekend compensation"


def test_voucher_redemption_status_rejects_unknown_value():
    with pytest.raises(ValidationError):
        Voucher(
            code="CAIBATCH3",
            package_id="pkg-30min",
            hotspot_id="hotspot-1",
            owner_id="owner-1",
            generated_by="owner-1",
            username="voucher-user",
            password="voucher-pass",
            redemption_status="deleted",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )


def test_voucher_request_accepts_batch_name():
    request = VoucherBase(
        package_id="pkg-30min",
        hotspot_id="hotspot-1",
        batch_name="Weekend sales",
    )

    assert request.batch_name == "Weekend sales"


def test_voucher_batch_name_has_length_limit():
    with pytest.raises(ValidationError):
        VoucherBase(
            package_id="pkg-30min",
            hotspot_id="hotspot-1",
            batch_name="x" * 121,
        )
