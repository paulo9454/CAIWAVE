"""
CAIWAVE Advertisement Models
Pydantic models for advertising packages and ads.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid
from .enums import AdType, AdStatus, AdCoverageScope, AdPackageStatus


class AdPackage(BaseModel):
    """Admin-created advertising packages with fixed pricing"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # Small Area, Large Area, Wide Area
    description: str
    coverage_scope: AdCoverageScope  # constituency, county, national
    duration_days: int
    price: float  # Price in KES
    max_impressions: Optional[int] = None  # Optional cap
    status: AdPackageStatus = AdPackageStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


class AdPackageCreate(BaseModel):
    """Create a new ad package (Admin only)"""
    name: str
    description: str
    coverage_scope: AdCoverageScope
    duration_days: int
    price: float
    max_impressions: Optional[int] = None


class AdPackageUpdate(BaseModel):
    """Update an ad package (Admin only)"""
    name: Optional[str] = None
    description: Optional[str] = None
    coverage_scope: Optional[AdCoverageScope] = None
    duration_days: Optional[int] = None
    price: Optional[float] = None
    max_impressions: Optional[int] = None
    status: Optional[AdPackageStatus] = None


class AdTargeting(BaseModel):
    """Coverage selection for ads"""
    constituencies: List[str] = Field(default_factory=list)  # Selected constituencies
    counties: List[str] = Field(default_factory=list)  # For county/national scope
    is_national: bool = False  # True for national coverage


class Ad(BaseModel):
    """Full ad model with package-based pricing"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    ad_type: AdType
    advertiser_id: str
    
    # Package reference (required)
    package_id: str
    package_name: Optional[str] = None  # Denormalized for display
    package_price: float = 0.0  # Price at time of purchase
    
    # Media storage
    media_path: Optional[str] = None  # Local file path
    media_url: Optional[str] = None  # URL to access media
    media_size_bytes: int = 0
    duration_seconds: int = 0  # For videos
    
    # Optional link
    click_url: Optional[str] = None
    
    # Coverage selection by advertiser (validated by admin)
    targeting: AdTargeting = Field(default_factory=AdTargeting)
    
    # Status flow: PENDING_APPROVAL → APPROVED → PAID → ACTIVE
    status: AdStatus = AdStatus.PENDING_APPROVAL
    
    # Admin controls
    rejection_reason: Optional[str] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    admin_notes: Optional[str] = None  # Admin notes on coverage validation
    
    # Payment
    payment_id: Optional[str] = None
    paid_at: Optional[datetime] = None
    
    # Activation period
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Stats
    impressions: int = 0
    clicks: int = 0
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = False


class AdApproval(BaseModel):
    """Admin approval - no price negotiation"""
    approved: bool
    rejection_reason: Optional[str] = None
    admin_notes: Optional[str] = None  # Notes on coverage validation


class AdPaymentRequest(BaseModel):
    """Request payment for an approved ad"""
    phone_number: str
