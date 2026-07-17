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
