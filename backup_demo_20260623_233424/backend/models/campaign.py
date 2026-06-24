"""
CAIWAVE Campaign & Stream Models
Pydantic models for campaigns, streams, and subsidized uptime.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid
from .enums import CampaignStatus, StreamAccessType, SubsidizedUptimeStatus


class CampaignBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    target_regions: List[str] = Field(default_factory=list)  # counties, constituencies
    target_hotspot_ids: List[str] = Field(default_factory=list)
    assigned_ad_ids: List[str] = Field(default_factory=list)
    stream_id: Optional[str] = None  # Link to CAIWAVE TV stream
    subsidized_uptime_id: Optional[str] = None  # Link to subsidized uptime


class CampaignCreate(CampaignBase):
    pass


class Campaign(CampaignBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: CampaignStatus = CampaignStatus.DRAFT
    created_by: str  # Admin user ID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_impressions: int = 0
    total_clicks: int = 0
    total_budget: float = 0.0
    spent_budget: float = 0.0


class StreamBase(BaseModel):
    name: str
    description: Optional[str] = None
    stream_url: str
    start_time: datetime
    end_time: datetime
    access_type: StreamAccessType = StreamAccessType.PAID
    price: float = 0.0  # Price if paid access
    allowed_hotspot_ids: List[str] = Field(default_factory=list)  # Empty = all hotspots
    allowed_regions: List[str] = Field(default_factory=list)  # counties
    pre_roll_ad_ids: List[str] = Field(default_factory=list)  # Ads to show before stream
    thumbnail_url: Optional[str] = None


class StreamCreate(StreamBase):
    pass


class Stream(StreamBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_by: str  # Admin user ID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    total_views: int = 0
    current_viewers: int = 0


class SubsidizedUptimeBase(BaseModel):
    name: str
    description: Optional[str] = None
    original_price: float  # Original package price
    discounted_price: float  # New lower price
    duration_hours: int  # How long the user gets access
    start_date: datetime
    end_date: datetime
    daily_start_time: Optional[str] = None  # e.g., "08:00" - optional time window
    daily_end_time: Optional[str] = None  # e.g., "22:00"
    allowed_hotspot_ids: List[str] = Field(default_factory=list)  # Empty = all
    allowed_regions: List[str] = Field(default_factory=list)
    max_uses: Optional[int] = None  # Optional limit on total uses
    linked_campaign_id: Optional[str] = None
    linked_stream_id: Optional[str] = None


class SubsidizedUptimeCreate(SubsidizedUptimeBase):
    pass


class SubsidizedUptime(SubsidizedUptimeBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: SubsidizedUptimeStatus = SubsidizedUptimeStatus.DRAFT
    created_by: str  # Admin user ID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_uses: int = 0
