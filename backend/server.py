"""
CAIWAVE Wi-Fi Hotspot Billing Platform
Main FastAPI Application

Refactored to use modular architecture:
- /models: Pydantic models and enums  
- /services: Business logic (M-Pesa, SMS, WhatsApp, Notifications)
- /utils: Helper functions (auth, vouchers, revenue, locations)
- /config.py: Configuration management
- /database.py: MongoDB connection
"""
from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Query, BackgroundTasks, UploadFile, File, Form, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import json
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
from enum import Enum
import httpx
import base64
import hashlib
import shutil
import mimetypes
import secrets as secrets_module

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create upload directories
UPLOAD_DIR = ROOT_DIR / "uploads" / "ads"
UPLOAD_DIR_IMAGES = UPLOAD_DIR / "images"
UPLOAD_DIR_VIDEOS = UPLOAD_DIR / "videos"
UPLOAD_DIR_IMAGES.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR_VIDEOS.mkdir(parents=True, exist_ok=True)

# Media validation constants
MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2MB (600x600 recommended)
MAX_VIDEO_SIZE = 10 * 1024 * 1024  # 10MB
MAX_VIDEO_DURATION = 15  # seconds
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]
ALLOWED_VIDEO_TYPES = ["video/mp4", "video/webm"]

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'caiwave-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# M-Pesa Configuration (Daraja API) - DEPRECATED, using Paystack now
MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY', '')
MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET', '')
MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE', '')
MPESA_PASSKEY = os.environ.get('MPESA_PASSKEY', '')
MPESA_CALLBACK_URL = os.environ.get('MPESA_CALLBACK_URL', '')
MPESA_ENV = os.environ.get('MPESA_ENV', 'sandbox')

# Paystack Configuration (Primary Payment Gateway)
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY', '')
PAYSTACK_PUBLIC_KEY = os.environ.get('PAYSTACK_PUBLIC_KEY', '')
PAYSTACK_WEBHOOK_SECRET = os.environ.get('PAYSTACK_WEBHOOK_SECRET', '')
PAYSTACK_ENVIRONMENT = os.environ.get('PAYSTACK_ENVIRONMENT', 'live')

# SMS Configuration
SMS_PROVIDER = os.environ.get('SMS_PROVIDER', 'africas_talking')  # 'africas_talking', 'centipid', etc.
SMS_API_KEY = os.environ.get('SMS_API_KEY', '')
SMS_USERNAME = os.environ.get('SMS_USERNAME', '')
SMS_SENDER_ID = os.environ.get('SMS_SENDER_ID', 'CAIWAVE')

# Twilio WhatsApp Configuration
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_WHATSAPP_NUMBER = os.environ.get('TWILIO_WHATSAPP_NUMBER', '')

# FreeRADIUS Configuration
RADIUS_HOST = os.environ.get('RADIUS_HOST', 'localhost')
RADIUS_SECRET = os.environ.get('RADIUS_SECRET', 'testing123')
RADIUS_AUTH_PORT = int(os.environ.get('RADIUS_AUTH_PORT', '1812'))
RADIUS_ACCT_PORT = int(os.environ.get('RADIUS_ACCT_PORT', '1813'))

# Create the main app
app = FastAPI(
    title="CAIWAVE Wi-Fi Hotspot Billing Platform", 
    version="2.1.0",
    description="ISP-grade Wi-Fi hotspot billing and advertising platform for www.caiwave.com"
)

# Mount static files for ad media
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR.parent)), name="uploads")

# Create routers
api_router = APIRouter(prefix="/api")
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
packages_router = APIRouter(prefix="/packages", tags=["Packages"])
hotspots_router = APIRouter(prefix="/hotspots", tags=["Hotspots"])
sessions_router = APIRouter(prefix="/sessions", tags=["Sessions"])
payments_router = APIRouter(prefix="/payments", tags=["Payments"])
mpesa_router = APIRouter(prefix="/mpesa", tags=["M-Pesa (Legacy)"])
paystack_router = APIRouter(prefix="/payments", tags=["Payments (Paystack)"])
ads_router = APIRouter(prefix="/ads", tags=["Advertisements"])
ad_packages_router = APIRouter(prefix="/ad-packages", tags=["Ad Packages"])
campaigns_router = APIRouter(prefix="/campaigns", tags=["Campaigns"])
streams_router = APIRouter(prefix="/streams", tags=["CAIWAVE TV"])
subsidized_router = APIRouter(prefix="/subsidized-uptime", tags=["Subsidized Uptime"])
analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])
locations_router = APIRouter(prefix="/locations", tags=["Locations"])
radius_router = APIRouter(prefix="/radius", tags=["RADIUS"])
mikrotik_onboard_router = APIRouter(prefix="/mikrotik-onboard", tags=["MikroTik Onboarding"])
notifications_router = APIRouter(prefix="/notifications", tags=["Notifications"])
settings_router = APIRouter(prefix="/settings", tags=["Settings"])
vouchers_router = APIRouter(prefix="/vouchers", tags=["Vouchers"])
marketplace_router = APIRouter(prefix="/marketplace", tags=["Marketplace"])
invoices_router = APIRouter(prefix="/invoices", tags=["Invoices"])
subscriptions_router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])

security = HTTPBearer()

# ==================== Enums ====================

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    HOTSPOT_OWNER = "hotspot_owner"
    ADVERTISER = "advertiser"
    END_USER = "end_user"

class AdType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"

class AdStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAYMENT_ENABLED = "payment_enabled"
    PAID = "paid"
    ACTIVE = "active"
    SUSPENDED = "suspended"

class SessionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PaymentMethod(str, Enum):
    MPESA = "mpesa"
    PAYSTACK = "paystack"
    BANK = "bank"
    VOUCHER = "voucher"
    FREE_AD = "free_ad"

class HotspotStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_SETUP = "pending_setup"

class NotificationType(str, Enum):
    SMS = "sms"
    WHATSAPP = "whatsapp"
    EMAIL = "email"

class CampaignStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"

class StreamAccessType(str, Enum):
    FREE = "free"
    DISCOUNTED = "discounted"
    SPONSORED = "sponsored"
    PAID = "paid"

class SubsidizedUptimeStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    EXPIRED = "expired"

class AdCoverageScope(str, Enum):
    CONSTITUENCY = "constituency"
    COUNTY = "county"
    NATIONAL = "national"

class AdPackageStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"

class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    TRIAL = "trial"
    UNPAID = "unpaid"
    PAID = "paid"
    OVERDUE = "overdue"

class SubscriptionStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    GRACE_PERIOD = "grace_period"  # Day 15-17
    SUSPENDED = "suspended"  # Day 18+

# ==================== Models ====================

# User Models
class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    role: UserRole = UserRole.END_USER

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    balance: float = 0.0
    notification_preferences: Dict[str, bool] = Field(default_factory=lambda: {
        "sms_enabled": True,
        "whatsapp_enabled": False,
        "email_enabled": True
    })

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    phone: Optional[str]
    role: UserRole
    is_active: bool
    balance: float

# Package Models - UPDATED PRICING
class PackageBase(BaseModel):
    name: str
    price: float  # KES
    duration_minutes: int
    speed_mbps: float = 10.0
    data_limit_mb: Optional[int] = None  # None = unlimited
    description: Optional[str] = None
    is_active: bool = True

class Package(PackageBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Hotspot Models
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

# Subscription Invoice Model
SUBSCRIPTION_PRICE_KES = 500  # KES 500 per hotspot per month
TRIAL_DAYS = 14
GRACE_PERIOD_DAYS = 3  # Day 15-17
SUSPENSION_DAY = 18

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

# Session Models
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

# Payment Models
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

# M-Pesa Models
class MPesaSTKPushRequest(BaseModel):
    phone_number: str
    amount: float
    account_reference: str
    transaction_desc: str

class MPesaSTKCallback(BaseModel):
    Body: Dict[str, Any]

# Ad Models - WITH APPROVAL WORKFLOW
# ==================== Advertising Package Models ====================

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

# ==================== Ad Targeting and Coverage ====================

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

# Voucher Models
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

# Notification Models
class NotificationRequest(BaseModel):
    recipient: str  # Phone number or email
    message: str
    notification_type: NotificationType

# Revenue Sharing Models
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

# Settings Models
class SystemSettings(BaseModel):
    mpesa_enabled: bool = False
    bank_enabled: bool = False
    sms_enabled: bool = False
    whatsapp_enabled: bool = False
    email_enabled: bool = False
    voucher_printing_enabled: bool = True
    auto_approve_ads: bool = False  # Always False for CAIWAVE

# Marketplace Models
class MarketplaceItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    category: str  # router, access_point, accessory, tutorial
    price: float
    image_url: Optional[str] = None
    purchase_url: Optional[str] = None
    is_active: bool = True

# Campaign Models - ADMIN ONLY
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

# CAIWAVE TV Stream Models - ADMIN ONLY
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

# Subsidized Uptime Models - ADMIN ONLY
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

# ==================== Helper Functions ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_role(allowed_roles: List[UserRole]):
    async def role_checker(user: dict = Depends(get_current_user)):
        if user["role"] not in [r.value for r in allowed_roles]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker

def require_admin(user: dict = Depends(get_current_user)):
    if user["role"] != UserRole.SUPER_ADMIN.value:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

def generate_voucher_code() -> str:
    """Generate a unique voucher code"""
    return uuid.uuid4().hex[:8].upper()

def generate_radius_credentials(prefix: str = "") -> tuple:
    """Generate RADIUS username and password"""
    username = f"{prefix}{uuid.uuid4().hex[:6]}"
    password = uuid.uuid4().hex[:8]
    return username, password

async def calculate_dynamic_revenue(hotspot_id: str, amount: float) -> DynamicRevenue:
    """Calculate dynamic revenue sharing based on hotspot metrics"""
    hotspot = await db.hotspots.find_one({"id": hotspot_id}, {"_id": 0})
    if not hotspot:
        # Default split if hotspot not found (30% to owner)
        return DynamicRevenue(
            total_amount=amount,
            owner_share=amount * 0.3,
            platform_share=amount * 0.7,
            owner_percentage=30.0,
            breakdown={"base": 30.0},
            capped=False
        )
    
    # Get revenue config
    config = await db.settings.find_one({"type": "revenue_config"}, {"_id": 0})
    if not config:
        config = RevenueConfig().model_dump()
    else:
        config = config.get("config", RevenueConfig().model_dump())
    
    # Calculate dynamic percentage
    breakdown = {"base": config.get("base_owner_percentage", 30.0)}
    owner_percentage = config.get("base_owner_percentage", 30.0)
    
    # Coverage bonus
    coverage_area = hotspot.get("coverage_area_sqm", 100)
    coverage_bonus = (coverage_area / 100) * config.get("coverage_bonus_per_100sqm", 0.5)
    breakdown["coverage_bonus"] = min(coverage_bonus, 5.0)
    owner_percentage += breakdown["coverage_bonus"]
    
    # Client bonus
    avg_clients = hotspot.get("avg_daily_clients", 0)
    client_bonus = (avg_clients / 10) * config.get("client_bonus_per_10", 0.5)
    breakdown["client_bonus"] = min(client_bonus, 5.0)
    owner_percentage += breakdown["client_bonus"]
    
    # Ad impression bonus
    ad_impressions = hotspot.get("ad_impressions_delivered", 0)
    ad_bonus = (ad_impressions / 1000) * config.get("ad_impression_bonus_per_1000", 1.0)
    breakdown["ad_bonus"] = min(ad_bonus, 5.0)
    owner_percentage += breakdown["ad_bonus"]
    
    # Uptime bonus
    uptime = hotspot.get("uptime_percentage", 100)
    if uptime >= config.get("uptime_bonus_threshold", 99.0):
        breakdown["uptime_bonus"] = config.get("uptime_bonus_percentage", 2.0)
        owner_percentage += breakdown["uptime_bonus"]
    
    # Check if cap needs to be applied
    max_percentage = config.get("max_owner_percentage", 50.0)
    capped = owner_percentage > max_percentage
    owner_percentage = min(owner_percentage, max_percentage)
    
    owner_share = amount * (owner_percentage / 100)
    platform_share = amount - owner_share
    
    return DynamicRevenue(
        total_amount=amount,
        owner_share=round(owner_share, 2),
        platform_share=round(platform_share, 2),
        owner_percentage=round(owner_percentage, 2),
        breakdown=breakdown,
        capped=capped
    )

# ==================== M-Pesa Daraja Integration ====================

class MPesaService:
    """Real M-Pesa Daraja API Integration"""
    
    def __init__(self):
        self.consumer_key = MPESA_CONSUMER_KEY
        self.consumer_secret = MPESA_CONSUMER_SECRET
        self.shortcode = MPESA_SHORTCODE
        self.passkey = MPESA_PASSKEY
        self.callback_url = MPESA_CALLBACK_URL
        self.env = MPESA_ENV
        
        if self.env == "sandbox":
            self.base_url = "https://sandbox.safaricom.co.ke"
        else:
            self.base_url = "https://api.safaricom.co.ke"
    
    def is_configured(self) -> bool:
        """Check if M-Pesa has API credentials configured"""
        return all([
            self.consumer_key,
            self.consumer_secret,
            self.shortcode,
            self.passkey
        ])
    
    def has_callback_url(self) -> bool:
        """Check if callback URL is configured"""
        return bool(self.callback_url)
    
    async def get_access_token(self) -> str:
        """Get OAuth access token from Daraja API"""
        if not self.is_configured():
            raise HTTPException(status_code=503, detail="M-Pesa not configured")
        
        credentials = base64.b64encode(
            f"{self.consumer_key}:{self.consumer_secret}".encode()
        ).decode()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials",
                headers={"Authorization": f"Basic {credentials}"}
            )
            
            if response.status_code != 200:
                logging.error(f"M-Pesa token error: {response.text}")
                raise HTTPException(status_code=502, detail="Failed to get M-Pesa access token")
            
            return response.json()["access_token"]
    
    def generate_password(self) -> tuple:
        """Generate password and timestamp for STK Push"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password_str = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode()
        return password, timestamp
    
    async def stk_push(self, phone_number: str, amount: float, account_ref: str, description: str) -> dict:
        """Initiate STK Push request"""
        if not self.is_configured():
            return {"errorMessage": "M-Pesa not configured. Please add credentials in settings."}
        
        # Use a default callback URL for testing if not set
        callback = self.callback_url if self.callback_url else "https://example.com/callback"
        
        # Format phone number (254XXXXXXXXX)
        phone = phone_number.replace("+", "").replace(" ", "")
        if phone.startswith("0"):
            phone = "254" + phone[1:]
        elif not phone.startswith("254"):
            phone = "254" + phone
        
        try:
            access_token = await self.get_access_token()
        except Exception as e:
            logging.error(f"Failed to get M-Pesa token: {e}")
            return {"errorMessage": str(e)}
        
        password, timestamp = self.generate_password()
        
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone,
            "PartyB": self.shortcode,
            "PhoneNumber": phone,
            "CallBackURL": callback,
            "AccountReference": account_ref[:12],  # Max 12 chars
            "TransactionDesc": description[:13]  # Max 13 chars
        }
        
        logging.info(f"STK Push request - Phone: {phone}, Amount: {amount}, Ref: {account_ref}")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/mpesa/stkpush/v1/processrequest",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    }
                )
                
                result = response.json()
                logging.info(f"STK Push response: {result}")
                return result
            except Exception as e:
                logging.error(f"STK Push error: {e}")
                return {"errorMessage": str(e)}
    
    async def query_stk_status(self, checkout_request_id: str) -> dict:
        """Query the status of an STK Push request"""
        if not self.is_configured():
            raise HTTPException(status_code=503, detail="M-Pesa not configured")
        
        access_token = await self.get_access_token()
        password, timestamp = self.generate_password()
        
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mpesa/stkpushquery/v1/query",
                json=payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
            )
            
            return response.json()

mpesa_service = MPesaService()

# ==================== SMS Service ====================

class SMSService:
    """SMS Gateway Integration (Africa's Talking / Centipid compatible)"""
    
    def __init__(self):
        self.provider = SMS_PROVIDER
        self.api_key = SMS_API_KEY
        self.username = SMS_USERNAME
        self.sender_id = SMS_SENDER_ID
    
    def is_configured(self) -> bool:
        return bool(self.api_key and self.username)
    
    async def send_sms(self, phone_number: str, message: str) -> dict:
        """Send SMS via configured provider"""
        if not self.is_configured():
            logging.warning("SMS not configured, skipping notification")
            return {"status": "skipped", "reason": "SMS not configured"}
        
        # Format phone number
        phone = phone_number.replace("+", "").replace(" ", "")
        if phone.startswith("0"):
            phone = "+254" + phone[1:]
        elif not phone.startswith("+"):
            phone = "+" + phone
        
        if self.provider == "africas_talking":
            return await self._send_africas_talking(phone, message)
        elif self.provider == "centipid":
            return await self._send_centipid(phone, message)
        else:
            return {"status": "error", "reason": f"Unknown provider: {self.provider}"}
    
    async def _send_africas_talking(self, phone: str, message: str) -> dict:
        """Send via Africa's Talking API"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.africastalking.com/version1/messaging",
                data={
                    "username": self.username,
                    "to": phone,
                    "message": message,
                    "from": self.sender_id
                },
                headers={
                    "apiKey": self.api_key,
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            return response.json()
    
    async def _send_centipid(self, phone: str, message: str) -> dict:
        """Send via Centipid SMS API"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.centipid.com/v1/sms/send",
                json={
                    "api_key": self.api_key,
                    "to": phone,
                    "message": message,
                    "sender_id": self.sender_id
                }
            )
            return response.json()

sms_service = SMSService()

# ==================== WhatsApp Service (Twilio) ====================

class WhatsAppService:
    """Twilio WhatsApp Integration"""
    
    def __init__(self):
        self.account_sid = TWILIO_ACCOUNT_SID
        self.auth_token = TWILIO_AUTH_TOKEN
        self.whatsapp_number = TWILIO_WHATSAPP_NUMBER
    
    def is_configured(self) -> bool:
        return all([self.account_sid, self.auth_token, self.whatsapp_number])
    
    async def send_message(self, phone_number: str, message: str) -> dict:
        """Send WhatsApp message via Twilio"""
        if not self.is_configured():
            logging.warning("WhatsApp not configured, skipping notification")
            return {"status": "skipped", "reason": "WhatsApp not configured"}
        
        # Format phone number
        phone = phone_number.replace("+", "").replace(" ", "")
        if phone.startswith("0"):
            phone = "254" + phone[1:]
        elif not phone.startswith("254"):
            phone = "254" + phone
        
        credentials = base64.b64encode(
            f"{self.account_sid}:{self.auth_token}".encode()
        ).decode()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json",
                data={
                    "From": f"whatsapp:{self.whatsapp_number}",
                    "To": f"whatsapp:+{phone}",
                    "Body": message
                },
                headers={
                    "Authorization": f"Basic {credentials}"
                }
            )
            
            if response.status_code in [200, 201]:
                return {"status": "sent", "data": response.json()}
            else:
                return {"status": "error", "data": response.json()}

whatsapp_service = WhatsAppService()

# ==================== Notification Service ====================

class NotificationService:
    """Unified notification service"""
    
    async def send_payment_confirmation(self, phone: str, amount: float, duration: str, preferences: dict):
        """Send payment confirmation via preferred channels"""
        message = f"CAIWAVE WiFi: Payment of KES {amount} received. Your {duration} session is now active. Enjoy browsing!"
        
        if preferences.get("sms_enabled", True):
            await sms_service.send_sms(phone, message)
        
        if preferences.get("whatsapp_enabled", False):
            await whatsapp_service.send_message(phone, message)
    
    async def send_expiry_reminder(self, phone: str, minutes_left: int, preferences: dict):
        """Send expiry reminder"""
        message = f"CAIWAVE WiFi: Your session expires in {minutes_left} minutes. Purchase more time to stay connected!"
        
        if preferences.get("sms_enabled", True):
            await sms_service.send_sms(phone, message)
        
        if preferences.get("whatsapp_enabled", False):
            await whatsapp_service.send_message(phone, message)
    
    async def send_session_expired(self, phone: str, preferences: dict):
        """Send session expired notification"""
        message = "CAIWAVE WiFi: Your session has expired. Visit the captive portal to purchase more time."
        
        if preferences.get("sms_enabled", True):
            await sms_service.send_sms(phone, message)

notification_service = NotificationService()

# ==================== Auth Routes ====================

@auth_router.post("/register", response_model=dict)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(**user_data.model_dump(exclude={"password"}))
    user_dict = user.model_dump()
    user_dict["password_hash"] = hash_password(user_data.password)
    user_dict["created_at"] = user_dict["created_at"].isoformat()
    
    await db.users.insert_one(user_dict)
    token = create_token(user.id, user.role.value)
    
    return {
        "token": token,
        "user": UserResponse(**user_dict).model_dump()
    }

@auth_router.post("/login", response_model=dict)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"], user["role"])
    return {
        "token": token,
        "user": UserResponse(**user).model_dump()
    }

@auth_router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(**user)

@auth_router.post("/forgot-password")
async def forgot_password(email: EmailStr):
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a reset link will be sent"}
    
    # Generate reset token
    reset_token = str(uuid.uuid4())
    await db.password_resets.insert_one({
        "user_id": user["id"],
        "token": reset_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "used": False
    })
    
    # TODO: Send email with reset link
    return {"message": "If the email exists, a reset link will be sent"}

