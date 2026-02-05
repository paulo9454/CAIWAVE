"""
CAIWAVE Payment Models
Pydantic models for payment processing.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from .enums import PaymentStatus, PaymentMethod


class PaymentBase(BaseModel):
    amount: float
    phone_number: str
    method: PaymentMethod = PaymentMethod.MPESA


class PaymentCreate(PaymentBase):
    hotspot_id: str
    package_id: str


class Payment(PaymentBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hotspot_id: str
    package_id: str
    session_id: Optional[str] = None
    status: PaymentStatus = PaymentStatus.PENDING
    mpesa_checkout_request_id: Optional[str] = None
    mpesa_receipt: Optional[str] = None
    bank_reference: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    # Revenue sharing
    owner_share: float = 0.0
    platform_share: float = 0.0


class MPesaSTKPushRequest(BaseModel):
    phone_number: str
    amount: float
    account_reference: str
    transaction_desc: str


class MPesaSTKCallback(BaseModel):
    Body: Dict[str, Any]
