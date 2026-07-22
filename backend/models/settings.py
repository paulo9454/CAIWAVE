"""
CAIWAVE Settings & Marketplace Models
Pydantic models for system settings and marketplace items.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict
from datetime import datetime, timezone
import uuid
from .enums import NotificationType


class NotificationRequest(BaseModel):
    recipient: str  # Phone number or email
    message: str
    notification_type: NotificationType


class RevenueConfig(BaseModel):
    base_owner_percentage: float = 30.0  # Base percentage for partners
    coverage_bonus_per_100sqm: float = 0.5
    client_bonus_per_10: float = 0.5
    ad_impression_bonus_per_1000: float = 1.0
    uptime_bonus_threshold: float = 99.0
    uptime_bonus_percentage: float = 2.0
    max_owner_percentage: float = 50.0  # Maximum cap for partner share


class DynamicRevenue(BaseModel):
    total_amount: float
    owner_share: float
    platform_share: float
    owner_percentage: float
    breakdown: Dict[str, float]
    capped: bool = False  # Indicates if cap was applied


class SystemSettings(BaseModel):
    mpesa_enabled: bool = False
    bank_enabled: bool = False
    sms_enabled: bool = False
    whatsapp_enabled: bool = False
    email_enabled: bool = False
    voucher_printing_enabled: bool = True
    auto_approve_ads: bool = False  # Always False for CAIWAVE


class MarketplaceItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    merchant_name: str = "CAIWAVE Partner"
    category: str
    price: float
    original_price: Optional[float] = None
    currency: str = "KES"
    image_url: Optional[str] = None
    purchase_url: Optional[str] = None
    is_featured: bool = False
    is_active: bool = True
    click_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_clicked_at: Optional[str] = None
