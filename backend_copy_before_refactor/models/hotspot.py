"""
CAIWAVE Hotspot Models
Pydantic models for hotspot configuration and management.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid
from .enums import HotspotStatus, SubscriptionStatus


class MikroTikConfig(BaseModel):
    ip_address: str
    api_port: int = 8728
    api_username: str = "admin"
    api_password: str = ""
    hotspot_server: str = "hotspot1"
    radius_secret: str = ""


class HotspotBase(BaseModel):
    name: str
    ssid: str
    location_name: str
    ward: Optional[str] = None
    constituency: Optional[str] = None
    county: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    mikrotik_config: Optional[MikroTikConfig] = None
    username_prefix: str = ""
    captive_portal_language: str = "en"
    redirect_url: Optional[str] = None
    auto_prune_days: int = 30


class HotspotCreate(HotspotBase):
    owner_id: Optional[str] = None


class Hotspot(HotspotBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_id: str
    status: HotspotStatus = HotspotStatus.PENDING_SETUP
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_revenue: float = 0.0
    total_sessions: int = 0
    total_data_mb: float = 0.0
    uptime_percentage: float = 100.0
    last_seen: Optional[datetime] = None
    enabled_packages: List[str] = Field(default_factory=list)  # Package IDs
    # Dynamic revenue factors
    coverage_area_sqm: float = 100.0
    avg_daily_clients: int = 0
    ad_impressions_delivered: int = 0
    # Subscription fields
    subscription_status: SubscriptionStatus = SubscriptionStatus.TRIAL
    trial_start_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