# ==================== Packages Routes ====================

@packages_router.get("/", response_model=List[Package])
async def get_packages(active_only: bool = True):
    query = {"is_active": True} if active_only else {}
    packages = await db.packages.find(query, {"_id": 0}).sort("price", 1).to_list(100)
    return packages

@packages_router.get("/{package_id}", response_model=Package)
async def get_package(package_id: str):
    package = await db.packages.find_one({"id": package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    return package

# Admin only - packages are predefined
@packages_router.post("/", response_model=Package)
async def create_package(
    package_data: PackageBase,
    user: dict = Depends(require_admin)
):
    package = Package(**package_data.model_dump())
    package_dict = package.model_dump()
    package_dict["created_at"] = package_dict["created_at"].isoformat()
    await db.packages.insert_one(package_dict)
    return package

@packages_router.put("/{package_id}", response_model=Package)
async def update_package(
    package_id: str,
    package_data: PackageBase,
    user: dict = Depends(require_admin)
):
    result = await db.packages.find_one_and_update(
        {"id": package_id},
        {"$set": package_data.model_dump()},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Package not found")
    result.pop("_id", None)
    return result

# ==================== Hotspots Routes ====================

@hotspots_router.get("/", response_model=List[Hotspot])
async def get_hotspots(
    user: dict = Depends(get_current_user),
    owner_id: Optional[str] = None
):
    query = {}
    if user["role"] == UserRole.HOTSPOT_OWNER.value:
        query["owner_id"] = user["id"]
    elif owner_id and user["role"] == UserRole.SUPER_ADMIN.value:
        query["owner_id"] = owner_id
    
    hotspots = await db.hotspots.find(query, {"_id": 0}).to_list(1000)
    return hotspots

@hotspots_router.get("/{hotspot_id}", response_model=Hotspot)
async def get_hotspot(hotspot_id: str, user: dict = Depends(get_current_user)):
    hotspot = await db.hotspots.find_one({"id": hotspot_id}, {"_id": 0})
    if not hotspot:
        raise HTTPException(status_code=404, detail="Hotspot not found")
    
    # Check access
    if user["role"] == UserRole.HOTSPOT_OWNER.value and hotspot["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return hotspot

@hotspots_router.post("/", response_model=Hotspot)
async def create_hotspot(
    hotspot_data: HotspotCreate,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOTSPOT_OWNER]))
):
    if user["role"] == UserRole.HOTSPOT_OWNER.value:
        hotspot_data.owner_id = user["id"]
    elif not hotspot_data.owner_id:
        hotspot_data.owner_id = user["id"]
    
    now = datetime.now(timezone.utc)
    trial_end = now + timedelta(days=TRIAL_DAYS)
    
    hotspot = Hotspot(**hotspot_data.model_dump())
    hotspot.status = HotspotStatus.ACTIVE  # Default to active for new hotspots
    hotspot.subscription_status = SubscriptionStatus.TRIAL  # Start with trial
    hotspot.trial_start_date = now
    hotspot.trial_end_date = trial_end
    
    hotspot_dict = hotspot.model_dump()
    hotspot_dict["created_at"] = hotspot_dict["created_at"].isoformat()
    hotspot_dict["trial_start_date"] = hotspot_dict["trial_start_date"].isoformat()
    hotspot_dict["trial_end_date"] = hotspot_dict["trial_end_date"].isoformat()
    if hotspot_dict.get("last_seen"):
        hotspot_dict["last_seen"] = hotspot_dict["last_seen"].isoformat()
    if hotspot_dict.get("subscription_end_date"):
        hotspot_dict["subscription_end_date"] = hotspot_dict["subscription_end_date"].isoformat()
    
    await db.hotspots.insert_one(hotspot_dict)
    
    # Create trial invoice for this hotspot
    owner_id = hotspot_data.owner_id or user["id"]
    await create_invoice_for_owner(owner_id, [hotspot.id], is_trial=True)
    
    return hotspot

@hotspots_router.put("/{hotspot_id}/packages", response_model=Hotspot)
async def update_hotspot_packages(
    hotspot_id: str,
    package_ids: List[str],
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOTSPOT_OWNER]))
):
    """Update which packages are enabled for a hotspot"""
    query = {"id": hotspot_id}
    if user["role"] == UserRole.HOTSPOT_OWNER.value:
        query["owner_id"] = user["id"]
    
    result = await db.hotspots.find_one_and_update(
        query,
        {"$set": {"enabled_packages": package_ids}},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Hotspot not found")
    result.pop("_id", None)
    return result

@hotspots_router.put("/{hotspot_id}/status")
async def update_hotspot_status(
    hotspot_id: str,
    status: HotspotStatus,
    user: dict = Depends(require_admin)
):
    """Admin only - suspend/activate hotspots"""
    result = await db.hotspots.find_one_and_update(
        {"id": hotspot_id},
        {"$set": {"status": status.value}},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Hotspot not found")
    result.pop("_id", None)
    return result

# ==================== M-Pesa Routes ====================

@mpesa_router.post("/stk-push")
async def initiate_stk_push(
    request: MPesaSTKPushRequest,
    background_tasks: BackgroundTasks
):
    """Initiate M-Pesa STK Push payment (generic)"""
    result = await mpesa_service.stk_push(
        phone_number=request.phone_number,
        amount=request.amount,
        account_ref=request.account_reference,
        description=request.transaction_desc
    )
    
    if result.get("ResponseCode") == "0":
        return {
            "success": True,
            "checkout_request_id": result.get("CheckoutRequestID"),
            "merchant_request_id": result.get("MerchantRequestID"),
            "message": "STK Push sent successfully"
        }
    else:
        return {
            "success": False,
            "error": result.get("errorMessage", "Failed to initiate payment"),
            "details": result
        }

# ==================== Role-Specific Payment Endpoints ====================

class OwnerSubscriptionPayment(BaseModel):
    """Payment request for hotspot owner subscription"""
    phone_number: str
    invoice_id: str

class AdvertiserPayment(BaseModel):
    """Payment request for advertiser ad"""
    phone_number: str
    ad_id: str

class ClientWiFiPayment(BaseModel):
    """Payment request for WiFi client"""
    phone_number: str
    package_id: str
    hotspot_id: str

@mpesa_router.post("/owner/pay-subscription")
async def owner_pay_subscription(
    payment: OwnerSubscriptionPayment,
    user: dict = Depends(require_role([UserRole.HOTSPOT_OWNER, UserRole.SUPER_ADMIN]))
):
    """
    Hotspot Owner: Pay monthly subscription via M-Pesa STK Push
    Post-payment: Activates/extends hotspot subscription
    """
    # Get invoice
    invoice = await db.invoices.find_one({"id": payment.invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Verify ownership
    if user["role"] == UserRole.HOTSPOT_OWNER.value and invoice["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if invoice["status"] == InvoiceStatus.PAID.value:
        raise HTTPException(status_code=400, detail="Invoice already paid")
    
    amount = invoice["amount"]
    account_ref = f"SUB-{invoice['invoice_number']}"
    
    # Store pending payment
    payment_record = {
        "id": str(uuid.uuid4()),
        "type": "subscription",
        "owner_id": invoice["owner_id"],
        "invoice_id": payment.invoice_id,
        "phone_number": payment.phone_number,
        "amount": amount,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.mpesa_transactions.insert_one(payment_record)
    
    # Initiate STK Push
    result = await mpesa_service.stk_push(
        phone_number=payment.phone_number,
        amount=amount,
        account_ref=account_ref,
        description="CAIWAVE Hotspot Monthly Subscription"
    )
    
    if result.get("ResponseCode") == "0":
        checkout_id = result.get("CheckoutRequestID")
        # Update transaction with checkout ID
        await db.mpesa_transactions.update_one(
            {"id": payment_record["id"]},
            {"$set": {"mpesa_checkout_id": checkout_id, "merchant_request_id": result.get("MerchantRequestID")}}
        )
        
        return {
            "success": True,
            "checkout_request_id": checkout_id,
            "merchant_request_id": result.get("MerchantRequestID"),
            "message": f"STK Push sent to {payment.phone_number}. Check your phone to complete payment.",
            "amount": amount,
            "invoice_number": invoice["invoice_number"]
        }
    else:
        await db.mpesa_transactions.update_one(
            {"id": payment_record["id"]},
            {"$set": {"status": "failed", "error": result.get("errorMessage")}}
        )
        return {
            "success": False,
            "error": result.get("errorMessage", "Failed to initiate payment"),
            "details": result
        }

@mpesa_router.post("/advertiser/pay-ad")
async def advertiser_pay_ad(
    payment: AdvertiserPayment,
    user: dict = Depends(require_role([UserRole.ADVERTISER, UserRole.SUPER_ADMIN]))
):
    """
    Advertiser: Pay for approved ad via M-Pesa STK Push
    Post-payment: Ad becomes ready for activation (goes live)
    """
    # Get ad
    ad = await db.ads.find_one({"id": payment.ad_id}, {"_id": 0})
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    
    # Verify ownership
    if user["role"] == UserRole.ADVERTISER.value and ad["advertiser_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if ad["status"] != AdStatus.APPROVED.value:
        raise HTTPException(status_code=400, detail="Ad must be approved before payment")
    
    amount = ad.get("package_price", 0)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid ad price")
    
    account_ref = f"AD-{ad['id'][:8].upper()}"
    
    # Store pending payment
    payment_record = {
        "id": str(uuid.uuid4()),
        "type": "advertising",
        "advertiser_id": ad["advertiser_id"],
        "ad_id": payment.ad_id,
        "phone_number": payment.phone_number,
        "amount": amount,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.mpesa_transactions.insert_one(payment_record)
    
    # Initiate STK Push
    result = await mpesa_service.stk_push(
        phone_number=payment.phone_number,
        amount=amount,
        account_ref=account_ref,
        description=f"CAIWAVE Ad Payment - {ad['title'][:20]}"
    )
    
    if result.get("ResponseCode") == "0":
        checkout_id = result.get("CheckoutRequestID")
        await db.mpesa_transactions.update_one(
            {"id": payment_record["id"]},
            {"$set": {"mpesa_checkout_id": checkout_id, "merchant_request_id": result.get("MerchantRequestID")}}
        )
        
        return {
            "success": True,
            "checkout_request_id": checkout_id,
            "merchant_request_id": result.get("MerchantRequestID"),
            "message": "STK Push sent. Check your phone to complete payment.",
            "amount": amount,
            "ad_title": ad["title"]
        }
    else:
        await db.mpesa_transactions.update_one(
            {"id": payment_record["id"]},
            {"$set": {"status": "failed", "error": result.get("errorMessage")}}
        )
        return {
            "success": False,
            "error": result.get("errorMessage", "Failed to initiate payment")
        }

@mpesa_router.post("/client/pay-wifi")
async def client_pay_wifi(payment: ClientWiFiPayment):
    """
    WiFi Client: Pay for WiFi package via M-Pesa STK Push (no auth required)
    Post-payment: Client gets WiFi access credentials
    """
    # Get package
    package = await db.packages.find_one({"id": payment.package_id, "is_active": True}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="Package not found or inactive")
    
    # Get hotspot
    hotspot = await db.hotspots.find_one({"id": payment.hotspot_id}, {"_id": 0})
    if not hotspot:
        raise HTTPException(status_code=404, detail="Hotspot not found")
    
    if hotspot["status"] != HotspotStatus.ACTIVE.value:
        raise HTTPException(status_code=400, detail="Hotspot is not active")
    
    amount = package["price"]
    account_ref = f"WIFI-{payment.hotspot_id[:4].upper()}-{str(uuid.uuid4())[:4].upper()}"
    
    # Store pending payment
    payment_record = {
        "id": str(uuid.uuid4()),
        "type": "wifi",
        "hotspot_id": payment.hotspot_id,
        "hotspot_owner_id": hotspot["owner_id"],
        "package_id": payment.package_id,
        "phone_number": payment.phone_number,
        "amount": amount,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.mpesa_transactions.insert_one(payment_record)
    
    # Initiate STK Push
    result = await mpesa_service.stk_push(
        phone_number=payment.phone_number,
        amount=amount,
        account_ref=account_ref,
        description=f"CAIWAVE WiFi - {package['name']}"
    )
    
    if result.get("ResponseCode") == "0":
        checkout_id = result.get("CheckoutRequestID")
        await db.mpesa_transactions.update_one(
            {"id": payment_record["id"]},
            {"$set": {"mpesa_checkout_id": checkout_id, "merchant_request_id": result.get("MerchantRequestID")}}
        )
        
        return {
            "success": True,
            "checkout_request_id": checkout_id,
            "merchant_request_id": result.get("MerchantRequestID"),
            "message": f"STK Push sent. Enter your M-Pesa PIN to pay KES {amount}.",
            "amount": amount,
            "package_name": package["name"],
            "duration": f"{package['duration_minutes']} minutes"
        }
    else:
        await db.mpesa_transactions.update_one(
            {"id": payment_record["id"]},
            {"$set": {"status": "failed", "error": result.get("errorMessage")}}
        )
        return {
            "success": False,
            "error": result.get("errorMessage", "Failed to initiate payment")
        }

# ==================== M-Pesa Callback Handler ====================

@mpesa_router.post("/callback")
async def mpesa_callback(request: Request):
    """
    Handle M-Pesa STK Push callback for all payment types
    This endpoint receives payment confirmations from Safaricom
    """
    try:
        callback_data = await request.json()
        logging.info(f"M-Pesa Callback received: {json.dumps(callback_data, indent=2)}")
    except Exception as e:
        logging.error(f"Failed to parse callback data: {e}")
        return {"ResultCode": 0, "ResultDesc": "Accepted"}
    
    body = callback_data.get("Body", {})
    stk_callback = body.get("stkCallback", {})
    
    checkout_request_id = stk_callback.get("CheckoutRequestID")
    merchant_request_id = stk_callback.get("MerchantRequestID")
    result_code = stk_callback.get("ResultCode")
    result_desc = stk_callback.get("ResultDesc")
    
    logging.info(f"Callback - CheckoutID: {checkout_request_id}, ResultCode: {result_code}, Desc: {result_desc}")
    
    # Find the transaction
    transaction = await db.mpesa_transactions.find_one(
        {"mpesa_checkout_id": checkout_request_id},
        {"_id": 0}
    )
    
    if not transaction:
        # Try to find in payments collection (legacy)
        transaction = await db.payments.find_one(
            {"mpesa_checkout_request_id": checkout_request_id},
            {"_id": 0}
        )
        if transaction:
            # Handle legacy payment
            await handle_legacy_payment_callback(transaction, stk_callback, result_code)
            return {"ResultCode": 0, "ResultDesc": "Accepted"}
        
        logging.warning(f"Transaction not found for checkout: {checkout_request_id}")
        return {"ResultCode": 0, "ResultDesc": "Accepted"}
    
    # Extract receipt number from callback metadata
    mpesa_receipt = None
    transaction_amount = None
    phone_number = None
    
    if result_code == 0:
        callback_metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])
        for item in callback_metadata:
            name = item.get("Name")
            value = item.get("Value")
            if name == "MpesaReceiptNumber":
                mpesa_receipt = value
            elif name == "Amount":
                transaction_amount = value
            elif name == "PhoneNumber":
                phone_number = value
    
    # Update transaction record
    update_data = {
        "result_code": result_code,
        "result_desc": result_desc,
        "mpesa_receipt": mpesa_receipt,
        "transaction_amount": transaction_amount,
        "callback_phone": phone_number,
        "callback_received_at": datetime.now(timezone.utc).isoformat()
    }
    
    if result_code == 0:
        update_data["status"] = "completed"
        logging.info(f"Payment SUCCESS - Type: {transaction['type']}, Receipt: {mpesa_receipt}")
        
        # Handle post-payment actions based on payment type
        payment_type = transaction.get("type")
        
        if payment_type == "subscription":
            # Hotspot Owner Subscription Payment
            await handle_subscription_payment_success(transaction, mpesa_receipt)
            
        elif payment_type == "advertising":
            # Advertiser Ad Payment
            await handle_ad_payment_success(transaction, mpesa_receipt)
            
        elif payment_type == "wifi":
            # WiFi Client Payment
            await handle_wifi_payment_success(transaction, mpesa_receipt)
    else:
        update_data["status"] = "failed"
        logging.info(f"Payment FAILED - Type: {transaction['type']}, Reason: {result_desc}")
    
    await db.mpesa_transactions.update_one(
        {"id": transaction["id"]},
        {"$set": update_data}
    )
    
    return {"ResultCode": 0, "ResultDesc": "Accepted"}

# ==================== Post-Payment Action Handlers ====================

async def handle_subscription_payment_success(transaction: dict, mpesa_receipt: str):
    """Handle successful subscription payment - activate hotspot subscription"""
    invoice_id = transaction.get("invoice_id")
    owner_id = transaction.get("owner_id")
    
    if not invoice_id:
        logging.error(f"No invoice_id in subscription transaction: {transaction['id']}")
        return
    
    now = datetime.now(timezone.utc)
    next_billing_end = now + timedelta(days=30)
    
    # Update invoice
    await db.invoices.update_one(
        {"id": invoice_id},
        {"$set": {
            "status": InvoiceStatus.PAID.value,
            "paid_at": now.isoformat(),
            "payment_method": "mpesa",
            "mpesa_receipt_number": mpesa_receipt,
            "mpesa_transaction_date": now.isoformat()
        }}
    )
    
    # Activate owner's hotspots
    await db.hotspots.update_many(
        {"owner_id": owner_id},
        {"$set": {
            "status": HotspotStatus.ACTIVE.value,
            "subscription_status": SubscriptionStatus.ACTIVE.value,
            "subscription_end_date": next_billing_end.isoformat()
        }}
    )
    
    logging.info(f"Subscription activated for owner {owner_id}, Invoice: {invoice_id}")

async def handle_ad_payment_success(transaction: dict, mpesa_receipt: str):
    """Handle successful ad payment - mark ad as paid and ready for activation"""
    ad_id = transaction.get("ad_id")
    
    if not ad_id:
        logging.error(f"No ad_id in advertising transaction: {transaction['id']}")
        return
    
    now = datetime.now(timezone.utc)
    
    # Get ad to calculate expiry
    ad = await db.ads.find_one({"id": ad_id}, {"_id": 0})
    if not ad:
        logging.error(f"Ad not found: {ad_id}")
        return
    
    # Get package for duration
    package = await db.ad_packages.find_one({"id": ad.get("package_id")})
    duration_days = package.get("duration_days", 7) if package else 7
    
    expires_at = now + timedelta(days=duration_days)
    
    # Update ad status to PAID (ready for admin to activate)
    await db.ads.update_one(
        {"id": ad_id},
        {"$set": {
            "status": AdStatus.PAID.value,
            "paid_at": now.isoformat(),
            "payment_id": transaction["id"],
            "mpesa_receipt": mpesa_receipt,
            "starts_at": now.isoformat(),
            "expires_at": expires_at.isoformat()
        }}
    )
    
    logging.info(f"Ad payment successful for ad {ad_id}, ready for activation")

async def handle_wifi_payment_success(transaction: dict, mpesa_receipt: str):
    """Handle successful WiFi payment - create session and grant access"""
    hotspot_id = transaction.get("hotspot_id")
    package_id = transaction.get("package_id")
    phone_number = transaction.get("phone_number")
    amount = transaction.get("amount", 0)
    
    if not all([hotspot_id, package_id]):
        logging.error(f"Missing data in wifi transaction: {transaction['id']}")
        return
    
    # Get package and hotspot
    package = await db.packages.find_one({"id": package_id}, {"_id": 0})
    hotspot = await db.hotspots.find_one({"id": hotspot_id}, {"_id": 0})
    
    if not package or not hotspot:
        logging.error(f"Package or hotspot not found for transaction: {transaction['id']}")
        return
    
    now = datetime.now(timezone.utc)
    
    # Calculate revenue sharing
    revenue = await calculate_dynamic_revenue(hotspot_id, amount)
    
    # Create payment record
    payment = Payment(
        hotspot_id=hotspot_id,
        package_id=package_id,
        phone_number=phone_number,
        amount=amount,
        method=PaymentMethod.MPESA,
        status=PaymentStatus.COMPLETED,
        mpesa_checkout_request_id=transaction.get("mpesa_checkout_id"),
        mpesa_receipt=mpesa_receipt,
        owner_share=revenue.owner_share,
        platform_share=revenue.platform_share
    )
    
    payment_dict = payment.model_dump()
    payment_dict["created_at"] = payment_dict["created_at"].isoformat()
    payment_dict["completed_at"] = now.isoformat()
    await db.payments.insert_one(payment_dict)
    
    # Generate WiFi credentials
    username, password = generate_radius_credentials(hotspot.get("username_prefix", ""))
    
    # Create session
    session = Session(
        package_id=package_id,
        hotspot_id=hotspot_id,
        phone_number=phone_number,
        username=username,
        password=password,
        payment_id=payment.id,
        expires_at=now + timedelta(minutes=package["duration_minutes"])
    )
    
    session_dict = session.model_dump()
    session_dict["started_at"] = session_dict["started_at"].isoformat()
    session_dict["expires_at"] = session_dict["expires_at"].isoformat()
    await db.sessions.insert_one(session_dict)
    
    # Update payment with session ID
    await db.payments.update_one(
        {"id": payment.id},
        {"$set": {"session_id": session.id}}
    )
    
    # Update hotspot stats
    await db.hotspots.update_one(
        {"id": hotspot_id},
        {"$inc": {"total_revenue": amount, "total_sessions": 1}}
    )
    
    # Store credentials in transaction for client to retrieve
    await db.mpesa_transactions.update_one(
        {"id": transaction["id"]},
        {"$set": {
            "wifi_username": username,
            "wifi_password": password,
            "session_id": session.id,
            "expires_at": session_dict["expires_at"]
        }}
    )
    
    logging.info(f"WiFi access granted - Session: {session.id}, Username: {username}")
    
    # Send SMS with credentials (if configured)
    try:
        await notification_service.send_payment_confirmation(
            phone_number,
            amount,
            f"{package['duration_minutes']} minutes",
            {"sms_enabled": True, "whatsapp_enabled": False}
        )
    except Exception as e:
        logging.warning(f"Failed to send notification: {e}")

async def handle_legacy_payment_callback(payment: dict, stk_callback: dict, result_code: int):
    """Handle callbacks for legacy payment records (backward compatibility)"""
    if result_code == 0:
        callback_metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])
        mpesa_receipt = None
        for item in callback_metadata:
            if item.get("Name") == "MpesaReceiptNumber":
                mpesa_receipt = item.get("Value")
                break
        
        revenue = await calculate_dynamic_revenue(payment["hotspot_id"], payment["amount"])
        
        await db.payments.update_one(
            {"id": payment["id"]},
            {"$set": {
                "status": PaymentStatus.COMPLETED.value,
                "mpesa_receipt": mpesa_receipt,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "owner_share": revenue.owner_share,
                "platform_share": revenue.platform_share
            }}
        )
        
        # Create session and update stats (same as wifi payment)
        package = await db.packages.find_one({"id": payment["package_id"]}, {"_id": 0})
        hotspot = await db.hotspots.find_one({"id": payment["hotspot_id"]}, {"_id": 0})
        
        if package and hotspot:
            username, password = generate_radius_credentials(hotspot.get("username_prefix", ""))
            
            session = Session(
                package_id=payment["package_id"],
                hotspot_id=payment["hotspot_id"],
                phone_number=payment["phone_number"],
                username=username,
                password=password,
                payment_id=payment["id"],
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=package["duration_minutes"])
            )
            
            session_dict = session.model_dump()
            session_dict["started_at"] = session_dict["started_at"].isoformat()
            session_dict["expires_at"] = session_dict["expires_at"].isoformat()
            await db.sessions.insert_one(session_dict)
            
            await db.payments.update_one(
                {"id": payment["id"]},
                {"$set": {"session_id": session.id}}
            )
            
            await db.hotspots.update_one(
                {"id": payment["hotspot_id"]},
                {"$inc": {"total_revenue": payment["amount"], "total_sessions": 1}}
            )
    else:
        await db.payments.update_one(
            {"id": payment["id"]},
            {"$set": {"status": PaymentStatus.FAILED.value}}
        )

# ==================== Payment Status & Transaction Queries ====================

@mpesa_router.get("/status/{checkout_request_id}")
async def check_payment_status(checkout_request_id: str):
    """Check the status of an STK Push request"""
    # First check our database
    transaction = await db.mpesa_transactions.find_one(
        {"mpesa_checkout_id": checkout_request_id},
        {"_id": 0}
    )
    
    if transaction:
        return {
            "found_in_db": True,
            "transaction": transaction
        }
    
    # Query Safaricom API
    result = await mpesa_service.query_stk_status(checkout_request_id)
    return {
        "found_in_db": False,
        "safaricom_response": result
    }

@mpesa_router.get("/transaction/{transaction_id}")
async def get_transaction(transaction_id: str):
    """Get transaction details by ID"""
    transaction = await db.mpesa_transactions.find_one(
        {"id": transaction_id},
        {"_id": 0}
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@mpesa_router.get("/wifi-credentials/{checkout_request_id}")
async def get_wifi_credentials(checkout_request_id: str):
    """Get WiFi credentials after successful payment"""
    transaction = await db.mpesa_transactions.find_one(
        {"mpesa_checkout_id": checkout_request_id, "type": "wifi"},
        {"_id": 0}
    )
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if transaction["status"] != "completed":
        return {
            "success": False,
            "status": transaction["status"],
            "message": "Payment not yet completed. Please enter your M-Pesa PIN."
        }
    
    return {
        "success": True,
        "username": transaction.get("wifi_username"),
        "password": transaction.get("wifi_password"),
        "expires_at": transaction.get("expires_at"),
        "message": "Connect to WiFi using these credentials"
    }

@mpesa_router.get("/transactions")
async def list_transactions(
    user: dict = Depends(require_admin),
    payment_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """Admin: List all M-Pesa transactions"""
    query = {}
    if payment_type:
        query["type"] = payment_type
    if status:
        query["status"] = status
    
    transactions = await db.mpesa_transactions.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    
    # Get stats
    total = await db.mpesa_transactions.count_documents({})
    completed = await db.mpesa_transactions.count_documents({"status": "completed"})
    pending = await db.mpesa_transactions.count_documents({"status": "pending"})
    failed = await db.mpesa_transactions.count_documents({"status": "failed"})
    
    return {
        "transactions": transactions,
        "stats": {
            "total": total,
            "completed": completed,
            "pending": pending,
            "failed": failed
        }
    }

@mpesa_router.get("/config-status")
async def get_mpesa_config_status(user: dict = Depends(require_admin)):
    """Check if M-Pesa is configured (Legacy - use Paystack)"""
    return {
        "configured": mpesa_service.is_configured(),
        "has_callback": mpesa_service.has_callback_url(),
        "environment": MPESA_ENV,
        "shortcode": MPESA_SHORTCODE if MPESA_SHORTCODE else None,
        "callback_url": MPESA_CALLBACK_URL if MPESA_CALLBACK_URL else "Not configured - Using default for testing",
        "consumer_key_set": bool(MPESA_CONSUMER_KEY),
        "consumer_secret_set": bool(MPESA_CONSUMER_SECRET),
        "passkey_set": bool(MPESA_PASSKEY),
        "deprecation_notice": "M-Pesa Daraja is deprecated. Use Paystack /api/payments/* endpoints instead."
    }

# ==================== Paystack Payment Routes ====================

from services.paystack import (
    PaystackService, PaystackConfig, 
    TransactionInitRequest, MobileMoneyChargeRequest, SubaccountCreateRequest,
    KENYA_BANKS
)

# Initialize Paystack service
paystack_config = PaystackConfig(
    secret_key=PAYSTACK_SECRET_KEY,
    public_key=PAYSTACK_PUBLIC_KEY,
    environment=PAYSTACK_ENVIRONMENT
)
paystack_service = PaystackService(paystack_config)


class PaystackPaymentRequest(BaseModel):
    """Request to initiate payment via Paystack"""
    email: str
    phone_number: str  # Format: 0724825975 or 254724825975
    amount: float
    payment_type: str  # 'subscription', 'advertising', 'wifi'
    reference_id: Optional[str] = None  # invoice_id, ad_id, or hotspot_id
    description: Optional[str] = None
    subaccount_code: Optional[str] = None


class PaystackSubaccountRequest(BaseModel):
    """Request to create subaccount for hotspot owner"""
    business_name: str
    bank_code: str
    account_number: str
    percentage_charge: float = 80.0  # Owner gets 80%, platform gets 20%
    email: Optional[str] = None
    phone: Optional[str] = None


@paystack_router.get("/config")
async def get_paystack_config():
    """Get Paystack public configuration for frontend"""
    return {
        "public_key": PAYSTACK_PUBLIC_KEY,
        "environment": PAYSTACK_ENVIRONMENT,
        "configured": paystack_service.is_configured(),
        "currency": "KES",
        "channels": ["mobile_money", "card", "bank"]
    }


@paystack_router.get("/banks")
async def list_kenya_banks():
    """List available Kenya banks for subaccount creation"""
    # Try to fetch from Paystack API first
    result = await paystack_service.list_banks("kenya")
    if result.get("status") and result.get("data"):
        return result["data"]
    # Fallback to static list
    return KENYA_BANKS


@paystack_router.post("/initialize")
async def initialize_paystack_payment(request: PaystackPaymentRequest):
    """
    Initialize a Paystack payment transaction.
    Returns authorization URL for customer to complete payment.
    """
    if not paystack_service.is_configured():
        raise HTTPException(status_code=503, detail="Paystack not configured")
    
    # Format phone number
    phone = request.phone_number.replace(" ", "").replace("+", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    elif not phone.startswith("254"):
        phone = "254" + phone
    
    # Generate reference
    reference = f"CAIWAVE-{request.payment_type.upper()}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"
    
    # Create transaction record
    transaction_id = str(uuid.uuid4())
    transaction_record = {
        "id": transaction_id,
        "reference": reference,
        "email": request.email,
        "phone_number": phone,
        "amount": request.amount,
        "currency": "KES",
        "payment_type": request.payment_type,
        "reference_id": request.reference_id,
        "description": request.description or f"CAIWAVE {request.payment_type} payment",
        "subaccount_code": request.subaccount_code,
        "status": "pending",
        "provider": "paystack",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.paystack_transactions.insert_one(transaction_record)
    
    # Initialize with Paystack
    init_request = TransactionInitRequest(
        email=request.email,
        amount=request.amount,
        reference=reference,
        metadata={
            "transaction_id": transaction_id,
            "payment_type": request.payment_type,
            "reference_id": request.reference_id,
            "phone_number": phone
        },
        subaccount_code=request.subaccount_code
    )
    
    result = await paystack_service.initialize_transaction(init_request)
    
    if not result.get("status"):
        await db.paystack_transactions.update_one(
            {"id": transaction_id},
            {"$set": {"status": "failed", "error": result.get("message")}}
        )
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to initialize payment"))
    
    # Update with authorization URL
    await db.paystack_transactions.update_one(
        {"id": transaction_id},
        {"$set": {
            "authorization_url": result["data"]["authorization_url"],
            "access_code": result["data"]["access_code"]
        }}
    )
    
    return {
        "success": True,
        "transaction_id": transaction_id,
        "reference": reference,
        "authorization_url": result["data"]["authorization_url"],
        "access_code": result["data"]["access_code"],
        "message": "Redirect customer to authorization_url to complete payment"
    }


@paystack_router.post("/charge-mobile")
async def charge_mobile_money(request: PaystackPaymentRequest):
    """
    Directly charge customer via M-Pesa mobile money.
    This sends an STK Push to the customer's phone.
    """
    if not paystack_service.is_configured():
        raise HTTPException(status_code=503, detail="Paystack not configured")
    
    # Format phone number
    phone = request.phone_number.replace(" ", "").replace("+", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    elif not phone.startswith("254"):
        phone = "254" + phone
    
    # Generate reference
    reference = f"CAIWAVE-{request.payment_type.upper()}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"
    
    # Create transaction record
    transaction_id = str(uuid.uuid4())
    transaction_record = {
        "id": transaction_id,
        "reference": reference,
        "email": request.email,
        "phone_number": phone,
        "amount": request.amount,
        "currency": "KES",
        "payment_type": request.payment_type,
        "reference_id": request.reference_id,
        "description": request.description or f"CAIWAVE {request.payment_type} payment",
        "subaccount_code": request.subaccount_code,
        "status": "pending",
        "provider": "paystack",
        "payment_method": "mobile_money",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.paystack_transactions.insert_one(transaction_record)
    
    # Charge via mobile money
    charge_request = MobileMoneyChargeRequest(
        email=request.email,
        amount=request.amount,
        phone_number=phone,
        provider="mpesa",
        reference=reference,
        metadata={
            "transaction_id": transaction_id,
            "payment_type": request.payment_type,
            "reference_id": request.reference_id
        }
    )
    
    result = await paystack_service.charge_mobile_money(charge_request)
    
    if not result.get("status"):
        await db.paystack_transactions.update_one(
            {"id": transaction_id},
            {"$set": {"status": "failed", "error": result.get("message")}}
        )
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to initiate M-Pesa payment"))
    
    return {
        "success": True,
        "transaction_id": transaction_id,
        "reference": reference,
        "message": "M-Pesa payment request sent. Check your phone for the payment prompt.",
        "data": result.get("data", {})
    }


@paystack_router.post("/owner/pay-subscription")
async def owner_pay_subscription_paystack(
    phone_number: str = Body(...),
    invoice_id: Optional[str] = Body(None),
    user: dict = Depends(require_role([UserRole.HOTSPOT_OWNER]))
):
    """
    Hotspot Owner: Pay monthly subscription via Paystack M-Pesa
    """
    if not paystack_service.is_configured():
        raise HTTPException(status_code=503, detail="Paystack not configured")
    
    # Get owner's details
    owner = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")
    
    # Get or create pending invoice
    if invoice_id:
        invoice = await db.invoices.find_one({"id": invoice_id, "owner_id": user["id"]}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
    else:
        # Find unpaid invoice or create new one
        invoice = await db.invoices.find_one({
            "owner_id": user["id"],
            "status": InvoiceStatus.PENDING.value
        }, {"_id": 0})
        
        if not invoice:
            # Create new subscription invoice
            invoice_id = str(uuid.uuid4())
            invoice = {
                "id": invoice_id,
                "owner_id": user["id"],
                "type": "subscription",
                "amount": 500.0,  # KES 500 monthly subscription
                "currency": "KES",
                "status": InvoiceStatus.PENDING.value,
                "due_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.invoices.insert_one(invoice)
    
    amount = invoice.get("amount", 500.0)
    
    # Format phone
    phone = phone_number.replace(" ", "").replace("+", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    elif not phone.startswith("254"):
        phone = "254" + phone
    
    # Generate reference
    reference = f"CAIWAVE-SUB-{user['id'][:8]}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    
    # Create transaction record
    transaction_id = str(uuid.uuid4())
    transaction_record = {
        "id": transaction_id,
        "reference": reference,
        "email": owner.get("email", f"{phone}@caiwave.com"),
        "phone_number": phone,
        "amount": amount,
        "currency": "KES",
        "payment_type": "subscription",
        "invoice_id": invoice["id"],
        "owner_id": user["id"],
        "status": "pending",
        "provider": "paystack",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.paystack_transactions.insert_one(transaction_record)
    
    # Initialize payment
    init_request = TransactionInitRequest(
        email=owner.get("email", f"{phone}@caiwave.com"),
        amount=amount,
        reference=reference,
        metadata={
            "transaction_id": transaction_id,
            "payment_type": "subscription",
            "invoice_id": invoice["id"],
            "owner_id": user["id"]
        }
    )
    
    result = await paystack_service.initialize_transaction(init_request)
    
    if not result.get("status"):
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to initialize payment"))
    
    await db.paystack_transactions.update_one(
        {"id": transaction_id},
        {"$set": {
            "authorization_url": result["data"]["authorization_url"],
            "access_code": result["data"]["access_code"]
        }}
    )
    
    return {
        "success": True,
        "transaction_id": transaction_id,
        "reference": reference,
        "amount": amount,
        "authorization_url": result["data"]["authorization_url"],
        "message": f"Complete payment of KES {amount} for your monthly subscription"
    }


@paystack_router.post("/advertiser/pay-ad")
async def advertiser_pay_ad_paystack(
    ad_id: str = Body(...),
    phone_number: str = Body(...),
    user: dict = Depends(require_role([UserRole.ADVERTISER]))
):
    """
    Advertiser: Pay for approved ad via Paystack
    """
    if not paystack_service.is_configured():
        raise HTTPException(status_code=503, detail="Paystack not configured")
    
    # Get the ad
    ad = await db.ads.find_one({"id": ad_id, "advertiser_id": user["id"]}, {"_id": 0})
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found or access denied")
    
    if ad["status"] != AdStatus.APPROVED.value:
        raise HTTPException(status_code=400, detail="Ad must be approved before payment")
    
    # Get package for pricing
    package = await db.ad_packages.find_one({"id": ad.get("package_id")}, {"_id": 0})
    amount = package["price"] if package else ad.get("total_cost", 1000)
    
    # Format phone
    phone = phone_number.replace(" ", "").replace("+", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    
    # Generate reference
    reference = f"CAIWAVE-AD-{ad_id[:8]}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    
    # Create transaction
    transaction_id = str(uuid.uuid4())
    transaction_record = {
        "id": transaction_id,
        "reference": reference,
        "email": user.get("email", f"{phone}@caiwave.com"),
        "phone_number": phone,
        "amount": amount,
        "currency": "KES",
        "payment_type": "advertising",
        "ad_id": ad_id,
        "advertiser_id": user["id"],
        "status": "pending",
        "provider": "paystack",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.paystack_transactions.insert_one(transaction_record)
    
    # Initialize payment
    init_request = TransactionInitRequest(
        email=user.get("email", f"{phone}@caiwave.com"),
        amount=amount,
        reference=reference,
        metadata={
            "transaction_id": transaction_id,
            "payment_type": "advertising",
            "ad_id": ad_id,
            "advertiser_id": user["id"]
        }
    )
    
    result = await paystack_service.initialize_transaction(init_request)
    
    if not result.get("status"):
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to initialize payment"))
    
    await db.paystack_transactions.update_one(
        {"id": transaction_id},
        {"$set": {
            "authorization_url": result["data"]["authorization_url"],
            "access_code": result["data"]["access_code"]
        }}
    )
    
    return {
        "success": True,
        "transaction_id": transaction_id,
        "reference": reference,
        "amount": amount,
        "authorization_url": result["data"]["authorization_url"],
        "message": f"Complete payment of KES {amount} for your ad: {ad['title']}"
    }


@paystack_router.post("/client/pay-wifi")
async def client_pay_wifi_paystack(
    hotspot_id: str = Body(...),
    package_id: str = Body(...),
    phone_number: str = Body(...),
    email: str = Body("guest@caiwave.com")
):
    """
    WiFi Client: Pay for WiFi package via Paystack M-Pesa (no auth required)
    """
    if not paystack_service.is_configured():
        raise HTTPException(status_code=503, detail="Paystack not configured")
    
    # Validate hotspot and package
    hotspot = await db.hotspots.find_one({"id": hotspot_id}, {"_id": 0})
    if not hotspot:
        raise HTTPException(status_code=404, detail="Hotspot not found")
    
    package = await db.packages.find_one({"id": package_id, "is_active": True}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="Package not found or inactive")
    
    amount = package["price"]
    
    # Format phone
    phone = phone_number.replace(" ", "").replace("+", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    
    # Get hotspot owner's subaccount for revenue split
    owner = await db.users.find_one({"id": hotspot.get("owner_id")}, {"_id": 0})
    subaccount_code = owner.get("paystack_subaccount_code") if owner else None
    
    # Generate reference
    reference = f"CAIWAVE-WIFI-{hotspot_id[:8]}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    
    # Create transaction
    transaction_id = str(uuid.uuid4())
    transaction_record = {
        "id": transaction_id,
        "reference": reference,
        "email": email,
        "phone_number": phone,
        "amount": amount,
        "currency": "KES",
        "payment_type": "wifi",
        "hotspot_id": hotspot_id,
        "package_id": package_id,
        "subaccount_code": subaccount_code,
        "status": "pending",
        "provider": "paystack",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.paystack_transactions.insert_one(transaction_record)
    
    # Initialize payment with subaccount for revenue split
    init_request = TransactionInitRequest(
        email=email,
        amount=amount,
        reference=reference,
        metadata={
            "transaction_id": transaction_id,
            "payment_type": "wifi",
            "hotspot_id": hotspot_id,
            "package_id": package_id,
            "phone_number": phone
        },
        subaccount_code=subaccount_code
    )
    
    result = await paystack_service.initialize_transaction(init_request)
    
    if not result.get("status"):
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to initialize payment"))
    
    await db.paystack_transactions.update_one(
        {"id": transaction_id},
        {"$set": {
            "authorization_url": result["data"]["authorization_url"],
            "access_code": result["data"]["access_code"]
        }}
    )
    
    return {
        "success": True,
        "transaction_id": transaction_id,
        "reference": reference,
        "amount": amount,
        "package_name": package["name"],
        "duration": package["duration_minutes"],
        "authorization_url": result["data"]["authorization_url"],
        "message": f"Pay KES {amount} for {package['name']} ({package['duration_minutes']} minutes)"
    }


@paystack_router.post("/verify/{reference}")
async def verify_paystack_payment(reference: str):
    """
    Verify a Paystack payment and process if successful
    """
    if not paystack_service.is_configured():
        raise HTTPException(status_code=503, detail="Paystack not configured")
    
    # Get our transaction record
    transaction = await db.paystack_transactions.find_one({"reference": reference}, {"_id": 0})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Verify with Paystack
    result = await paystack_service.verify_transaction(reference)
    
    if not result.get("status"):
        raise HTTPException(status_code=400, detail=result.get("message", "Verification failed"))
    
    paystack_data = result.get("data", {})
    payment_status = paystack_data.get("status")
    
    if payment_status == "success":
        # Update transaction
        await db.paystack_transactions.update_one(
            {"reference": reference},
            {"$set": {
                "status": "completed",
                "paystack_reference": paystack_data.get("reference"),
                "paystack_transaction_id": paystack_data.get("id"),
                "paid_at": paystack_data.get("paid_at"),
                "channel": paystack_data.get("channel"),
                "completed_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Process based on payment type
        payment_type = transaction.get("payment_type")
        
        if payment_type == "subscription":
            await handle_paystack_subscription_success(transaction, paystack_data)
        elif payment_type == "advertising":
            await handle_paystack_ad_success(transaction, paystack_data)
        elif payment_type == "wifi":
            wifi_creds = await handle_paystack_wifi_success(transaction, paystack_data)
            return {
                "success": True,
                "status": "completed",
                "payment_type": payment_type,
                "wifi_credentials": wifi_creds,
                "message": "Payment successful! Use these credentials to connect to WiFi."
            }
        
        return {
            "success": True,
            "status": "completed",
            "payment_type": payment_type,
            "message": "Payment verified and processed successfully"
        }
    
    elif payment_status == "pending":
        return {
            "success": False,
            "status": "pending",
            "message": "Payment is still pending. Please complete the payment."
        }
    
    else:
        await db.paystack_transactions.update_one(
            {"reference": reference},
            {"$set": {"status": "failed", "failure_reason": paystack_data.get("gateway_response")}}
        )
        return {
            "success": False,
            "status": "failed",
            "message": paystack_data.get("gateway_response", "Payment failed")
        }


@paystack_router.post("/webhook")
async def paystack_webhook(request: Request):
    """
    Handle Paystack webhook events
    """
    # Get raw body for signature verification
    raw_body = await request.body()
    signature = request.headers.get("x-paystack-signature", "")
    
    # Verify signature if webhook secret is configured
    if PAYSTACK_WEBHOOK_SECRET:
        if not paystack_service.verify_webhook_signature(raw_body, signature):
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        payload = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    event = payload.get("event")
    data = payload.get("data", {})
    
    logging.info(f"Paystack webhook received: {event}")
    
    if event == "charge.success":
        reference = data.get("reference")
        
        # Find our transaction
        transaction = await db.paystack_transactions.find_one({"reference": reference}, {"_id": 0})
        
        if transaction and transaction["status"] != "completed":
            # Update status
            await db.paystack_transactions.update_one(
                {"reference": reference},
                {"$set": {
                    "status": "completed",
                    "paystack_transaction_id": data.get("id"),
                    "paid_at": data.get("paid_at"),
                    "channel": data.get("channel"),
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Process based on type
            payment_type = transaction.get("payment_type")
            if payment_type == "subscription":
                await handle_paystack_subscription_success(transaction, data)
            elif payment_type == "advertising":
                await handle_paystack_ad_success(transaction, data)
            elif payment_type == "wifi":
                await handle_paystack_wifi_success(transaction, data)
    
    return {"status": "ok"}


@paystack_router.post("/subaccount/create")
async def create_paystack_subaccount(
    request: PaystackSubaccountRequest,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOTSPOT_OWNER]))
):
    """
    Create a Paystack subaccount for a hotspot owner
    This enables automatic revenue splitting on WiFi payments
    """
    if not paystack_service.is_configured():
        raise HTTPException(status_code=503, detail="Paystack not configured")
    
    subaccount_request = SubaccountCreateRequest(
        business_name=request.business_name,
        settlement_bank=request.bank_code,
        account_number=request.account_number,
        percentage_charge=request.percentage_charge,
        primary_contact_email=request.email,
        primary_contact_phone=request.phone
    )
    
    result = await paystack_service.create_subaccount(subaccount_request)
    
    if not result.get("status"):
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to create subaccount"))
    
    subaccount_code = result["data"]["subaccount_code"]
    
    # Store subaccount code with the user
    if user["role"] == UserRole.HOTSPOT_OWNER.value:
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {
                "paystack_subaccount_code": subaccount_code,
                "paystack_business_name": request.business_name,
                "paystack_bank_code": request.bank_code,
                "paystack_account_number": request.account_number[-4:]  # Store only last 4 digits
            }}
        )
    
    return {
        "success": True,
        "subaccount_code": subaccount_code,
        "message": "Subaccount created successfully. WiFi payments will now be split automatically."
    }


@paystack_router.get("/transactions")
async def list_paystack_transactions(
    user: dict = Depends(require_admin),
    payment_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """Admin: List all Paystack transactions"""
    query = {}
    if payment_type:
        query["payment_type"] = payment_type
    if status:
        query["status"] = status
    
    transactions = await db.paystack_transactions.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    
    # Stats
    total = await db.paystack_transactions.count_documents({})
    completed = await db.paystack_transactions.count_documents({"status": "completed"})
    pending = await db.paystack_transactions.count_documents({"status": "pending"})
    failed = await db.paystack_transactions.count_documents({"status": "failed"})
    
    return {
        "transactions": transactions,
        "stats": {
            "total": total,
            "completed": completed,
            "pending": pending,
            "failed": failed
        }
    }


# Paystack Payment Success Handlers

async def handle_paystack_subscription_success(transaction: dict, paystack_data: dict):
    """Handle successful subscription payment via Paystack"""
    invoice_id = transaction.get("invoice_id")
    owner_id = transaction.get("owner_id")
    
    if not invoice_id:
        logging.error(f"No invoice_id in subscription transaction: {transaction['id']}")
        return
    
    now = datetime.now(timezone.utc)
    next_billing_end = now + timedelta(days=30)
    
    # Update invoice
    await db.invoices.update_one(
        {"id": invoice_id},
        {"$set": {
            "status": InvoiceStatus.PAID.value,
            "paid_at": now.isoformat(),
            "payment_method": "paystack",
            "paystack_reference": paystack_data.get("reference"),
            "paystack_transaction_id": paystack_data.get("id")
        }}
    )
    
    # Activate owner's hotspots
    await db.hotspots.update_many(
        {"owner_id": owner_id},
        {"$set": {
            "status": HotspotStatus.ACTIVE.value,
            "subscription_status": SubscriptionStatus.ACTIVE.value,
            "subscription_end_date": next_billing_end.isoformat()
        }}
    )
    
    logging.info(f"Subscription activated for owner {owner_id}, Invoice: {invoice_id}")


async def handle_paystack_ad_success(transaction: dict, paystack_data: dict):
    """Handle successful ad payment via Paystack"""
    ad_id = transaction.get("ad_id")
    
    if not ad_id:
        logging.error(f"No ad_id in advertising transaction: {transaction['id']}")
        return
    
    now = datetime.now(timezone.utc)
    
    # Get ad and package
    ad = await db.ads.find_one({"id": ad_id}, {"_id": 0})
    if not ad:
        logging.error(f"Ad not found: {ad_id}")
        return
    
    package = await db.ad_packages.find_one({"id": ad.get("package_id")})
    duration_days = package["duration_days"] if package else 30
    expires_at = now + timedelta(days=duration_days)
    
    # Update ad
    await db.ads.update_one(
        {"id": ad_id},
        {"$set": {
            "status": AdStatus.ACTIVE.value,
            "starts_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "payment_status": "paid",
            "payment_method": "paystack",
            "paystack_reference": paystack_data.get("reference")
        }}
    )
    
    logging.info(f"Ad activated: {ad_id}, expires: {expires_at}")


async def handle_paystack_wifi_success(transaction: dict, paystack_data: dict):
    """Handle successful WiFi payment via Paystack"""
    hotspot_id = transaction.get("hotspot_id")
    package_id = transaction.get("package_id")
    phone_number = transaction.get("phone_number")
    amount = transaction.get("amount")
    
    if not all([hotspot_id, package_id]):
        logging.error(f"Missing data in WiFi transaction: {transaction['id']}")
        return None
    
    # Get hotspot and package
    hotspot = await db.hotspots.find_one({"id": hotspot_id}, {"_id": 0})
    package = await db.packages.find_one({"id": package_id}, {"_id": 0})
    
    if not hotspot or not package:
        logging.error(f"Hotspot or package not found for WiFi payment")
        return None
    
    now = datetime.now(timezone.utc)
    
    # Calculate revenue sharing
    revenue = await calculate_dynamic_revenue(hotspot_id, amount)
    
    # Create payment record
    payment = Payment(
        hotspot_id=hotspot_id,
        package_id=package_id,
        phone_number=phone_number,
        amount=amount,
        method=PaymentMethod.PAYSTACK,
        status=PaymentStatus.COMPLETED,
        owner_share=revenue.owner_share,
        platform_share=revenue.platform_share
    )
    
    payment_dict = payment.model_dump()
    payment_dict["created_at"] = payment_dict["created_at"].isoformat()
    payment_dict["completed_at"] = now.isoformat()
    payment_dict["paystack_reference"] = paystack_data.get("reference")
    await db.payments.insert_one(payment_dict)
    
    # Generate WiFi credentials
    username, password = generate_radius_credentials(hotspot.get("username_prefix", ""))
    
    # Create session
    session = Session(
        package_id=package_id,
        hotspot_id=hotspot_id,
        phone_number=phone_number,
        username=username,
        password=password,
        payment_id=payment.id,
        expires_at=now + timedelta(minutes=package["duration_minutes"])
    )
    
    session_dict = session.model_dump()
    session_dict["started_at"] = session_dict["started_at"].isoformat()
    session_dict["expires_at"] = session_dict["expires_at"].isoformat()
    await db.sessions.insert_one(session_dict)
    
    # Update payment with session ID
    await db.payments.update_one(
        {"id": payment.id},
        {"$set": {"session_id": session.id}}
    )
    
    # Update hotspot stats
    await db.hotspots.update_one(
        {"id": hotspot_id},
        {"$inc": {"total_revenue": amount, "total_sessions": 1}}
    )
    
    # Store credentials in transaction
    await db.paystack_transactions.update_one(
        {"id": transaction["id"]},
        {"$set": {
            "wifi_username": username,
            "wifi_password": password,
            "session_id": session.id,
            "expires_at": session_dict["expires_at"]
        }}
    )
    
    logging.info(f"WiFi access granted - Session: {session.id}, Username: {username}")
    
    return {
        "username": username,
        "password": password,
        "expires_at": session_dict["expires_at"],
        "duration_minutes": package["duration_minutes"]
    }

# ==================== Payments Routes ====================

@payments_router.post("/initiate", response_model=dict)
async def initiate_payment(payment_data: PaymentCreate):
    """Initiate a payment"""
    package = await db.packages.find_one({"id": payment_data.package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    hotspot = await db.hotspots.find_one({"id": payment_data.hotspot_id}, {"_id": 0})
    if not hotspot:
        raise HTTPException(status_code=404, detail="Hotspot not found")
    
    if hotspot.get("status") not in [HotspotStatus.ACTIVE.value, None, "pending_setup"]:
        raise HTTPException(status_code=400, detail="Hotspot is not active")
    
    # Create payment record
    payment = Payment(**payment_data.model_dump())
    payment.amount = package["price"]
    payment_dict = payment.model_dump()
    payment_dict["created_at"] = payment_dict["created_at"].isoformat()
    
    if payment_data.method == PaymentMethod.MPESA:
        # Initiate STK Push
        if not mpesa_service.is_configured():
            raise HTTPException(
                status_code=503,
                detail="M-Pesa is not configured. Please contact admin."
            )
        
        stk_result = await mpesa_service.stk_push(
            phone_number=payment_data.phone_number,
            amount=package["price"],
            account_ref=f"CAIWAVE-{payment.id[:8]}",
            description=f"WiFi {package['name']}"
        )
        
        if stk_result.get("ResponseCode") == "0":
            payment_dict["mpesa_checkout_request_id"] = stk_result.get("CheckoutRequestID")
            payment_dict["status"] = PaymentStatus.PROCESSING.value
        else:
            payment_dict["status"] = PaymentStatus.FAILED.value
            await db.payments.insert_one(payment_dict)
            raise HTTPException(
                status_code=400,
                detail=stk_result.get("errorMessage", "Failed to initiate M-Pesa payment")
            )
    
    await db.payments.insert_one(payment_dict)
    
    return {
        "payment_id": payment.id,
        "status": payment_dict["status"],
        "checkout_request_id": payment_dict.get("mpesa_checkout_request_id"),
        "message": "Payment initiated. Check your phone for M-Pesa prompt."
    }

@payments_router.get("/{payment_id}")
async def get_payment(payment_id: str):
    """Get payment details"""
    payment = await db.payments.find_one({"id": payment_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

@payments_router.get("/")
async def get_payments(
    user: dict = Depends(get_current_user),
    hotspot_id: Optional[str] = None,
    status: Optional[PaymentStatus] = None,
    limit: int = 100
):
    """Get payments list"""
    query = {}
    
    if user["role"] == UserRole.HOTSPOT_OWNER.value:
        hotspots = await db.hotspots.find({"owner_id": user["id"]}, {"id": 1}).to_list(100)
        hotspot_ids = [h["id"] for h in hotspots]
        query["hotspot_id"] = {"$in": hotspot_ids}
    elif hotspot_id:
        query["hotspot_id"] = hotspot_id
    
    if status:
        query["status"] = status.value
    
    payments = await db.payments.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return payments

# ==================== Kenya Locations Data ====================

# Kenya Counties and their Constituencies (sample - can be expanded)
KENYA_LOCATIONS = {
    "Nairobi": [
        "Westlands", "Dagoretti North", "Dagoretti South", "Langata", 
        "Kibra", "Roysambu", "Kasarani", "Ruaraka", "Embakasi South",
        "Embakasi North", "Embakasi Central", "Embakasi East", "Embakasi West",
        "Makadara", "Kamukunji", "Starehe", "Mathare"
    ],
    "Mombasa": [
        "Changamwe", "Jomvu", "Kisauni", "Nyali", "Likoni", "Mvita"
    ],
    "Kisumu": [
        "Kisumu East", "Kisumu West", "Kisumu Central", "Seme", "Nyando", 
        "Muhoroni", "Nyakach"
    ],
    "Nakuru": [
        "Nakuru Town East", "Nakuru Town West", "Naivasha", "Gilgil", 
        "Subukia", "Rongai", "Bahati", "Molo", "Kuresoi South", "Kuresoi North", "Njoro"
    ],
    "Kiambu": [
        "Gatundu South", "Gatundu North", "Juja", "Thika Town", "Ruiru",
        "Githunguri", "Kiambu", "Kiambaa", "Kabete", "Kikuyu", "Limuru", "Lari"
    ],
    "Machakos": [
        "Masinga", "Yatta", "Kangundo", "Matungulu", "Kathiani", "Mavoko",
        "Machakos Town", "Mwala"
    ],
    "Kajiado": [
        "Kajiado North", "Kajiado Central", "Kajiado East", "Kajiado West", "Kajiado South"
    ],
    "Uasin Gishu": [
        "Soy", "Turbo", "Moiben", "Ainabkoi", "Kapseret", "Kesses"
    ],
    "Trans Nzoia": [
        "Kwanza", "Endebess", "Saboti", "Kiminini", "Cherangany"
    ],
    "Kakamega": [
        "Lugari", "Likuyani", "Malava", "Lurambi", "Navakholo", "Mumias West",
        "Mumias East", "Matungu", "Butere", "Khwisero", "Shinyalu", "Ikolomani"
    ],
    "Bungoma": [
        "Mount Elgon", "Sirisia", "Kabuchai", "Bumula", "Kanduyi", 
        "Webuye East", "Webuye West", "Kimilili", "Tongaren"
    ],
    "Nyeri": [
        "Tetu", "Kieni", "Mathira", "Othaya", "Mukurweini", "Nyeri Town"
    ],
    "Meru": [
        "North Imenti", "South Imenti", "Central Imenti", "Tigania West",
        "Tigania East", "Igembe South", "Igembe Central", "Igembe North", "Buuri"
    ],
    "Kilifi": [
        "Kilifi North", "Kilifi South", "Kaloleni", "Rabai", "Ganze", "Malindi", "Magarini"
    ],
    "Kwale": [
        "Msambweni", "Lunga Lunga", "Matuga", "Kinango"
    ],
    "Turkana": [
        "Turkana North", "Turkana West", "Turkana Central", "Loima", 
        "Turkana South", "Turkana East"
    ],
    "Garissa": [
        "Garissa Township", "Balambala", "Lagdera", "Dadaab", "Fafi", "Ijara"
    ],
    "Wajir": [
        "Wajir North", "Wajir East", "Tarbaj", "Wajir West", "Eldas", "Wajir South"
    ],
    "Mandera": [
        "Mandera West", "Banissa", "Mandera North", "Mandera South", "Mandera East", "Lafey"
    ]
}

# Get all counties
def get_all_counties() -> List[str]:
    return list(KENYA_LOCATIONS.keys())

# Get constituencies for a county
def get_constituencies(county: str) -> List[str]:
    return KENYA_LOCATIONS.get(county, [])

# Get all constituencies
def get_all_constituencies() -> List[dict]:
    result = []
    for county, constituencies in KENYA_LOCATIONS.items():
        for const in constituencies:
            result.append({"county": county, "constituency": const})
    return result

# ==================== Location Routes ====================

@locations_router.get("/counties")
async def list_counties():
    """Get all Kenya counties"""
    return {"counties": get_all_counties()}

@locations_router.get("/constituencies")
async def list_constituencies(county: Optional[str] = None):
    """Get constituencies, optionally filtered by county"""
    if county:
        return {"constituencies": get_constituencies(county)}
    return {"constituencies": get_all_constituencies()}

# ==================== Ad Packages Routes (Admin Only) ====================

@ad_packages_router.get("/")
async def get_ad_packages(include_disabled: bool = False):
    """Get all ad packages - public endpoint for advertisers to see pricing"""
    query = {} if include_disabled else {"status": AdPackageStatus.ACTIVE.value}
    packages = await db.ad_packages.find(query, {"_id": 0}).sort("price", 1).to_list(100)
    return packages

@ad_packages_router.get("/{package_id}")
async def get_ad_package(package_id: str):
    """Get a specific ad package"""
    pkg = await db.ad_packages.find_one({"id": package_id}, {"_id": 0})
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    return pkg

@ad_packages_router.post("/")
async def create_ad_package(
    package: AdPackageCreate,
    user: dict = Depends(require_admin)
):
    """Create a new ad package (Admin only)"""
    new_package = AdPackage(
        name=package.name,
        description=package.description,
        coverage_scope=package.coverage_scope,
        duration_days=package.duration_days,
        price=package.price,
        max_impressions=package.max_impressions
    )
    
    pkg_dict = new_package.model_dump()
    pkg_dict["created_at"] = pkg_dict["created_at"].isoformat()
    
    await db.ad_packages.insert_one(pkg_dict)
    
    return {"success": True, "package": pkg_dict}

@ad_packages_router.put("/{package_id}")
async def update_ad_package(
    package_id: str,
    update: AdPackageUpdate,
    user: dict = Depends(require_admin)
):
    """Update an ad package (Admin only)"""
    existing = await db.ad_packages.find_one({"id": package_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Package not found")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.ad_packages.update_one({"id": package_id}, {"$set": update_data})
    
    updated = await db.ad_packages.find_one({"id": package_id}, {"_id": 0})
    return {"success": True, "package": updated}

@ad_packages_router.delete("/{package_id}")
async def delete_ad_package(
    package_id: str,
    user: dict = Depends(require_admin)
):
    """Delete an ad package (Admin only) - only if not used by any ads"""
    # Check if any ads use this package
    ad_count = await db.ads.count_documents({"package_id": package_id})
    if ad_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete - {ad_count} ads use this package. Disable instead."
        )
    
    result = await db.ad_packages.delete_one({"id": package_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Package not found")
    
    return {"success": True, "message": "Package deleted"}

@ad_packages_router.post("/{package_id}/toggle")
async def toggle_ad_package(
    package_id: str,
    user: dict = Depends(require_admin)
):
    """Toggle package status between active/disabled (Admin only)"""
    pkg = await db.ad_packages.find_one({"id": package_id})
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    
    new_status = AdPackageStatus.DISABLED.value if pkg["status"] == AdPackageStatus.ACTIVE.value else AdPackageStatus.ACTIVE.value
    
    await db.ad_packages.update_one(
        {"id": package_id},
        {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"success": True, "status": new_status}

# ==================== Ads Routes (WITH PACKAGE-BASED PRICING) ====================

@ads_router.get("/")
async def get_ads(
    user: dict = Depends(get_current_user),
    status: Optional[AdStatus] = None
):
    """Get ads - advertisers see their own, admin sees all"""
    query = {}
    
    if user["role"] == UserRole.ADVERTISER.value:
        query["advertiser_id"] = user["id"]
    
    if status and user["role"] == UserRole.SUPER_ADMIN.value:
        query["status"] = status.value
    
    ads = await db.ads.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return ads

@ads_router.get("/pending")
async def get_pending_ads(user: dict = Depends(require_admin)):
    """Admin only - get ads pending approval"""
    ads = await db.ads.find(
        {"status": AdStatus.PENDING_APPROVAL.value},
        {"_id": 0}
    ).sort("created_at", 1).to_list(1000)
    return ads

@ads_router.get("/active")
async def get_active_ads():
    """Public - get active ads for display on captive portal"""
    ads = await db.ads.find(
        {"status": AdStatus.ACTIVE.value, "is_active": True},
        {"_id": 0}
    ).to_list(100)
    return ads

@ads_router.get("/{ad_id}")
async def get_ad(ad_id: str, user: dict = Depends(get_current_user)):
    """Get a specific ad"""
    ad = await db.ads.find_one({"id": ad_id}, {"_id": 0})
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    
    # Advertisers can only see their own ads
    if user["role"] == UserRole.ADVERTISER.value and ad["advertiser_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return ad

@ads_router.post("/upload")
async def upload_ad(
    title: str = Form(...),
    ad_type: AdType = Form(...),
    package_id: str = Form(...),
    click_url: Optional[str] = Form(None),
    constituencies: Optional[str] = Form(None),  # JSON array string
    counties: Optional[str] = Form(None),  # JSON array string for county/national scope
    media: UploadFile = File(...),
    user: dict = Depends(require_role([UserRole.ADVERTISER, UserRole.SUPER_ADMIN]))
):
    """
    Upload a new ad with media file and package selection.
    - Images: Max 5MB, JPG/PNG/WEBP
    - Videos: Max 20MB, MP4/WEBM, 10-15 seconds
    - Package determines pricing and coverage scope
    """
    import json
    
    # Validate package exists and is active
    package = await db.ad_packages.find_one({"id": package_id, "status": AdPackageStatus.ACTIVE.value})
    if not package:
        raise HTTPException(status_code=400, detail="Invalid or inactive package selected")
    
    # Parse coverage selections
    selected_constituencies = []
    selected_counties = []
    is_national = False
    
    if constituencies:
        try:
            selected_constituencies = json.loads(constituencies)
        except (json.JSONDecodeError, TypeError):
            selected_constituencies = [c.strip() for c in constituencies.split(",") if c.strip()]
    
    if counties:
        try:
            selected_counties = json.loads(counties)
        except (json.JSONDecodeError, TypeError):
            selected_counties = [c.strip() for c in counties.split(",") if c.strip()]
    
    # Validate coverage based on package scope
    if package["coverage_scope"] == AdCoverageScope.CONSTITUENCY.value:
        if not selected_constituencies:
            raise HTTPException(status_code=400, detail="Please select at least one constituency")
    elif package["coverage_scope"] == AdCoverageScope.COUNTY.value:
        if not selected_counties and not selected_constituencies:
            raise HTTPException(status_code=400, detail="Please select at least one county or constituency")
    elif package["coverage_scope"] == AdCoverageScope.NATIONAL.value:
        is_national = True  # National coverage
    
    # Validate file type
    content_type = media.content_type
    
    if ad_type == AdType.IMAGE:
        if content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400, 
                detail="Invalid image type. Allowed: JPG, PNG, WEBP"
            )
    elif ad_type == AdType.VIDEO:
        if content_type not in ALLOWED_VIDEO_TYPES:
            raise HTTPException(
                status_code=400, 
                detail="Invalid video type. Allowed: MP4, WEBM"
            )
    
    # Read file content
    file_content = await media.read()
    file_size = len(file_content)
    
    # Validate file size
    if ad_type == AdType.IMAGE and file_size > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail="Image too large. Maximum size: 2MB. Recommended: 600x600 pixels"
        )
    
    if ad_type == AdType.VIDEO and file_size > MAX_VIDEO_SIZE:
        raise HTTPException(
            status_code=400, 
            detail="Video too large. Maximum size: 10MB"
        )
    
    # Generate unique filename
    file_ext = Path(media.filename).suffix.lower() or (
        ".jpg" if ad_type == AdType.IMAGE else ".mp4"
    )
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    
    # Determine upload directory
    if ad_type == AdType.IMAGE:
        upload_path = UPLOAD_DIR_IMAGES / unique_filename
        media_url = f"/uploads/ads/images/{unique_filename}"
    else:
        upload_path = UPLOAD_DIR_VIDEOS / unique_filename
        media_url = f"/uploads/ads/videos/{unique_filename}"
    
    # Save file
    with open(upload_path, "wb") as f:
        f.write(file_content)
    
    # For videos, estimate duration (simplified - real implementation would use ffprobe)
    duration_seconds = 10 if ad_type == AdType.VIDEO else 5
    
    # Create targeting object
    targeting = AdTargeting(
        constituencies=selected_constituencies,
        counties=selected_counties,
        is_national=is_national
    )
    
    # Create ad record with package info
    ad = Ad(
        title=title,
        ad_type=ad_type,
        advertiser_id=user["id"],
        package_id=package_id,
        package_name=package["name"],
        package_price=package["price"],
        media_path=str(upload_path),
        media_url=media_url,
        media_size_bytes=file_size,
        duration_seconds=duration_seconds,
        click_url=click_url,
        targeting=targeting,
        status=AdStatus.PENDING_APPROVAL,
        is_active=False
    )
    
    ad_dict = ad.model_dump()
    ad_dict["created_at"] = ad_dict["created_at"].isoformat()
    
    await db.ads.insert_one(ad_dict)
    
    return {
        "success": True,
        "ad_id": ad.id,
        "status": ad.status.value,
        "package": package["name"],
        "price": package["price"],
        "message": "Ad uploaded successfully. Awaiting admin approval."
    }

@ads_router.post("/{ad_id}/approve")
async def approve_ad(
    ad_id: str,
    approval: AdApproval,
    user: dict = Depends(require_admin)
):
    """
    Admin only - approve or reject an ad.
    Price is determined by the package - admin validates coverage and content.
    """
    ad = await db.ads.find_one({"id": ad_id}, {"_id": 0})
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    
    if ad["status"] != AdStatus.PENDING_APPROVAL.value:
        raise HTTPException(status_code=400, detail="Ad is not pending approval")
    
    if approval.approved:
        update = {
            "status": AdStatus.APPROVED.value,
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "approved_by": user["id"],
            "rejection_reason": None,
            "admin_notes": approval.admin_notes
        }
    else:
        if not approval.rejection_reason:
            raise HTTPException(status_code=400, detail="Rejection reason required")
        
        update = {
            "status": AdStatus.REJECTED.value,
            "rejection_reason": approval.rejection_reason
        }
    
    await db.ads.update_one({"id": ad_id}, {"$set": update})
    
    updated_ad = await db.ads.find_one({"id": ad_id}, {"_id": 0})
    return updated_ad

@ads_router.post("/{ad_id}/pay")
async def pay_for_ad(
    ad_id: str,
    payment_request: AdPaymentRequest,
    user: dict = Depends(require_role([UserRole.ADVERTISER, UserRole.SUPER_ADMIN]))
):
    """Pay for an approved ad via M-Pesa STK Push - price from package"""
    ad = await db.ads.find_one({"id": ad_id}, {"_id": 0})
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    
    # Verify ownership
    if user["role"] == UserRole.ADVERTISER.value and ad["advertiser_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # New flow: APPROVED → (pay) → PAID → (activate) → ACTIVE
    if ad["status"] != AdStatus.APPROVED.value:
        raise HTTPException(status_code=400, detail="Ad must be approved before payment")
    
    # Get price from package
    price = ad.get("package_price", 0)
    if price <= 0:
        raise HTTPException(status_code=400, detail="Invalid package price")
    
    # Initiate M-Pesa payment
    if not mpesa_service.is_configured():
        # For demo - simulate payment success
        # Calculate expiry based on package duration
        package = await db.ad_packages.find_one({"id": ad.get("package_id")})
        duration_days = package.get("duration_days", 7) if package else 7
        starts_at = datetime.now(timezone.utc)
        expires_at = starts_at + timedelta(days=duration_days)
        
        await db.ads.update_one(
            {"id": ad_id},
            {
                "$set": {
                    "status": AdStatus.PAID.value,
                    "paid_at": datetime.now(timezone.utc).isoformat(),
                    "starts_at": starts_at.isoformat(),
                    "expires_at": expires_at.isoformat()
                }
            }
        )
        return {
            "success": True,
            "message": "Payment simulated (M-Pesa not configured). Ad is now paid and ready for activation.",
            "ad_id": ad_id,
            "amount": price
        }
    
    # Real M-Pesa STK Push
    result = await mpesa_service.stk_push(
        phone_number=payment_request.phone_number,
        amount=int(price),
        account_ref=f"CAIWAVE-AD-{ad_id[:8]}",
        description=f"Payment for ad: {ad['title']}"
    )
    
    if result.get("ResponseCode") == "0":
        # Store checkout request ID for callback handling
        await db.ads.update_one(
            {"id": ad_id},
            {"$set": {"payment_checkout_id": result.get("CheckoutRequestID")}}
        )
        return {
            "success": True,
            "message": "STK Push sent. Check your phone to complete payment.",
            "checkout_request_id": result.get("CheckoutRequestID"),
            "amount": price
        }
    else:
        return {
            "success": False,
            "message": result.get("errorMessage", "Failed to initiate payment")
        }

@ads_router.post("/{ad_id}/activate")
async def activate_ad(ad_id: str, user: dict = Depends(require_admin)):
    """Admin only - activate a paid ad"""
    ad = await db.ads.find_one({"id": ad_id}, {"_id": 0})
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    
    if ad["status"] != AdStatus.PAID.value:
        raise HTTPException(status_code=400, detail="Ad must be paid before activation")
    
    # Set activation dates if not already set
    starts_at = ad.get("starts_at")
    expires_at = ad.get("expires_at")
    
    if not starts_at or not expires_at:
        package = await db.ad_packages.find_one({"id": ad.get("package_id")})
        duration_days = package.get("duration_days", 7) if package else 7
        starts_at = datetime.now(timezone.utc).isoformat()
        expires_at = (datetime.now(timezone.utc) + timedelta(days=duration_days)).isoformat()
    
    await db.ads.update_one(
        {"id": ad_id},
        {"$set": {
            "status": AdStatus.ACTIVE.value, 
            "is_active": True,
            "starts_at": starts_at,
            "expires_at": expires_at
        }}
    )
    
    updated_ad = await db.ads.find_one({"id": ad_id}, {"_id": 0})
    return updated_ad

@ads_router.post("/{ad_id}/suspend")
async def suspend_ad(ad_id: str, user: dict = Depends(require_admin)):
    """Admin only - suspend an active ad"""
    result = await db.ads.find_one_and_update(
        {"id": ad_id, "status": AdStatus.ACTIVE.value},
        {"$set": {"status": AdStatus.SUSPENDED.value, "is_active": False}},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Ad not found or not active")
    result.pop("_id", None)
    return result

@ads_router.post("/{ad_id}/reactivate")
async def reactivate_ad(ad_id: str, user: dict = Depends(require_admin)):
    """Admin only - reactivate a suspended ad"""
    result = await db.ads.find_one_and_update(
        {"id": ad_id, "status": AdStatus.SUSPENDED.value},
        {"$set": {"status": AdStatus.ACTIVE.value, "is_active": True}},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Ad not found or not suspended")
    result.pop("_id", None)
    return result

@ads_router.post("/{ad_id}/impression")
async def record_impression(ad_id: str, hotspot_id: Optional[str] = None):
    """Record an ad impression"""
    result = await db.ads.update_one(
        {"id": ad_id, "status": AdStatus.ACTIVE.value},
        {"$inc": {"impressions": 1}}
    )
    
    if hotspot_id:
        await db.hotspots.update_one(
            {"id": hotspot_id},
            {"$inc": {"ad_impressions_delivered": 1}}
        )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Ad not found or not active")
    
    return {"status": "recorded"}

@ads_router.post("/{ad_id}/click")
async def record_click(ad_id: str):
    """Record an ad click"""
    result = await db.ads.update_one(
        {"id": ad_id, "status": AdStatus.ACTIVE.value},
        {"$inc": {"clicks": 1}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Ad not found or not active")
    return {"status": "recorded"}

@ads_router.delete("/{ad_id}")
async def delete_ad(ad_id: str, user: dict = Depends(get_current_user)):
    """Delete an ad (advertiser can delete pending, admin can delete any)"""
    ad = await db.ads.find_one({"id": ad_id}, {"_id": 0})
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    
    # Advertisers can only delete their own pending ads
    if user["role"] == UserRole.ADVERTISER.value:
        if ad["advertiser_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        if ad["status"] not in [AdStatus.PENDING_APPROVAL.value, AdStatus.REJECTED.value]:
            raise HTTPException(status_code=400, detail="Can only delete pending or rejected ads")
    
    # Delete media file if exists
    if ad.get("media_path") and os.path.exists(ad["media_path"]):
        os.remove(ad["media_path"])
    
    await db.ads.delete_one({"id": ad_id})
    return {"status": "deleted"}

# ==================== Campaign Routes (ADMIN ONLY) ====================

@campaigns_router.get("/")
async def get_campaigns(
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN])),
    status: Optional[CampaignStatus] = None
):
    """Get all campaigns - Admin only"""
    query = {}
    if status:
        query["status"] = status.value
    
    campaigns = await db.campaigns.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return campaigns

@campaigns_router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    """Get a specific campaign - Admin only"""
    campaign = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@campaigns_router.post("/", response_model=Campaign)
async def create_campaign(
    campaign_data: CampaignCreate,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    """Create a new campaign - Admin only"""
    campaign = Campaign(
        **campaign_data.model_dump(),
        created_by=user["id"]
    )
    
    campaign_dict = campaign.model_dump()
    campaign_dict["start_date"] = campaign_dict["start_date"].isoformat()
    campaign_dict["end_date"] = campaign_dict["end_date"].isoformat()
    campaign_dict["created_at"] = campaign_dict["created_at"].isoformat()
    campaign_dict["updated_at"] = campaign_dict["updated_at"].isoformat()
    
    await db.campaigns.insert_one(campaign_dict)
    return campaign

@campaigns_router.put("/{campaign_id}")
async def update_campaign(
    campaign_id: str,
    campaign_data: CampaignCreate,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    """Update a campaign - Admin only"""
    existing = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    update_data = campaign_data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["start_date"] = update_data["start_date"].isoformat()
    update_data["end_date"] = update_data["end_date"].isoformat()
    
    await db.campaigns.update_one({"id": campaign_id}, {"$set": update_data})
    
    updated = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    return updated

@campaigns_router.post("/{campaign_id}/status")
async def update_campaign_status(
    campaign_id: str,
    status: CampaignStatus,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    """Update campaign status - Admin only"""
    result = await db.campaigns.update_one(
        {"id": campaign_id},
        {"$set": {"status": status.value, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"status": "updated", "new_status": status.value}

@campaigns_router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    """Delete a campaign - Admin only"""
    result = await db.campaigns.delete_one({"id": campaign_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"status": "deleted"}

# ==================== CAIWAVE TV Stream Routes (ADMIN ONLY) ====================

@streams_router.get("/")
async def get_streams(
    user: dict = Depends(get_current_user),
    active_only: bool = False
):
    """Get all streams - Available to all users, admin sees all"""
    query = {}
    if active_only or user["role"] != UserRole.SUPER_ADMIN.value:
        query["is_active"] = True
    
    streams = await db.streams.find(query, {"_id": 0}).sort("start_time", -1).to_list(100)
    return streams

@streams_router.get("/live")
async def get_live_streams():
    """Get currently live streams - Public endpoint for captive portal"""
    now = datetime.now(timezone.utc).isoformat()
    streams = await db.streams.find({
        "is_active": True,
        "start_time": {"$lte": now},
        "end_time": {"$gte": now}
    }, {"_id": 0}).to_list(50)
    return streams

@streams_router.get("/{stream_id}")
async def get_stream(stream_id: str, user: dict = Depends(get_current_user)):
    """Get a specific stream"""
    stream = await db.streams.find_one({"id": stream_id}, {"_id": 0})
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    return stream

@streams_router.post("/", response_model=Stream)
async def create_stream(
    stream_data: StreamCreate,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    """Create a new stream - Admin only"""
    stream = Stream(
        **stream_data.model_dump(),
        created_by=user["id"]
    )
    
    stream_dict = stream.model_dump()
    stream_dict["start_time"] = stream_dict["start_time"].isoformat()
    stream_dict["end_time"] = stream_dict["end_time"].isoformat()
    stream_dict["created_at"] = stream_dict["created_at"].isoformat()
    stream_dict["updated_at"] = stream_dict["updated_at"].isoformat()
    
    await db.streams.insert_one(stream_dict)
    return stream

@streams_router.put("/{stream_id}")
async def update_stream(
    stream_id: str,
    stream_data: StreamCreate,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    """Update a stream - Admin only"""
    existing = await db.streams.find_one({"id": stream_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    update_data = stream_data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["start_time"] = update_data["start_time"].isoformat()
    update_data["end_time"] = update_data["end_time"].isoformat()
    
    await db.streams.update_one({"id": stream_id}, {"$set": update_data})
    
    updated = await db.streams.find_one({"id": stream_id}, {"_id": 0})
    return updated

@streams_router.post("/{stream_id}/toggle")
async def toggle_stream(
    stream_id: str,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    """Toggle stream active status - Admin only"""
    stream = await db.streams.find_one({"id": stream_id}, {"_id": 0})
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    new_status = not stream.get("is_active", True)
    await db.streams.update_one(
        {"id": stream_id},
        {"$set": {"is_active": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"status": "updated", "is_active": new_status}

@streams_router.post("/{stream_id}/view")
async def record_stream_view(stream_id: str):
    """Record a stream view - Public for analytics"""
    result = await db.streams.update_one(
        {"id": stream_id, "is_active": True},
        {"$inc": {"total_views": 1}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Stream not found or not active")
    return {"status": "recorded"}

@streams_router.delete("/{stream_id}")
async def delete_stream(
    stream_id: str,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    """Delete a stream - Admin only"""
    result = await db.streams.delete_one({"id": stream_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Stream not found")
    return {"status": "deleted"}

# ==================== Subsidized Uptime Routes (ADMIN ONLY) ====================

@subsidized_router.get("/")
async def get_subsidized_uptimes(
    user: dict = Depends(get_current_user),
    active_only: bool = False
):
    """Get all subsidized uptime offers"""
    query = {}
    if active_only or user["role"] != UserRole.SUPER_ADMIN.value:
        query["status"] = SubsidizedUptimeStatus.ACTIVE.value
    
    uptimes = await db.subsidized_uptime.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return uptimes

@subsidized_router.get("/active")
async def get_active_subsidized_uptimes(hotspot_id: Optional[str] = None):
    """Get currently active subsidized offers - Public for captive portal"""
    now = datetime.now(timezone.utc).isoformat()
    query = {
        "status": SubsidizedUptimeStatus.ACTIVE.value,
        "start_date": {"$lte": now},
        "end_date": {"$gte": now}
    }
    
    if hotspot_id:
        query["$or"] = [
            {"allowed_hotspot_ids": {"$size": 0}},  # Empty = all hotspots
            {"allowed_hotspot_ids": hotspot_id}
        ]
    
    uptimes = await db.subsidized_uptime.find(query, {"_id": 0}).to_list(50)
    return uptimes

@subsidized_router.get("/{uptime_id}")
async def get_subsidized_uptime(
    uptime_id: str,
    user: dict = Depends(get_current_user)
):
    """Get a specific subsidized uptime offer"""
    uptime = await db.subsidized_uptime.find_one({"id": uptime_id}, {"_id": 0})
    if not uptime:
        raise HTTPException(status_code=404, detail="Subsidized uptime not found")
    return uptime

@subsidized_router.post("/", response_model=SubsidizedUptime)
async def create_subsidized_uptime(
    uptime_data: SubsidizedUptimeCreate,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    """Create a new subsidized uptime offer - Admin only"""
    uptime = SubsidizedUptime(
        **uptime_data.model_dump(),
        created_by=user["id"]
    )
    
    uptime_dict = uptime.model_dump()
    uptime_dict["start_date"] = uptime_dict["start_date"].isoformat()
    uptime_dict["end_date"] = uptime_dict["end_date"].isoformat()
    uptime_dict["created_at"] = uptime_dict["created_at"].isoformat()
    uptime_dict["updated_at"] = uptime_dict["updated_at"].isoformat()
    
    await db.subsidized_uptime.insert_one(uptime_dict)
    return uptime

@subsidized_router.put("/{uptime_id}")
async def update_subsidized_uptime(
    uptime_id: str,
    uptime_data: SubsidizedUptimeCreate,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    """Update a subsidized uptime offer - Admin only"""
    existing = await db.subsidized_uptime.find_one({"id": uptime_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Subsidized uptime not found")
    
    update_data = uptime_data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["start_date"] = update_data["start_date"].isoformat()
    update_data["end_date"] = update_data["end_date"].isoformat()
    
    await db.subsidized_uptime.update_one({"id": uptime_id}, {"$set": update_data})
    
    updated = await db.subsidized_uptime.find_one({"id": uptime_id}, {"_id": 0})
    return updated

@subsidized_router.post("/{uptime_id}/status")
async def update_subsidized_uptime_status(
    uptime_id: str,
    status: SubsidizedUptimeStatus,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    """Update subsidized uptime status - Admin only"""
    result = await db.subsidized_uptime.update_one(
        {"id": uptime_id},
        {"$set": {"status": status.value, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Subsidized uptime not found")
    return {"status": "updated", "new_status": status.value}

@subsidized_router.post("/{uptime_id}/use")
async def record_subsidized_uptime_use(uptime_id: str):
    """Record usage of subsidized uptime - For tracking"""
    uptime = await db.subsidized_uptime.find_one({"id": uptime_id}, {"_id": 0})
    if not uptime:
        raise HTTPException(status_code=404, detail="Subsidized uptime not found")
    
    # Check max uses
    if uptime.get("max_uses") and uptime.get("total_uses", 0) >= uptime["max_uses"]:
        raise HTTPException(status_code=400, detail="Maximum uses reached for this offer")
    
    await db.subsidized_uptime.update_one(
        {"id": uptime_id},
        {"$inc": {"total_uses": 1}}
    )
    return {"status": "recorded"}

@subsidized_router.delete("/{uptime_id}")
async def delete_subsidized_uptime(
    uptime_id: str,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    """Delete a subsidized uptime offer - Admin only"""
    result = await db.subsidized_uptime.delete_one({"id": uptime_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Subsidized uptime not found")
    return {"status": "deleted"}

# ==================== RADIUS / MikroTik NAS Routes (ADMIN ONLY) ====================

class NASClientBase(BaseModel):
    name: str
    ip_address: str
    secret: str
    shortname: Optional[str] = None
    nastype: str = "mikrotik"
    description: Optional[str] = None
    location: Optional[str] = None

class NASClient(NASClientBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    last_seen: Optional[datetime] = None

class RADIUSConfigUpdate(BaseModel):
    radius_enabled: bool = False
    radius_host: Optional[str] = None
    radius_secret: Optional[str] = None
    radius_auth_port: int = 1812
    radius_acct_port: int = 1813
    radius_coa_port: int = 3799

@radius_router.get("/config")
async def get_radius_config(user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))):
    """Get RADIUS/FreeRADIUS configuration status"""
    radius_enabled = os.environ.get('RADIUS_ENABLED', 'false').lower() == 'true'
    return {
        "enabled": radius_enabled,
        "host": RADIUS_HOST if radius_enabled else None,
        "auth_port": RADIUS_AUTH_PORT,
        "acct_port": RADIUS_ACCT_PORT,
        "configured": bool(RADIUS_HOST and RADIUS_SECRET),
        "instructions": {
            "setup": "Configure FreeRADIUS server and update .env with RADIUS_HOST, RADIUS_SECRET",
            "mikrotik": "Add NAS clients below and configure MikroTik routers to use this RADIUS server"
        }
    }

@radius_router.get("/nas-clients")
async def get_nas_clients(user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))):
    """Get all configured NAS clients (MikroTik routers)"""
    clients = await db.nas_clients.find({}, {"_id": 0}).to_list(100)
    return clients

@radius_router.post("/nas-clients", response_model=NASClient)
async def add_nas_client(
    client_data: NASClientBase,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    """Add a new NAS client (MikroTik router)"""
    # Check if IP already exists
    existing = await db.nas_clients.find_one({"ip_address": client_data.ip_address})
    if existing:
        raise HTTPException(status_code=400, detail="NAS client with this IP already exists")
    
    data = client_data.model_dump()
    if not data.get("shortname"):
        data["shortname"] = client_data.name.replace(" ", "_").lower()
    
    client = NASClient(**data)
    
    client_dict = client.model_dump()
    client_dict["created_at"] = client_dict["created_at"].isoformat()
    
    await db.nas_clients.insert_one(client_dict)
    
    return client

@radius_router.put("/nas-clients/{client_id}")
async def update_nas_client(
    client_id: str,
    client_data: NASClientBase,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    """Update a NAS client"""
    existing = await db.nas_clients.find_one({"id": client_id})
    if not existing:
        raise HTTPException(status_code=404, detail="NAS client not found")
    
    update_data = client_data.model_dump()
    await db.nas_clients.update_one({"id": client_id}, {"$set": update_data})
    
    updated = await db.nas_clients.find_one({"id": client_id}, {"_id": 0})
    return updated

@radius_router.delete("/nas-clients/{client_id}")
async def delete_nas_client(
    client_id: str,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    """Delete a NAS client"""
    result = await db.nas_clients.delete_one({"id": client_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="NAS client not found")
    return {"status": "deleted"}

@radius_router.post("/nas-clients/{client_id}/toggle")
async def toggle_nas_client(
    client_id: str,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    """Toggle NAS client active status"""
    client = await db.nas_clients.find_one({"id": client_id})
    if not client:
        raise HTTPException(status_code=404, detail="NAS client not found")
    
    new_status = not client.get("is_active", True)
    await db.nas_clients.update_one({"id": client_id}, {"$set": {"is_active": new_status}})
    
    return {"status": "updated", "is_active": new_status}

@radius_router.get("/generate-config/{client_id}")
async def generate_mikrotik_config(
    client_id: str,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    """Generate MikroTik configuration commands for a NAS client"""
    client = await db.nas_clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="NAS client not found")
    
    # Generate MikroTik RouterOS commands
    radius_server = RADIUS_HOST or "YOUR_RADIUS_SERVER_IP"
    radius_secret = client.get("secret", "YOUR_SECRET")
    
    config = f"""# ============================================
# MikroTik RADIUS Configuration for CAIWAVE
# Router: {client['name']}
# Generated: {datetime.now(timezone.utc).isoformat()}
# ============================================

# Step 1: Add RADIUS Server
/radius add service=hotspot address={radius_server} secret="{radius_secret}" timeout=3s

# Step 2: Configure Hotspot to use RADIUS
/ip hotspot profile set default use-radius=yes

# Step 3: Configure AAA (Authentication, Authorization, Accounting)
/ppp aaa set interim-update=5m use-radius=yes accounting=yes

# Step 4: Enable RADIUS incoming (for CoA/Disconnect)
/radius incoming set accept=yes port=3799

# Step 5: Create Hotspot User Profile (will be overridden by RADIUS)
/ip hotspot user profile add name="caiwave-default" rate-limit="10M/10M" session-timeout=1h

# ============================================
# IMPORTANT NOTES:
# 1. Replace {radius_server} with your actual FreeRADIUS server IP
# 2. Ensure firewall allows UDP 1812, 1813, 3799 from this router to RADIUS server
# 3. Test with: /radius monitor numbers=0
# ============================================
"""
    
    return {
        "client_name": client["name"],
        "client_ip": client["ip_address"],
        "config": config
    }

@radius_router.post("/test-connection")
async def test_radius_connection(user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))):
    """Test connection to FreeRADIUS server"""
    radius_enabled = os.environ.get('RADIUS_ENABLED', 'false').lower() == 'true'
    
    if not radius_enabled:
        return {
            "success": False,
            "message": "RADIUS is not enabled. Set RADIUS_ENABLED=true in .env"
        }
    
    if not RADIUS_HOST or not RADIUS_SECRET:
        return {
            "success": False,
            "message": "RADIUS_HOST or RADIUS_SECRET not configured in .env"
        }
    
    # In a real implementation, you would use pyrad to test the connection
    # For now, return configuration status
    return {
        "success": True,
        "message": "RADIUS configuration found",
        "host": RADIUS_HOST,
        "auth_port": RADIUS_AUTH_PORT,
        "acct_port": RADIUS_ACCT_PORT,
        "note": "For actual connection test, ensure FreeRADIUS server is running and accessible"
    }

# ==================== MikroTik Onboarding Routes ====================

class MikroTikRegisterRequest(BaseModel):
    """Request to register a new MikroTik router"""
    name: str = Field(..., min_length=3, max_length=50)
    hotspot_id: str
    notes: Optional[str] = None

class MikroTikConfirmRequest(BaseModel):
    """Request to confirm router connection"""
    router_id: str
    nas_identifier: str
    detected_ports: Optional[List[str]] = None
    detected_services: Optional[List[str]] = None
    firmware_version: Optional[str] = None
    model: Optional[str] = None

def generate_secure_secret() -> str:
    """Generate a secure RADIUS secret"""
    return secrets_module.token_hex(16)

def generate_nas_id(name: str) -> str:
    """Generate a unique NAS identifier"""
    clean_name = "".join(c for c in name if c.isalnum())[:10].upper()
    return f"CAIWAVE-{clean_name}-{secrets_module.token_hex(4).upper()}"

def generate_mikrotik_script(router_name: str, nas_id: str, radius_secret: str, radius_host: str, callback_url: str) -> str:
    """Generate a complete MikroTik auto-configuration script"""
    
    return f'''# =========================================================
# CAIWAVE MikroTik Auto-Configuration Script
# Router: {router_name}
# NAS Identifier: {nas_id}
# Generated: {datetime.now(timezone.utc).isoformat()}
# =========================================================

# IMPORTANT: Run this script in MikroTik Terminal after:
# 1. System Reset (optional but recommended for fresh install)
# 2. DHCP Client configured on ether1 for internet

:log info "CAIWAVE: Starting auto-configuration..."

# =========================================================
# 1. BASIC SYSTEM CONFIGURATION
# =========================================================
/system identity set name="{router_name}"
:log info "CAIWAVE: System identity set to {router_name}"

# Set system clock (NTP)
/system ntp client set enabled=yes servers=time.google.com

# =========================================================
# 2. BRIDGE CONFIGURATION
# =========================================================
# Create bridge for hotspot if not exists
:if ([:len [/interface bridge find name=bridge-hotspot]] = 0) do={{
    /interface bridge add name=bridge-hotspot comment="CAIWAVE Hotspot Bridge"
    :log info "CAIWAVE: Created bridge-hotspot"
}}

# Add all ethernet ports to bridge EXCEPT ether1 (WAN)
:foreach i in=[/interface ethernet find] do={{
    :local ethName [/interface ethernet get $i name]
    :if ($ethName != "ether1") do={{
        :if ([:len [/interface bridge port find interface=$ethName]] = 0) do={{
            /interface bridge port add bridge=bridge-hotspot interface=$ethName comment="CAIWAVE"
            :log info ("CAIWAVE: Added " . $ethName . " to bridge-hotspot")
        }}
    }}
}}

# =========================================================
# 3. IP CONFIGURATION FOR HOTSPOT
# =========================================================
:if ([:len [/ip address find interface=bridge-hotspot]] = 0) do={{
    /ip address add address=10.10.0.1/24 interface=bridge-hotspot comment="CAIWAVE Hotspot Network"
    :log info "CAIWAVE: Added IP 10.10.0.1/24 to bridge-hotspot"
}}

# DHCP Pool for hotspot clients
:if ([:len [/ip pool find name=pool-hotspot]] = 0) do={{
    /ip pool add name=pool-hotspot ranges=10.10.0.10-10.10.0.254
    :log info "CAIWAVE: Created DHCP pool for hotspot"
}}

# DHCP Server for hotspot
:if ([:len [/ip dhcp-server find name=dhcp-hotspot]] = 0) do={{
    /ip dhcp-server add name=dhcp-hotspot interface=bridge-hotspot address-pool=pool-hotspot disabled=no
    /ip dhcp-server network add address=10.10.0.0/24 gateway=10.10.0.1 dns-server=8.8.8.8,8.8.4.4 comment="CAIWAVE Hotspot Network"
    :log info "CAIWAVE: Configured DHCP server for hotspot"
}}

# =========================================================
# 4. DNS CONFIGURATION
# =========================================================
/ip dns set allow-remote-requests=yes servers=8.8.8.8,8.8.4.4,1.1.1.1
:log info "CAIWAVE: DNS configured"

# =========================================================
# 5. RADIUS CONFIGURATION
# =========================================================
# Remove existing CAIWAVE RADIUS config if any
:foreach r in=[/radius find comment~"CAIWAVE"] do={{
    /radius remove $r
}}

# Add CAIWAVE RADIUS server
/radius add address={radius_host} secret="{radius_secret}" service=hotspot comment="CAIWAVE RADIUS Server" timeout=3s

:log info "CAIWAVE: RADIUS server configured - {radius_host}"

# Enable RADIUS for hotspot
/ip hotspot profile set [find default=yes] use-radius=yes radius-interim-update=5m

# =========================================================
# 6. HOTSPOT SERVER PROFILE
# =========================================================
:if ([:len [/ip hotspot profile find name=caiwave-profile]] = 0) do={{
    /ip hotspot profile add name=caiwave-profile \\
        hotspot-address=10.10.0.1 \\
        dns-name=wifi.caiwave.com \\
        login-by=http-pap,http-chap \\
        use-radius=yes \\
        radius-accounting=yes \\
        nas-port-type=wireless-802.11 \\
        radius-interim-update=5m \\
        html-directory=hotspot \\
        rate-limit="" \\
        http-cookie-lifetime=1d \\
        split-user-domain=no
    :log info "CAIWAVE: Hotspot profile created"
}} else={{
    /ip hotspot profile set caiwave-profile \\
        use-radius=yes \\
        radius-accounting=yes \\
        radius-interim-update=5m
    :log info "CAIWAVE: Hotspot profile updated"
}}

# =========================================================
# 7. HOTSPOT SERVER SETUP
# =========================================================
:if ([:len [/ip hotspot find name=caiwave-hotspot]] = 0) do={{
    /ip hotspot add name=caiwave-hotspot interface=bridge-hotspot \\
        address-pool=pool-hotspot \\
        profile=caiwave-profile \\
        disabled=no
    :log info "CAIWAVE: Hotspot server created"
}} else={{
    /ip hotspot set caiwave-hotspot profile=caiwave-profile disabled=no
    :log info "CAIWAVE: Hotspot server updated"
}}

# Set NAS identifier
/ip hotspot set caiwave-hotspot addresses-per-mac=1

# =========================================================
# 8. ANTI-SHARING PROTECTION
# =========================================================
/ip hotspot set caiwave-hotspot addresses-per-mac=1

# Add connection tracking rules
:if ([:len [/ip firewall filter find comment="CAIWAVE Anti-Sharing"]] = 0) do={{
    /ip firewall filter add chain=forward action=drop connection-state=invalid comment="CAIWAVE Anti-Sharing"
}}

:log info "CAIWAVE: Anti-sharing protection enabled"

# =========================================================
# 9. FIREWALL RULES
# =========================================================
:if ([:len [/ip firewall nat find comment="CAIWAVE NAT"]] = 0) do={{
    /ip firewall nat add chain=srcnat out-interface=ether1 action=masquerade comment="CAIWAVE NAT"
    :log info "CAIWAVE: NAT masquerade configured"
}}

:if ([:len [/ip firewall filter find comment="CAIWAVE Firewall"]] = 0) do={{
    /ip firewall filter add chain=input connection-state=established,related action=accept comment="CAIWAVE Firewall"
    /ip firewall filter add chain=input connection-state=invalid action=drop comment="CAIWAVE Firewall"
    /ip firewall filter add chain=input protocol=icmp action=accept comment="CAIWAVE Firewall"
    /ip firewall filter add chain=input in-interface=bridge-hotspot action=accept comment="CAIWAVE Firewall"
    :log info "CAIWAVE: Firewall rules configured"
}}

# =========================================================
# 10. WALLED GARDEN
# =========================================================
/ip hotspot walled-garden add dst-host=*.caiwave.com action=allow comment="CAIWAVE Portal"
/ip hotspot walled-garden add dst-host=caiwave.com action=allow comment="CAIWAVE Portal"
/ip hotspot walled-garden add dst-host=*.safaricom.co.ke action=allow comment="M-Pesa"
/ip hotspot walled-garden add dst-host=safaricom.co.ke action=allow comment="M-Pesa"

:log info "CAIWAVE: Walled garden configured"

# =========================================================
# CONFIGURATION COMPLETE
# =========================================================
:log info "=========================================="
:log info "CAIWAVE AUTO-CONFIGURATION COMPLETE!"
:log info "=========================================="
:log info ("NAS Identifier: " . "{nas_id}")
:log info "Hotspot Server: caiwave-hotspot"
:log info "Hotspot Network: 10.10.0.0/24"
:log info "RADIUS Server: {radius_host}"
:log info "=========================================="

:put ""
:put "==========================================="
:put "CAIWAVE CONFIGURATION COMPLETE!"
:put "==========================================="
:put ""
:put "NAS Identifier: {nas_id}"
:put "RADIUS Secret: {radius_secret}"
:put ""
:put "Please confirm the connection in your"
:put "CAIWAVE dashboard to complete setup."
:put ""
:put "==========================================="
'''


@mikrotik_onboard_router.post("/register")
async def register_mikrotik(
    request: MikroTikRegisterRequest,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOTSPOT_OWNER]))
):
    """
    Register a new MikroTik router and generate configuration script.
    
    Flow:
    1. Hotspot owner clicks "Add MikroTik" in dashboard
    2. System validates hotspot ownership
    3. Generates secure RADIUS credentials
    4. Returns auto-configuration script
    """
    # Verify hotspot exists and user has access
    hotspot = await db.hotspots.find_one({"id": request.hotspot_id}, {"_id": 0})
    if not hotspot:
        raise HTTPException(status_code=404, detail="Hotspot not found")
    
    if user["role"] == UserRole.HOTSPOT_OWNER.value and hotspot["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied to this hotspot")
    
    # Generate secure credentials
    radius_secret = generate_secure_secret()
    nas_id = generate_nas_id(request.name)
    
    # Get RADIUS server configuration
    radius_host = os.environ.get('RADIUS_HOST', 'radius.caiwave.com')
    callback_url = os.environ.get('MPESA_CALLBACK_URL', '').replace('/mpesa/callback', '/mikrotik-onboard/confirm')
    
    if not callback_url:
        # Construct from frontend URL
        frontend_url = os.environ.get('REACT_APP_BACKEND_URL', 'https://caiwave.com')
        callback_url = f"{frontend_url}/api/mikrotik-onboard/confirm"
    
    # Create router record
    router_id = str(uuid.uuid4())
    router_record = {
        "id": router_id,
        "name": request.name,
        "hotspot_id": request.hotspot_id,
        "owner_id": user["id"],
        "radius_secret": radius_secret,
        "nas_identifier": nas_id,
        "status": "pending_configuration",
        "connection_confirmed": False,
        "detected_ports": [],
        "detected_services": [],
        "firmware_version": None,
        "model": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "configured_at": None,
        "notes": request.notes
    }
    
    await db.mikrotik_routers.insert_one(router_record)
    
    # Also register as NAS client for RADIUS
    nas_client = {
        "id": str(uuid.uuid4()),
        "name": request.name,
        "hotspot_id": request.hotspot_id,
        "ip_address": "0.0.0.0",  # Will be updated when router connects
        "secret": radius_secret,
        "nas_type": "MikroTik",
        "description": f"Auto-configured via CAIWAVE - {nas_id}",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.nas_clients.insert_one(nas_client)
    
    # Generate the script
    script = generate_mikrotik_script(
        router_name=request.name,
        nas_id=nas_id,
        radius_secret=radius_secret,
        radius_host=radius_host,
        callback_url=callback_url
    )
    
    return {
        "router_id": router_id,
        "router_name": request.name,
        "nas_identifier": nas_id,
        "radius_secret": radius_secret,
        "callback_url": callback_url,
        "script": script,
        "instructions": [
            "1. Log into your MikroTik via Winbox or Terminal",
            "2. Configure DHCP Client on ether1 for internet access",
            "3. Open Terminal in MikroTik",
            "4. Copy and paste the entire script below",
            "5. Wait for 'CONFIGURATION COMPLETE' message",
            "6. Return to this dashboard and click 'Confirm Connection'",
            "7. Test by connecting a device to your hotspot"
        ]
    }


@mikrotik_onboard_router.post("/confirm")
async def confirm_mikrotik_connection(
    request: MikroTikConfirmRequest,
    req: Request
):
    """
    Confirm router connection after script execution.
    Can be called by the router itself or manually by the owner.
    """
    # Find the router
    router = await db.mikrotik_routers.find_one({
        "id": request.router_id,
        "nas_identifier": request.nas_identifier
    }, {"_id": 0})
    
    if not router:
        raise HTTPException(status_code=404, detail="Router not found or NAS identifier mismatch")
    
    # Get client IP if available
    client_ip = req.client.host if req.client else "unknown"
    
    # Update router record
    update_data = {
        "status": "connected",
        "connection_confirmed": True,
        "configured_at": datetime.now(timezone.utc).isoformat(),
        "last_seen": datetime.now(timezone.utc).isoformat()
    }
    
    if request.detected_ports:
        update_data["detected_ports"] = request.detected_ports
    if request.detected_services:
        update_data["detected_services"] = request.detected_services
    if request.firmware_version:
        update_data["firmware_version"] = request.firmware_version
    if request.model:
        update_data["model"] = request.model
    
    await db.mikrotik_routers.update_one(
        {"id": request.router_id},
        {"$set": update_data}
    )
    
    # Update NAS client with actual IP
    await db.nas_clients.update_one(
        {"hotspot_id": router["hotspot_id"], "nas_type": "MikroTik"},
        {"$set": {"ip_address": client_ip, "last_seen": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Update hotspot status
    await db.hotspots.update_one(
        {"id": router["hotspot_id"]},
        {"$set": {
            "status": "active",
            "last_seen": datetime.now(timezone.utc).isoformat(),
            "mikrotik_connected": True
        }}
    )
    
    return {
        "success": True,
        "message": "MikroTik router connection confirmed!",
        "router_id": request.router_id,
        "status": "connected",
        "detected_ports": request.detected_ports or [],
        "detected_services": request.detected_services or []
    }


@mikrotik_onboard_router.get("/routers")
async def get_mikrotik_routers(
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOTSPOT_OWNER])),
    hotspot_id: Optional[str] = None
):
    """Get list of registered MikroTik routers"""
    query = {}
    
    if user["role"] == UserRole.HOTSPOT_OWNER.value:
        query["owner_id"] = user["id"]
    elif hotspot_id:
        query["hotspot_id"] = hotspot_id
    
    routers = await db.mikrotik_routers.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return routers


@mikrotik_onboard_router.get("/routers/{router_id}")
async def get_mikrotik_router(
    router_id: str,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOTSPOT_OWNER]))
):
    """Get details of a specific router"""
    router = await db.mikrotik_routers.find_one({"id": router_id}, {"_id": 0})
    
    if not router:
        raise HTTPException(status_code=404, detail="Router not found")
    
    if user["role"] == UserRole.HOTSPOT_OWNER.value and router["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return router


@mikrotik_onboard_router.get("/routers/{router_id}/script")
async def regenerate_mikrotik_script(
    router_id: str,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOTSPOT_OWNER]))
):
    """Regenerate the configuration script for a router"""
    router = await db.mikrotik_routers.find_one({"id": router_id}, {"_id": 0})
    
    if not router:
        raise HTTPException(status_code=404, detail="Router not found")
    
    if user["role"] == UserRole.HOTSPOT_OWNER.value and router["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    radius_host = os.environ.get('RADIUS_HOST', 'radius.caiwave.com')
    callback_url = os.environ.get('MPESA_CALLBACK_URL', '').replace('/mpesa/callback', '/mikrotik-onboard/confirm')
    
    script = generate_mikrotik_script(
        router_name=router["name"],
        nas_id=router["nas_identifier"],
        radius_secret=router["radius_secret"],
        radius_host=radius_host,
        callback_url=callback_url
    )
    
    return {
        "router_id": router_id,
        "router_name": router["name"],
        "nas_identifier": router["nas_identifier"],
        "script": script
    }


@mikrotik_onboard_router.delete("/routers/{router_id}")
async def delete_mikrotik_router(
    router_id: str,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOTSPOT_OWNER]))
):
    """Delete a registered router"""
    router = await db.mikrotik_routers.find_one({"id": router_id}, {"_id": 0})
    
    if not router:
        raise HTTPException(status_code=404, detail="Router not found")
    
    if user["role"] == UserRole.HOTSPOT_OWNER.value and router["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.mikrotik_routers.delete_one({"id": router_id})
    
    # Also remove the NAS client
    await db.nas_clients.delete_one({
        "hotspot_id": router["hotspot_id"],
        "description": {"$regex": router["nas_identifier"]}
    })
    
    return {"success": True, "message": "Router deleted successfully"}


@mikrotik_onboard_router.post("/routers/{router_id}/heartbeat")
async def mikrotik_heartbeat(router_id: str, req: Request):
    """
    Heartbeat endpoint for routers to report status.
    Can be called periodically by a MikroTik scheduler script.
    """
    router = await db.mikrotik_routers.find_one({"id": router_id}, {"_id": 0})
    
    if not router:
        raise HTTPException(status_code=404, detail="Router not found")
    
    client_ip = req.client.host if req.client else "unknown"
    
    await db.mikrotik_routers.update_one(
        {"id": router_id},
        {"$set": {
            "last_seen": datetime.now(timezone.utc).isoformat(),
            "status": "connected"
        }}
    )
    
    await db.nas_clients.update_one(
        {"hotspot_id": router["hotspot_id"], "nas_type": "MikroTik"},
        {"$set": {"ip_address": client_ip, "last_seen": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"success": True, "timestamp": datetime.now(timezone.utc).isoformat()}

# ==================== Voucher Routes ====================

@vouchers_router.post("/generate", response_model=List[Voucher])
async def generate_vouchers(
    voucher_data: VoucherBase,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOTSPOT_OWNER]))
):
    """Generate vouchers for a hotspot"""
    package = await db.packages.find_one({"id": voucher_data.package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    hotspot = await db.hotspots.find_one({"id": voucher_data.hotspot_id}, {"_id": 0})
    if not hotspot:
        raise HTTPException(status_code=404, detail="Hotspot not found")
    
    # Check access
    if user["role"] == UserRole.HOTSPOT_OWNER.value and hotspot["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    vouchers = []
    for _ in range(voucher_data.quantity):
        code = generate_voucher_code()
        username, password = generate_radius_credentials(hotspot.get("username_prefix", ""))
        
        voucher = Voucher(
            code=code,
            package_id=voucher_data.package_id,
            hotspot_id=voucher_data.hotspot_id,
            owner_id=hotspot["owner_id"],
            username=username,
            password=password,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)  # Voucher validity
        )
        
        voucher_dict = voucher.model_dump()
        voucher_dict["created_at"] = voucher_dict["created_at"].isoformat()
        voucher_dict["expires_at"] = voucher_dict["expires_at"].isoformat()
        
        await db.vouchers.insert_one(voucher_dict)
        vouchers.append(voucher)
    
    return vouchers

@vouchers_router.get("/")
async def get_vouchers(
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOTSPOT_OWNER])),
    hotspot_id: Optional[str] = None,
    unused_only: bool = False
):
    """Get vouchers"""
    query = {}
    
    if user["role"] == UserRole.HOTSPOT_OWNER.value:
        query["owner_id"] = user["id"]
    elif hotspot_id:
        query["hotspot_id"] = hotspot_id
    
    if unused_only:
        query["is_used"] = False
    
    vouchers = await db.vouchers.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return vouchers

@vouchers_router.post("/redeem/{code}")
async def redeem_voucher(code: str, hotspot_id: str, user_mac: Optional[str] = None):
    """Redeem a voucher"""
    voucher = await db.vouchers.find_one(
        {"code": code.upper(), "is_used": False},
        {"_id": 0}
    )
    
    if not voucher:
        raise HTTPException(status_code=404, detail="Invalid or already used voucher")
    
    if voucher["hotspot_id"] != hotspot_id:
        raise HTTPException(status_code=400, detail="Voucher not valid for this hotspot")
    
    # Check expiry
    if datetime.fromisoformat(voucher["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Voucher has expired")
    
    package = await db.packages.find_one({"id": voucher["package_id"]}, {"_id": 0})
    
    # Create session
    session = Session(
        package_id=voucher["package_id"],
        hotspot_id=hotspot_id,
        user_mac=user_mac,
        username=voucher["username"],
        password=voucher["password"],
        voucher_code=code,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=package["duration_minutes"])
    )
    
    session_dict = session.model_dump()
    session_dict["started_at"] = session_dict["started_at"].isoformat()
    session_dict["expires_at"] = session_dict["expires_at"].isoformat()
    
    await db.sessions.insert_one(session_dict)
    
    # Mark voucher as used
    await db.vouchers.update_one(
        {"code": code.upper()},
        {
            "$set": {
                "is_used": True,
                "used_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Update hotspot stats
    await db.hotspots.update_one(
        {"id": hotspot_id},
        {"$inc": {"total_sessions": 1}}
    )
    
    return {
        "session_id": session.id,
        "username": session.username,
        "password": session.password,
        "expires_at": session.expires_at.isoformat(),
        "duration_minutes": package["duration_minutes"]
    }

# ==================== Sessions Routes ====================

@sessions_router.post("/")
async def create_session(session_data: SessionCreate):
    """Create a new session"""
    package = await db.packages.find_one({"id": session_data.package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    hotspot = await db.hotspots.find_one({"id": session_data.hotspot_id}, {"_id": 0})
    username, password = generate_radius_credentials(
        hotspot.get("username_prefix", "") if hotspot else ""
    )
    
    session = Session(**session_data.model_dump())
    session.username = username
    session.password = password
    session.expires_at = datetime.now(timezone.utc) + timedelta(minutes=package["duration_minutes"])
    
    session_dict = session.model_dump()
    session_dict["started_at"] = session_dict["started_at"].isoformat()
    session_dict["expires_at"] = session_dict["expires_at"].isoformat()
    
    await db.sessions.insert_one(session_dict)
    
    # Update hotspot stats
    if hotspot:
        await db.hotspots.update_one(
            {"id": session_data.hotspot_id},
            {"$inc": {"total_sessions": 1}}
        )
    
    return {
        "session_id": session.id,
        "username": session.username,
        "password": session.password,
        "expires_at": session.expires_at.isoformat(),
        "duration_minutes": package["duration_minutes"]
    }

@sessions_router.get("/active")
async def get_active_sessions(
    user: dict = Depends(get_current_user),
    hotspot_id: Optional[str] = None
):
    query = {"status": SessionStatus.ACTIVE.value}
    
    if user["role"] == UserRole.HOTSPOT_OWNER.value:
        hotspots = await db.hotspots.find({"owner_id": user["id"]}, {"id": 1}).to_list(100)
        hotspot_ids = [h["id"] for h in hotspots]
        query["hotspot_id"] = {"$in": hotspot_ids}
    elif hotspot_id:
        query["hotspot_id"] = hotspot_id
    
    sessions = await db.sessions.find(query, {"_id": 0}).to_list(1000)
    return sessions

@sessions_router.get("/{session_id}")
async def get_session(session_id: str):
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@sessions_router.post("/{session_id}/extend")
async def extend_session(
    session_id: str,
    minutes: int,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOTSPOT_OWNER]))
):
    """Extend session duration (compensation feature)"""
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check ownership
    if user["role"] == UserRole.HOTSPOT_OWNER.value:
        hotspot = await db.hotspots.find_one({"id": session["hotspot_id"]}, {"_id": 0})
        if hotspot["owner_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    current_expiry = datetime.fromisoformat(session["expires_at"])
    new_expiry = current_expiry + timedelta(minutes=minutes)
    
    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {"expires_at": new_expiry.isoformat()}}
    )
    
    return {"message": f"Session extended by {minutes} minutes", "new_expires_at": new_expiry.isoformat()}

# ==================== Analytics Routes ====================

@analytics_router.get("/dashboard")
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    if user["role"] == UserRole.HOTSPOT_OWNER.value:
        hotspots = await db.hotspots.find({"owner_id": user["id"]}, {"_id": 0}).to_list(1000)
        hotspot_ids = [h["id"] for h in hotspots]
        
        total_revenue = sum(h.get("total_revenue", 0) for h in hotspots)
        total_sessions = sum(h.get("total_sessions", 0) for h in hotspots)
        
        # Get active sessions count
        active_sessions = await db.sessions.count_documents({
            "hotspot_id": {"$in": hotspot_ids},
            "status": SessionStatus.ACTIVE.value
        })
        
        return {
            "total_hotspots": len(hotspots),
            "active_hotspots": len([h for h in hotspots if h.get("status") == HotspotStatus.ACTIVE.value]),
            "total_revenue": total_revenue,
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "pending_withdrawals": 0
        }
    else:
        # Admin view
        total_hotspots = await db.hotspots.count_documents({})
        active_hotspots = await db.hotspots.count_documents({"status": HotspotStatus.ACTIVE.value})
        total_users = await db.users.count_documents({})
        
        pipeline = [{"$group": {"_id": None, "total": {"$sum": "$total_revenue"}}}]
        result = await db.hotspots.aggregate(pipeline).to_list(1)
        total_revenue = result[0]["total"] if result else 0
        
        pipeline = [{"$group": {"_id": None, "total": {"$sum": "$total_sessions"}}}]
        result = await db.hotspots.aggregate(pipeline).to_list(1)
        total_sessions = result[0]["total"] if result else 0
        
        pending_ads = await db.ads.count_documents({"status": AdStatus.PENDING_APPROVAL.value})
        active_ads = await db.ads.count_documents({"status": AdStatus.ACTIVE.value, "is_active": True})
        
        return {
            "total_hotspots": total_hotspots,
            "active_hotspots": active_hotspots,
            "total_users": total_users,
            "total_revenue": total_revenue,
            "total_sessions": total_sessions,
            "pending_ads": pending_ads,
            "active_ads": active_ads
        }

@analytics_router.get("/revenue/{hotspot_id}")
async def get_hotspot_revenue(
    hotspot_id: str,
    user: dict = Depends(get_current_user)
):
    hotspot = await db.hotspots.find_one({"id": hotspot_id}, {"_id": 0})
    if not hotspot:
        raise HTTPException(status_code=404, detail="Hotspot not found")
    
    if user["role"] == UserRole.HOTSPOT_OWNER.value and hotspot["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get completed payments
    payments = await db.payments.find(
        {"hotspot_id": hotspot_id, "status": PaymentStatus.COMPLETED.value},
        {"_id": 0}
    ).to_list(1000)
    
    total_revenue = sum(p.get("amount", 0) for p in payments)
    owner_share = sum(p.get("owner_share", 0) for p in payments)
    platform_share = sum(p.get("platform_share", 0) for p in payments)
    
    return {
        "total_revenue": total_revenue,
        "owner_share": owner_share,
        "platform_share": platform_share,
        "total_sessions": hotspot.get("total_sessions", 0),
        "total_payments": len(payments)
    }

# ==================== Settings Routes ====================

@settings_router.get("/")
async def get_settings(user: dict = Depends(require_admin)):
    """Get system settings"""
    settings = await db.settings.find_one({"type": "system"}, {"_id": 0})
    if not settings:
        settings = SystemSettings().model_dump()
    return settings.get("config", settings)

@settings_router.put("/")
async def update_settings(
    settings: SystemSettings,
    user: dict = Depends(require_admin)
):
    """Update system settings"""
    await db.settings.update_one(
        {"type": "system"},
        {"$set": {"config": settings.model_dump()}},
        upsert=True
    )
    return {"message": "Settings updated"}

@settings_router.get("/mpesa")
async def get_mpesa_settings(user: dict = Depends(require_admin)):
    """Get M-Pesa configuration status"""
    return {
        "configured": mpesa_service.is_configured(),
        "environment": MPESA_ENV,
        "shortcode_configured": bool(MPESA_SHORTCODE),
        "callback_url": MPESA_CALLBACK_URL or "Not configured"
    }

@settings_router.get("/sms")
async def get_sms_settings(user: dict = Depends(require_admin)):
    """Get SMS configuration status"""
    return {
        "configured": sms_service.is_configured(),
        "provider": SMS_PROVIDER,
        "sender_id": SMS_SENDER_ID
    }

@settings_router.get("/whatsapp")
async def get_whatsapp_settings(user: dict = Depends(require_admin)):
    """Get WhatsApp configuration status"""
    return {
        "configured": whatsapp_service.is_configured(),
        "number_configured": bool(TWILIO_WHATSAPP_NUMBER)
    }

@settings_router.get("/revenue-config")
async def get_revenue_config(user: dict = Depends(require_admin)):
    """Get revenue sharing configuration"""
    config = await db.settings.find_one({"type": "revenue_config"}, {"_id": 0})
    if not config:
        config = {"config": RevenueConfig().model_dump()}
    return config.get("config", RevenueConfig().model_dump())

@settings_router.put("/revenue-config")
async def update_revenue_config(
    config: RevenueConfig,
    user: dict = Depends(require_admin)
):
    """Update revenue sharing configuration"""
    await db.settings.update_one(
        {"type": "revenue_config"},
        {"$set": {"config": config.model_dump()}},
        upsert=True
    )
    return {"message": "Revenue configuration updated"}

# ==================== Captive Portal Routes ====================

@api_router.get("/portal/{hotspot_id}")
async def get_portal_data(hotspot_id: str):
    """Get data for captive portal display"""
    hotspot = await db.hotspots.find_one({"id": hotspot_id}, {"_id": 0})
    
    # Allow demo hotspot
    if hotspot_id == "demo":
        hotspot = {
            "id": "demo",
            "name": "CAIWAVE Demo Hotspot",
            "ssid": "Cainet-Demo_FREE WIFI",
            "location_name": "Demo Location",
            "status": HotspotStatus.ACTIVE.value
        }
    elif not hotspot:
        raise HTTPException(status_code=404, detail="Hotspot not found")
    
    # Get enabled packages or all active packages
    enabled_packages = hotspot.get("enabled_packages", [])
    if enabled_packages:
        packages = await db.packages.find(
            {"id": {"$in": enabled_packages}, "is_active": True},
            {"_id": 0}
        ).sort("price", 1).to_list(20)
    else:
        packages = await db.packages.find({"is_active": True}, {"_id": 0}).sort("price", 1).to_list(20)
    
    # Get active ads targeting this location
    ads_query = {
        "status": AdStatus.ACTIVE.value,
        "is_active": True,
        "$or": [
            {"targeting.is_global": True},
            {"targeting.hotspot_ids": hotspot_id},
            {"targeting.counties": hotspot.get("county")}
        ]
    }
    ads = await db.ads.find(ads_query, {"_id": 0}).to_list(10)
    
    return {
        "hotspot": hotspot,
        "packages": packages,
        "ads": ads,
        "mpesa_enabled": mpesa_service.is_configured()
    }

@api_router.post("/portal/free-session")
async def create_free_session(
    hotspot_id: str,
    ad_id: str,
    user_mac: Optional[str] = None
):
    """Create a free session after watching an ad"""
    # Verify ad is active
    ad = await db.ads.find_one(
        {"id": ad_id, "status": AdStatus.ACTIVE.value},
        {"_id": 0}
    )
    if not ad:
        raise HTTPException(status_code=400, detail="Invalid ad")
    
    # Record impression
    await db.ads.update_one({"id": ad_id}, {"$inc": {"impressions": 1}})
    
    if hotspot_id != "demo":
        await db.hotspots.update_one(
            {"id": hotspot_id},
            {"$inc": {"ad_impressions_delivered": 1}}
        )
    
    hotspot = await db.hotspots.find_one({"id": hotspot_id}, {"_id": 0})
    username, password = generate_radius_credentials(
        hotspot.get("username_prefix", "") if hotspot else ""
    )
    
    # Create 30-minute free session
    session = Session(
        package_id="free",
        hotspot_id=hotspot_id,
        user_mac=user_mac,
        username=username,
        password=password,
        is_free=True,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30)
    )
    
    session_dict = session.model_dump()
    session_dict["started_at"] = session_dict["started_at"].isoformat()
    session_dict["expires_at"] = session_dict["expires_at"].isoformat()
    
    await db.sessions.insert_one(session_dict)
    
    return {
        "session_id": session.id,
        "username": session.username,
        "password": session.password,
        "expires_at": session.expires_at.isoformat(),
        "duration_minutes": 30
    }

# ==================== Marketplace Routes ====================

@marketplace_router.get("/")
async def get_marketplace_items(category: Optional[str] = None):
    """Get marketplace items"""
    query = {"is_active": True}
    if category:
        query["category"] = category
    
    items = await db.marketplace.find(query, {"_id": 0}).to_list(100)
    return items

@marketplace_router.post("/")
async def add_marketplace_item(
    item: MarketplaceItem,
    user: dict = Depends(require_admin)
):
    """Admin only - add marketplace item"""
    item_dict = item.model_dump()
    await db.marketplace.insert_one(item_dict)
    return item

# ==================== Invoice & Subscription Routes ====================

def generate_invoice_number():
    """Generate unique invoice number: INV-YYYYMM-XXXX"""
    now = datetime.now(timezone.utc)
    random_suffix = str(uuid.uuid4())[:4].upper()
    return f"INV-{now.strftime('%Y%m')}-{random_suffix}"

async def create_invoice_for_owner(owner_id: str, hotspot_ids: List[str], is_trial: bool = False):
    """Helper function to create an invoice for a hotspot owner"""
    now = datetime.now(timezone.utc)
    
    # Calculate billing period (1 month from now)
    billing_start = now
    billing_end = now + timedelta(days=30)
    
    # Due date: 14 days from now (end of trial)
    due_date = now + timedelta(days=TRIAL_DAYS)
    
    invoice = Invoice(
        invoice_number=generate_invoice_number(),
        owner_id=owner_id,
        hotspot_ids=hotspot_ids,
        billing_period_start=billing_start,
        billing_period_end=billing_end,
        amount=SUBSCRIPTION_PRICE_KES * len(hotspot_ids),
        hotspot_count=len(hotspot_ids),
        status=InvoiceStatus.TRIAL if is_trial else InvoiceStatus.UNPAID,
        due_date=due_date
    )
    
    invoice_dict = invoice.model_dump()
    invoice_dict["created_at"] = invoice_dict["created_at"].isoformat()
    invoice_dict["billing_period_start"] = invoice_dict["billing_period_start"].isoformat()
    invoice_dict["billing_period_end"] = invoice_dict["billing_period_end"].isoformat()
    invoice_dict["due_date"] = invoice_dict["due_date"].isoformat()
    
    await db.invoices.insert_one(invoice_dict)
    
    # Remove MongoDB _id before returning
    invoice_dict.pop("_id", None)
    return invoice_dict

async def check_and_update_subscription_status(owner_id: str):
    """Check owner's subscription status and update hotspots accordingly"""
    now = datetime.now(timezone.utc)
    
    # Get latest invoice
    invoice = await db.invoices.find_one(
        {"owner_id": owner_id},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    
    if not invoice:
        return None
    
    # Parse dates
    created_at = datetime.fromisoformat(invoice["created_at"].replace("Z", "+00:00")) if isinstance(invoice["created_at"], str) else invoice["created_at"]
    days_since_created = (now - created_at).days
    
    # Determine status based on days
    new_status = None
    hotspot_status = HotspotStatus.ACTIVE
    
    if invoice["status"] == InvoiceStatus.PAID.value:
        new_status = SubscriptionStatus.ACTIVE
        hotspot_status = HotspotStatus.ACTIVE
    elif invoice["status"] == InvoiceStatus.TRIAL.value:
        if days_since_created < TRIAL_DAYS:
            new_status = SubscriptionStatus.TRIAL
            hotspot_status = HotspotStatus.ACTIVE
        elif days_since_created < SUSPENSION_DAY:
            new_status = SubscriptionStatus.GRACE_PERIOD
            hotspot_status = HotspotStatus.ACTIVE  # Still active but limited
            # Update invoice to unpaid
            await db.invoices.update_one(
                {"id": invoice["id"]},
                {"$set": {"status": InvoiceStatus.UNPAID.value}}
            )
        else:
            new_status = SubscriptionStatus.SUSPENDED
            hotspot_status = HotspotStatus.SUSPENDED
            await db.invoices.update_one(
                {"id": invoice["id"]},
                {"$set": {"status": InvoiceStatus.OVERDUE.value}}
            )
    elif invoice["status"] == InvoiceStatus.UNPAID.value:
        if days_since_created < SUSPENSION_DAY:
            new_status = SubscriptionStatus.GRACE_PERIOD
            hotspot_status = HotspotStatus.ACTIVE
        else:
            new_status = SubscriptionStatus.SUSPENDED
            hotspot_status = HotspotStatus.SUSPENDED
            await db.invoices.update_one(
                {"id": invoice["id"]},
                {"$set": {"status": InvoiceStatus.OVERDUE.value}}
            )
    elif invoice["status"] == InvoiceStatus.OVERDUE.value:
        new_status = SubscriptionStatus.SUSPENDED
        hotspot_status = HotspotStatus.SUSPENDED
    
    # Update hotspots
    if new_status:
        await db.hotspots.update_many(
            {"owner_id": owner_id},
            {"$set": {
                "subscription_status": new_status.value,
                "status": hotspot_status.value
            }}
        )
    
    return {"subscription_status": new_status.value if new_status else None, "days": days_since_created}

# Invoice Routes
@invoices_router.get("/")
async def get_invoices(
    user: dict = Depends(get_current_user),
    status: Optional[InvoiceStatus] = None,
    limit: int = 50
):
    """Get invoices - owners see their own, admin sees all"""
    query = {}
    
    if user["role"] == UserRole.HOTSPOT_OWNER.value:
        query["owner_id"] = user["id"]
    
    if status:
        query["status"] = status.value
    
    invoices = await db.invoices.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return invoices

@invoices_router.get("/current")
async def get_current_invoice(user: dict = Depends(require_role([UserRole.HOTSPOT_OWNER]))):
    """Get current/latest invoice for the logged-in hotspot owner"""
    invoice = await db.invoices.find_one(
        {"owner_id": user["id"]},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    
    if not invoice:
        return {"message": "No invoices found", "invoice": None}
    
    # Check and update status
    status_info = await check_and_update_subscription_status(user["id"])
    
    # Refresh invoice
    invoice = await db.invoices.find_one({"id": invoice["id"]}, {"_id": 0})
    
    return {
        "invoice": invoice,
        "subscription_status": status_info
    }

@invoices_router.get("/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    user: dict = Depends(get_current_user)
):
    """Get a specific invoice"""
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Check access
    if user["role"] == UserRole.HOTSPOT_OWNER.value and invoice["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return invoice

@invoices_router.post("/pay/{invoice_id}")
async def pay_invoice(
    invoice_id: str,
    payment_request: InvoicePaymentRequest,
    user: dict = Depends(require_role([UserRole.HOTSPOT_OWNER, UserRole.SUPER_ADMIN]))
):
    """Pay invoice via M-Pesa STK Push"""
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Verify ownership
    if user["role"] == UserRole.HOTSPOT_OWNER.value and invoice["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if invoice["status"] == InvoiceStatus.PAID.value:
        raise HTTPException(status_code=400, detail="Invoice already paid")
    
    # Initiate M-Pesa payment
    if not mpesa_service.is_configured():
        # Simulate payment success for demo
        now = datetime.now(timezone.utc)
        next_billing_end = now + timedelta(days=30)
        
        await db.invoices.update_one(
            {"id": invoice_id},
            {"$set": {
                "status": InvoiceStatus.PAID.value,
                "paid_at": now.isoformat(),
                "payment_method": "mpesa_simulated",
                "mpesa_receipt_number": f"SIM{uuid.uuid4().hex[:10].upper()}"
            }}
        )
        
        # Activate hotspots
        await db.hotspots.update_many(
            {"owner_id": invoice["owner_id"]},
            {"$set": {
                "status": HotspotStatus.ACTIVE.value,
                "subscription_status": SubscriptionStatus.ACTIVE.value,
                "subscription_end_date": next_billing_end.isoformat()
            }}
        )
        
        return {
            "success": True,
            "message": "Payment simulated (M-Pesa not configured). Subscription activated!",
            "invoice_id": invoice_id
        }
    
    # Real M-Pesa STK Push
    result = await mpesa_service.stk_push(
        phone_number=payment_request.phone_number,
        amount=int(invoice["amount"]),
        account_ref=invoice["invoice_number"],
        description="CAIWAVE Hotspot Subscription"
    )
    
    if result.get("ResponseCode") == "0":
        # Store checkout request ID
        await db.invoices.update_one(
            {"id": invoice_id},
            {"$set": {"mpesa_checkout_id": result.get("CheckoutRequestID")}}
        )
        return {
            "success": True,
            "message": "STK Push sent. Check your phone to complete payment.",
            "checkout_request_id": result.get("CheckoutRequestID")
        }
    else:
        return {
            "success": False,
            "message": result.get("errorMessage", "Failed to initiate payment")
        }

@invoices_router.post("/admin/create")
async def admin_create_invoice(
    data: InvoiceCreate,
    user: dict = Depends(require_admin)
):
    """Admin - manually create invoice for owner"""
    invoice = await create_invoice_for_owner(data.owner_id, data.hotspot_ids, is_trial=False)
    return {"success": True, "invoice": invoice}

@invoices_router.post("/admin/mark-paid/{invoice_id}")
async def admin_mark_invoice_paid(
    invoice_id: str,
    user: dict = Depends(require_admin)
):
    """Admin - manually mark invoice as paid"""
    invoice = await db.invoices.find_one({"id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    now = datetime.now(timezone.utc)
    next_billing_end = now + timedelta(days=30)
    
    await db.invoices.update_one(
        {"id": invoice_id},
        {"$set": {
            "status": InvoiceStatus.PAID.value,
            "paid_at": now.isoformat(),
            "payment_method": "manual_admin"
        }}
    )
    
    # Activate hotspots
    await db.hotspots.update_many(
        {"owner_id": invoice["owner_id"]},
        {"$set": {
            "status": HotspotStatus.ACTIVE.value,
            "subscription_status": SubscriptionStatus.ACTIVE.value,
            "subscription_end_date": next_billing_end.isoformat()
        }}
    )
    
    return {"success": True, "message": "Invoice marked as paid"}

# Subscription Routes
@subscriptions_router.get("/status")
async def get_subscription_status(user: dict = Depends(require_role([UserRole.HOTSPOT_OWNER]))):
    """Get subscription status for logged-in hotspot owner"""
    # Get hotspots
    hotspots = await db.hotspots.find({"owner_id": user["id"]}, {"_id": 0}).to_list(100)
    
    # Get current invoice
    invoice = await db.invoices.find_one(
        {"owner_id": user["id"]},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    
    # Calculate trial/subscription info
    now = datetime.now(timezone.utc)
    trial_days_remaining = 0
    subscription_status = SubscriptionStatus.TRIAL.value
    
    if invoice:
        created_at = datetime.fromisoformat(invoice["created_at"].replace("Z", "+00:00")) if isinstance(invoice["created_at"], str) else invoice["created_at"]
        days_since_created = (now - created_at).days
        
        if invoice["status"] == InvoiceStatus.PAID.value:
            subscription_status = SubscriptionStatus.ACTIVE.value
            trial_days_remaining = 0
        elif invoice["status"] == InvoiceStatus.TRIAL.value:
            trial_days_remaining = max(0, TRIAL_DAYS - days_since_created)
            subscription_status = SubscriptionStatus.TRIAL.value
        elif invoice["status"] == InvoiceStatus.UNPAID.value:
            subscription_status = SubscriptionStatus.GRACE_PERIOD.value
            trial_days_remaining = 0
        elif invoice["status"] == InvoiceStatus.OVERDUE.value:
            subscription_status = SubscriptionStatus.SUSPENDED.value
            trial_days_remaining = 0
    
    return {
        "subscription_status": subscription_status,
        "trial_days_remaining": trial_days_remaining,
        "hotspot_count": len(hotspots),
        "monthly_fee": SUBSCRIPTION_PRICE_KES * len(hotspots),
        "current_invoice": invoice,
        "hotspots": hotspots
    }

@subscriptions_router.post("/start-trial")
async def start_trial(user: dict = Depends(require_role([UserRole.HOTSPOT_OWNER]))):
    """Start 14-day free trial for new hotspot owner"""
    # Check if already has invoices
    existing = await db.invoices.find_one({"owner_id": user["id"]})
    if existing:
        raise HTTPException(status_code=400, detail="Trial already started")
    
    # Get owner's hotspots
    hotspots = await db.hotspots.find({"owner_id": user["id"]}, {"_id": 0, "id": 1}).to_list(100)
    if not hotspots:
        raise HTTPException(status_code=400, detail="No hotspots found. Create a hotspot first.")
    
    hotspot_ids = [h["id"] for h in hotspots]
    
    # Create trial invoice
    invoice = await create_invoice_for_owner(user["id"], hotspot_ids, is_trial=True)
    
    # Update hotspots with trial info
    now = datetime.now(timezone.utc)
    trial_end = now + timedelta(days=TRIAL_DAYS)
    
    await db.hotspots.update_many(
        {"owner_id": user["id"]},
        {"$set": {
            "subscription_status": SubscriptionStatus.TRIAL.value,
            "trial_start_date": now.isoformat(),
            "trial_end_date": trial_end.isoformat(),
            "status": HotspotStatus.ACTIVE.value
        }}
    )
    
    return {
        "success": True,
        "message": f"14-day free trial started! Your subscription will be due on {trial_end.strftime('%Y-%m-%d')}",
        "invoice": invoice,
        "trial_end_date": trial_end.isoformat()
    }

# Admin invoice management
@invoices_router.get("/admin/all")
async def admin_get_all_invoices(
    user: dict = Depends(require_admin),
    status: Optional[InvoiceStatus] = None,
    limit: int = 100
):
    """Admin - get all invoices with stats"""
    query = {}
    if status:
        query["status"] = status.value
    
    invoices = await db.invoices.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    
    # Get stats
    total = await db.invoices.count_documents({})
    paid = await db.invoices.count_documents({"status": InvoiceStatus.PAID.value})
    trial = await db.invoices.count_documents({"status": InvoiceStatus.TRIAL.value})
    unpaid = await db.invoices.count_documents({"status": InvoiceStatus.UNPAID.value})
    overdue = await db.invoices.count_documents({"status": InvoiceStatus.OVERDUE.value})
    
    # Revenue
    paid_invoices = await db.invoices.find({"status": InvoiceStatus.PAID.value}, {"amount": 1}).to_list(1000)
    total_revenue = sum(inv.get("amount", 0) for inv in paid_invoices)
    
    return {
        "invoices": invoices,
        "stats": {
            "total": total,
            "paid": paid,
            "trial": trial,
            "unpaid": unpaid,
            "overdue": overdue,
            "total_revenue": total_revenue
        }
    }

@invoices_router.post("/admin/suspend-overdue")
async def admin_suspend_overdue(user: dict = Depends(require_admin)):
    """Admin - suspend all overdue hotspots"""
    # Find overdue invoices
    overdue_invoices = await db.invoices.find(
        {"status": InvoiceStatus.OVERDUE.value},
        {"owner_id": 1}
    ).to_list(1000)
    
    owner_ids = list(set(inv["owner_id"] for inv in overdue_invoices))
    
    # Suspend hotspots
    result = await db.hotspots.update_many(
        {"owner_id": {"$in": owner_ids}},
        {"$set": {
            "status": HotspotStatus.SUSPENDED.value,
            "subscription_status": SubscriptionStatus.SUSPENDED.value
        }}
    )
    
    return {
        "success": True,
        "suspended_count": result.modified_count,
        "owner_count": len(owner_ids)
    }

# ==================== Seed Data Route ====================

@api_router.post("/seed")
async def seed_data():
    """Seed initial packages, ad packages, and demo data"""
    # UPDATED PACKAGES - as per spec
    default_packages = [
        {"name": "30 Minutes", "price": 5, "duration_minutes": 30, "speed_mbps": 5, "description": "Quick browsing session"},
        {"name": "4 Hours", "price": 15, "duration_minutes": 240, "speed_mbps": 10, "description": "Half-day access"},
        {"name": "8 Hours", "price": 25, "duration_minutes": 480, "speed_mbps": 10, "description": "Work day access"},
        {"name": "12 Hours", "price": 30, "duration_minutes": 720, "speed_mbps": 10, "description": "Extended access"},
        {"name": "24 Hours", "price": 35, "duration_minutes": 1440, "speed_mbps": 15, "description": "Full day unlimited"},
        {"name": "1 Week", "price": 200, "duration_minutes": 10080, "speed_mbps": 15, "description": "Weekly unlimited access"},
        {"name": "1 Month", "price": 600, "duration_minutes": 43200, "speed_mbps": 20, "description": "Monthly unlimited access"},
    ]
    
    # Clear existing packages and insert new ones
    await db.packages.delete_many({})
    
    for pkg_data in default_packages:
        package = Package(**pkg_data, is_active=True)
        pkg_dict = package.model_dump()
        pkg_dict["created_at"] = pkg_dict["created_at"].isoformat()
        await db.packages.insert_one(pkg_dict)
    
    # ==================== AD PACKAGES (New Package-Based Advertising) ====================
    ad_packages = [
        {
            "name": "Small Area",
            "description": "Advertise in selected hotspots within a single constituency. Perfect for local businesses targeting specific neighborhoods.",
            "coverage_scope": AdCoverageScope.CONSTITUENCY.value,
            "duration_days": 3,
            "price": 300,
            "max_impressions": None
        },
        {
            "name": "Large Area",
            "description": "Advertise across all hotspots within an entire constituency. Great for businesses serving a wider local audience.",
            "coverage_scope": AdCoverageScope.COUNTY.value,
            "duration_days": 7,
            "price": 1000,
            "max_impressions": None
        },
        {
            "name": "Wide Area",
            "description": "Advertise across multiple constituencies or nationwide. Ideal for county/national campaigns, political ads, and major brands.",
            "coverage_scope": AdCoverageScope.NATIONAL.value,
            "duration_days": 14,
            "price": 3500,
            "max_impressions": None
        }
    ]
    
    # Clear existing ad packages and insert new ones
    await db.ad_packages.delete_many({})
    
    for pkg_data in ad_packages:
        ad_pkg = AdPackage(**pkg_data)
        pkg_dict = ad_pkg.model_dump()
        pkg_dict["created_at"] = pkg_dict["created_at"].isoformat()
        await db.ad_packages.insert_one(pkg_dict)
    
    # Clear old ads (as per user request)
    await db.ads.delete_many({})
    
    # Note: Admin user should be created manually via registration or direct DB insert
    # DO NOT seed admin credentials in production
    
    # Create demo advertiser user (for testing only - remove in production)
    advertiser_email = "advertiser@caiwave.com"
    existing_advertiser = await db.users.find_one({"email": advertiser_email})
    if not existing_advertiser:
        advertiser = User(
            email=advertiser_email,
            name="Demo Advertiser",
            role=UserRole.ADVERTISER,
            phone="+254711000000"
        )
        advertiser_dict = advertiser.model_dump()
        advertiser_dict["password_hash"] = hash_password("advertiser123")
        advertiser_dict["created_at"] = advertiser_dict["created_at"].isoformat()
        await db.users.insert_one(advertiser_dict)
    
    # Create default revenue config
    await db.settings.update_one(
        {"type": "revenue_config"},
        {"$set": {"config": RevenueConfig().model_dump()}},
        upsert=True
    )
    
    # Add sample marketplace items
    marketplace_items = [
        {
            "name": "MikroTik hAP ac²",
            "description": "Dual-band wireless access point with 5 Gigabit ports",
            "category": "router",
            "price": 8500,
            "image_url": "https://img.routerboard.com/mimg/1455_m.png"
        },
        {
            "name": "MikroTik RB750Gr3",
            "description": "5-port Gigabit router, perfect for small hotspots",
            "category": "router",
            "price": 5500,
            "image_url": "https://img.routerboard.com/mimg/1451_m.png"
        },
        {
            "name": "Ubiquiti UniFi AP AC LR",
            "description": "Long-range access point for large coverage",
            "category": "access_point",
            "price": 12000,
            "image_url": None
        }
    ]
    
    for item_data in marketplace_items:
        existing = await db.marketplace.find_one({"name": item_data["name"]})
        if not existing:
            item = MarketplaceItem(**item_data)
            await db.marketplace.insert_one(item.model_dump())
    
    # Create hotspot owner user
    owner_email = "owner@caiwave.com"
    existing_owner = await db.users.find_one({"email": owner_email})
    owner_id = None
    if not existing_owner:
        owner = User(
            email=owner_email,
            name="Demo Hotspot Owner",
            role=UserRole.HOTSPOT_OWNER,
            phone="+254722000000"
        )
        owner_dict = owner.model_dump()
        owner_dict["password_hash"] = hash_password("owner123")
        owner_dict["created_at"] = owner_dict["created_at"].isoformat()
        await db.users.insert_one(owner_dict)
        owner_id = owner_dict["id"]
    else:
        owner_id = existing_owner["id"]
    
    # Create demo hotspot with trial
    now = datetime.now(timezone.utc)
    trial_end = now + timedelta(days=TRIAL_DAYS)
    
    existing_hotspot = await db.hotspots.find_one({"name": "Demo Cafe Hotspot"})
    if not existing_hotspot and owner_id:
        demo_hotspot = Hotspot(
            name="Demo Cafe Hotspot",
            ssid="CAIWAVE_Demo",
            location_name="Westlands Mall, Nairobi",
            county="Nairobi",
            constituency="Westlands",
            owner_id=owner_id,
            status=HotspotStatus.ACTIVE,
            subscription_status=SubscriptionStatus.TRIAL,
            trial_start_date=now,
            trial_end_date=trial_end
        )
        hotspot_dict = demo_hotspot.model_dump()
        hotspot_dict["created_at"] = hotspot_dict["created_at"].isoformat()
        hotspot_dict["trial_start_date"] = hotspot_dict["trial_start_date"].isoformat()
        hotspot_dict["trial_end_date"] = hotspot_dict["trial_end_date"].isoformat()
        await db.hotspots.insert_one(hotspot_dict)
        
        # Create trial invoice
        invoice = Invoice(
            invoice_number=generate_invoice_number(),
            owner_id=owner_id,
            hotspot_ids=[demo_hotspot.id],
            billing_period_start=now,
            billing_period_end=now + timedelta(days=30),
            amount=SUBSCRIPTION_PRICE_KES,
            hotspot_count=1,
            status=InvoiceStatus.TRIAL,
            due_date=trial_end
        )
        invoice_dict = invoice.model_dump()
        invoice_dict["created_at"] = invoice_dict["created_at"].isoformat()
        invoice_dict["billing_period_start"] = invoice_dict["billing_period_start"].isoformat()
        invoice_dict["billing_period_end"] = invoice_dict["billing_period_end"].isoformat()
        invoice_dict["due_date"] = invoice_dict["due_date"].isoformat()
        await db.invoices.insert_one(invoice_dict)
    
    return {
        "message": "Seed data created successfully",
        "details": {
            "wifi_packages": len(default_packages),
            "ad_packages": len(ad_packages),
            "advertiser": advertiser_email,
            "hotspot_owner": owner_email,
            "note": "Admin must be created separately via /api/admin/setup endpoint"
        }
    }


# Secure admin setup endpoint (use with caution)
class AdminSetupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: Optional[str] = None
    setup_key: str  # Secret key to authorize admin creation


@api_router.post("/admin/setup")
async def setup_admin(request: AdminSetupRequest):
    """Create admin account with secure setup key"""
    # Setup key should be set in environment variable
    expected_key = os.environ.get('ADMIN_SETUP_KEY', '')
    
    if not expected_key:
        raise HTTPException(status_code=503, detail="Admin setup not configured. Set ADMIN_SETUP_KEY in environment.")
    
    if request.setup_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid setup key")
    
    # Check if admin already exists
    existing = await db.users.find_one({"email": request.email})
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Check if any admin exists
    existing_admin = await db.users.find_one({"role": UserRole.SUPER_ADMIN.value})
    if existing_admin:
        raise HTTPException(status_code=400, detail="Admin already exists. Contact system administrator.")
    
    # Create admin
    admin = User(
        email=request.email,
        name=request.name,
        role=UserRole.SUPER_ADMIN,
        phone=request.phone
    )
    admin_dict = admin.model_dump()
    admin_dict["password_hash"] = hash_password(request.password)
    admin_dict["created_at"] = admin_dict["created_at"].isoformat()
    await db.users.insert_one(admin_dict)
    
    return {"message": "Admin account created successfully", "email": request.email}

# Root endpoint
@api_router.get("/")
async def root():
    return {
        "message": "CAIWAVE Wi-Fi Hotspot Billing Platform API",
        "version": "2.1.0",
        "powered_by": "CAIWAVE © 2026",
        "domain": "www.caiwave.com"
    }

# Root-level health check for Kubernetes
@app.get("/health")
async def root_health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mpesa_configured": mpesa_service.is_configured(),
        "sms_configured": sms_service.is_configured(),
        "whatsapp_configured": whatsapp_service.is_configured()
    }

# Include all routers
api_router.include_router(auth_router)
api_router.include_router(packages_router)
api_router.include_router(hotspots_router)
api_router.include_router(sessions_router)
api_router.include_router(payments_router)
api_router.include_router(mpesa_router)
api_router.include_router(paystack_router)
api_router.include_router(ads_router)
api_router.include_router(ad_packages_router)
api_router.include_router(campaigns_router)
api_router.include_router(streams_router)
api_router.include_router(subsidized_router)
api_router.include_router(analytics_router)
api_router.include_router(locations_router)
api_router.include_router(radius_router)
api_router.include_router(mikrotik_onboard_router)
api_router.include_router(notifications_router)
api_router.include_router(settings_router)
api_router.include_router(vouchers_router)
api_router.include_router(marketplace_router)
api_router.include_router(invoices_router)
api_router.include_router(subscriptions_router)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
