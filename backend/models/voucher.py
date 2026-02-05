"""
CAIWAVE Voucher Models
Pydantic models for pre-paid vouchers.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, timezone
import uuid


class VoucherBase(BaseModel):
    package_id: str
    hotspot_id: str
    quantity: int = 1


class Voucher(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    package_id: str
    hotspot_id: str
    owner_id: str
    username: str
    password: str
    is_used: bool = False
    used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
