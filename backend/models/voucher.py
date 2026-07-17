"""
Canonical CAIWAVE voucher models.

These contracts are shared by voucher generation, owner management,
captive-portal redemption, tests, and API response validation.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field


class VoucherPurpose(str, Enum):
    STANDARD = "standard"
    TEST = "test"
    COMPENSATION = "compensation"
    PROMOTION = "promotion"
    STAFF = "staff"
    OFFLINE_SALE = "offline_sale"


class VoucherRedemptionStatus(str, Enum):
    UNUSED = "unused"
    PROCESSING = "processing"
    REDEEMED = "redeemed"
    REVOKED = "revoked"


class VoucherBase(BaseModel):
    package_id: str
    hotspot_id: str
    quantity: int = Field(default=1, ge=1, le=1000)
    validity_days: int = Field(default=30, ge=1, le=365)
    purpose: VoucherPurpose = VoucherPurpose.STANDARD
    batch_name: Optional[str] = Field(
        default=None,
        max_length=120,
    )


class VoucherRevocationRequest(BaseModel):
    reason: str = Field(
        min_length=3,
        max_length=250,
    )


class Voucher(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    package_id: str
    hotspot_id: str
    owner_id: str
    generated_by: str
    purpose: VoucherPurpose = VoucherPurpose.STANDARD

    batch_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())
    )
    batch_name: Optional[str] = None

    username: str
    password: str

    is_used: bool = False
    redemption_status: VoucherRedemptionStatus = (
        VoucherRedemptionStatus.UNUSED
    )
    used_at: Optional[datetime] = None
    used_mac: Optional[str] = None
    used_ip: Optional[str] = None
    redeemed_session_id: Optional[str] = None

    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None
    revocation_reason: Optional[str] = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    expires_at: datetime
