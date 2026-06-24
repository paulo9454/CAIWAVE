"""
CAIWAVE Session Models
Pydantic models for WiFi sessions.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, timezone
import uuid
from .enums import SessionStatus


class SessionBase(BaseModel):
    package_id: str
    hotspot_id: str
    user_mac: Optional[str] = None
    user_ip: Optional[str] = None


class SessionCreate(SessionBase):
    user_id: Optional[str] = None
    phone_number: Optional[str] = None


class Session(SessionBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    phone_number: Optional[str] = None
    username: str = ""  # RADIUS username
    password: str = ""  # RADIUS password (for vouchers)
    status: SessionStatus = SessionStatus.ACTIVE
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    data_used_mb: float = 0.0
    is_free: bool = False
    voucher_code: Optional[str] = None
    payment_id: Optional[str] = None
