"""
CAIWAVE Invoice & Subscription Models
Pydantic models for billing and subscriptions.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid
from .enums import InvoiceStatus


class Invoice(BaseModel):
    """Monthly subscription invoice for hotspot owners"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invoice_number: str = ""  # INV-YYYYMM-XXXX format
    owner_id: str
    hotspot_ids: List[str] = Field(default_factory=list)
    
    # Billing period
    billing_period_start: datetime
    billing_period_end: datetime
    
    # Amount
    amount: float  # KES 500 × number of hotspots
    hotspot_count: int = 1
    
    # Status
    status: InvoiceStatus = InvoiceStatus.DRAFT
    
    # Dates
    due_date: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    paid_at: Optional[datetime] = None
    
    # Payment details
    payment_method: Optional[str] = None
    mpesa_checkout_id: Optional[str] = None
    mpesa_receipt_number: Optional[str] = None
    mpesa_transaction_date: Optional[str] = None
    
    # Reminders
    reminder_sent_day_11: bool = False
    reminder_sent_day_13: bool = False
    reminder_sent_day_14: bool = False


class InvoiceCreate(BaseModel):
    """Create invoice for owner"""
    owner_id: str
    hotspot_ids: List[str]


class InvoicePaymentRequest(BaseModel):
    """Request to pay invoice via M-Pesa"""
    phone_number: str
