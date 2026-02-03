from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Query, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'caiwave-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# M-Pesa Configuration (Daraja API)
MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY', '')
MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET', '')
MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE', '')
MPESA_PASSKEY = os.environ.get('MPESA_PASSKEY', '')
MPESA_CALLBACK_URL = os.environ.get('MPESA_CALLBACK_URL', '')
MPESA_ENV = os.environ.get('MPESA_ENV', 'sandbox')  # 'sandbox' or 'production'

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
app = FastAPI(title="CAIWAVE Wi-Fi Hotspot Billing Platform", version="2.0.0")

# Create routers
api_router = APIRouter(prefix="/api")
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
packages_router = APIRouter(prefix="/packages", tags=["Packages"])
hotspots_router = APIRouter(prefix="/hotspots", tags=["Hotspots"])
sessions_router = APIRouter(prefix="/sessions", tags=["Sessions"])
payments_router = APIRouter(prefix="/payments", tags=["Payments"])
mpesa_router = APIRouter(prefix="/mpesa", tags=["M-Pesa"])
ads_router = APIRouter(prefix="/ads", tags=["Advertisements"])
campaigns_router = APIRouter(prefix="/campaigns", tags=["Campaigns"])
streams_router = APIRouter(prefix="/streams", tags=["CAIWAVE TV"])
subsidized_router = APIRouter(prefix="/subsidized-uptime", tags=["Subsidized Uptime"])
analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])
locations_router = APIRouter(prefix="/locations", tags=["Locations"])
radius_router = APIRouter(prefix="/radius", tags=["RADIUS"])
notifications_router = APIRouter(prefix="/notifications", tags=["Notifications"])
settings_router = APIRouter(prefix="/settings", tags=["Settings"])
vouchers_router = APIRouter(prefix="/vouchers", tags=["Vouchers"])
marketplace_router = APIRouter(prefix="/marketplace", tags=["Marketplace"])

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
    BANNER = "banner"
    TEXT = "text"

class AdStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
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
class AdTargeting(BaseModel):
    is_global: bool = False
    counties: List[str] = Field(default_factory=list)
    constituencies: List[str] = Field(default_factory=list)
    wards: List[str] = Field(default_factory=list)
    hotspot_ids: List[str] = Field(default_factory=list)

class AdBase(BaseModel):
    title: str
    ad_type: AdType
    content_url: Optional[str] = None
    text_content: Optional[str] = None
    link_url: Optional[str] = None
    duration_seconds: int = 10
    targeting: AdTargeting = Field(default_factory=AdTargeting)

class AdCreate(AdBase):
    pass

class Ad(AdBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    advertiser_id: str
    status: AdStatus = AdStatus.PENDING  # REQUIRES ADMIN APPROVAL
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    impressions: int = 0
    clicks: int = 0
    is_active: bool = False  # Only active after approval

class AdApproval(BaseModel):
    approved: bool
    rejection_reason: Optional[str] = None

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
        """Check if M-Pesa is properly configured"""
        return all([
            self.consumer_key,
            self.consumer_secret,
            self.shortcode,
            self.passkey,
            self.callback_url
        ])
    
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
            raise HTTPException(status_code=503, detail="M-Pesa not configured. Please add credentials in settings.")
        
        # Format phone number (254XXXXXXXXX)
        phone = phone_number.replace("+", "").replace(" ", "")
        if phone.startswith("0"):
            phone = "254" + phone[1:]
        elif not phone.startswith("254"):
            phone = "254" + phone
        
        access_token = await self.get_access_token()
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
            "CallBackURL": self.callback_url,
            "AccountReference": account_ref,
            "TransactionDesc": description
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mpesa/stkpush/v1/processrequest",
                json=payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
            )
            
            return response.json()
    
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
    
    hotspot = Hotspot(**hotspot_data.model_dump())
    hotspot.status = HotspotStatus.ACTIVE  # Default to active for new hotspots
    hotspot_dict = hotspot.model_dump()
    hotspot_dict["created_at"] = hotspot_dict["created_at"].isoformat()
    if hotspot_dict.get("last_seen"):
        hotspot_dict["last_seen"] = hotspot_dict["last_seen"].isoformat()
    
    await db.hotspots.insert_one(hotspot_dict)
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
    """Initiate M-Pesa STK Push payment"""
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

@mpesa_router.post("/callback")
async def mpesa_callback(callback_data: MPesaSTKCallback):
    """Handle M-Pesa STK Push callback"""
    body = callback_data.Body
    stk_callback = body.get("stkCallback", {})
    
    checkout_request_id = stk_callback.get("CheckoutRequestID")
    result_code = stk_callback.get("ResultCode")
    
    # Find the payment
    payment = await db.payments.find_one(
        {"mpesa_checkout_request_id": checkout_request_id},
        {"_id": 0}
    )
    
    if not payment:
        logging.error(f"Payment not found for checkout: {checkout_request_id}")
        return {"ResultCode": 0, "ResultDesc": "Accepted"}
    
    if result_code == 0:
        # Payment successful
        callback_metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])
        mpesa_receipt = None
        for item in callback_metadata:
            if item.get("Name") == "MpesaReceiptNumber":
                mpesa_receipt = item.get("Value")
                break
        
        # Calculate revenue sharing
        revenue = await calculate_dynamic_revenue(payment["hotspot_id"], payment["amount"])
        
        # Update payment
        await db.payments.update_one(
            {"id": payment["id"]},
            {
                "$set": {
                    "status": PaymentStatus.COMPLETED.value,
                    "mpesa_receipt": mpesa_receipt,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "owner_share": revenue.owner_share,
                    "platform_share": revenue.platform_share
                }
            }
        )
        
        # Create session
        package = await db.packages.find_one({"id": payment["package_id"]}, {"_id": 0})
        hotspot = await db.hotspots.find_one({"id": payment["hotspot_id"]}, {"_id": 0})
        
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
        
        # Update payment with session ID
        await db.payments.update_one(
            {"id": payment["id"]},
            {"$set": {"session_id": session.id}}
        )
        
        # Update hotspot stats
        await db.hotspots.update_one(
            {"id": payment["hotspot_id"]},
            {
                "$inc": {
                    "total_revenue": payment["amount"],
                    "total_sessions": 1
                }
            }
        )
        
        # Send notification
        await notification_service.send_payment_confirmation(
            payment["phone_number"],
            payment["amount"],
            f"{package['duration_minutes']} minutes",
            {"sms_enabled": True, "whatsapp_enabled": False}
        )
    else:
        # Payment failed
        await db.payments.update_one(
            {"id": payment["id"]},
            {"$set": {"status": PaymentStatus.FAILED.value}}
        )
    
    return {"ResultCode": 0, "ResultDesc": "Accepted"}

@mpesa_router.get("/status/{checkout_request_id}")
async def check_payment_status(checkout_request_id: str):
    """Check the status of an STK Push request"""
    result = await mpesa_service.query_stk_status(checkout_request_id)
    return result

@mpesa_router.get("/config-status")
async def get_mpesa_config_status(user: dict = Depends(require_admin)):
    """Check if M-Pesa is configured"""
    return {
        "configured": mpesa_service.is_configured(),
        "environment": MPESA_ENV,
        "shortcode": MPESA_SHORTCODE if MPESA_SHORTCODE else None
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

# ==================== Ads Routes (WITH ADMIN APPROVAL) ====================

@ads_router.get("/", response_model=List[Ad])
async def get_ads(
    user: dict = Depends(get_current_user),
    status: Optional[AdStatus] = None,
    approved_only: bool = False
):
    query = {}
    
    if user["role"] == UserRole.ADVERTISER.value:
        query["advertiser_id"] = user["id"]
    elif approved_only:
        query["status"] = AdStatus.APPROVED.value
        query["is_active"] = True
    
    if status and user["role"] == UserRole.SUPER_ADMIN.value:
        query["status"] = status.value
    
    ads = await db.ads.find(query, {"_id": 0}).to_list(1000)
    return ads

@ads_router.get("/pending", response_model=List[Ad])
async def get_pending_ads(user: dict = Depends(require_admin)):
    """Admin only - get ads pending approval"""
    ads = await db.ads.find(
        {"status": AdStatus.PENDING.value},
        {"_id": 0}
    ).sort("created_at", 1).to_list(1000)
    return ads

@ads_router.post("/", response_model=Ad)
async def create_ad(
    ad_data: AdCreate,
    user: dict = Depends(require_role([UserRole.ADVERTISER, UserRole.SUPER_ADMIN]))
):
    """Create ad - goes to PENDING status for admin approval"""
    ad = Ad(**ad_data.model_dump(), advertiser_id=user["id"])
    ad.status = AdStatus.PENDING  # Always pending until admin approves
    ad.is_active = False
    
    ad_dict = ad.model_dump()
    ad_dict["created_at"] = ad_dict["created_at"].isoformat()
    
    await db.ads.insert_one(ad_dict)
    return ad

@ads_router.post("/{ad_id}/approve", response_model=Ad)
async def approve_ad(
    ad_id: str,
    approval: AdApproval,
    user: dict = Depends(require_admin)
):
    """Admin only - approve or reject an ad"""
    ad = await db.ads.find_one({"id": ad_id}, {"_id": 0})
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    
    if approval.approved:
        update = {
            "status": AdStatus.APPROVED.value,
            "is_active": True,
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "approved_by": user["id"],
            "rejection_reason": None
        }
    else:
        update = {
            "status": AdStatus.REJECTED.value,
            "is_active": False,
            "rejection_reason": approval.rejection_reason
        }
    
    result = await db.ads.find_one_and_update(
        {"id": ad_id},
        {"$set": update},
        return_document=True
    )
    result.pop("_id", None)
    return result

@ads_router.post("/{ad_id}/suspend")
async def suspend_ad(ad_id: str, user: dict = Depends(require_admin)):
    """Admin only - suspend an approved ad"""
    result = await db.ads.find_one_and_update(
        {"id": ad_id},
        {"$set": {"status": AdStatus.SUSPENDED.value, "is_active": False}},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Ad not found")
    result.pop("_id", None)
    return result

@ads_router.post("/{ad_id}/impression")
async def record_impression(ad_id: str, hotspot_id: Optional[str] = None):
    """Record an ad impression"""
    result = await db.ads.update_one(
        {"id": ad_id, "status": AdStatus.APPROVED.value},
        {"$inc": {"impressions": 1}}
    )
    
    if hotspot_id:
        await db.hotspots.update_one(
            {"id": hotspot_id},
            {"$inc": {"ad_impressions_delivered": 1}}
        )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Ad not found or not approved")
    
    return {"status": "recorded"}

@ads_router.post("/{ad_id}/click")
async def record_click(ad_id: str):
    """Record an ad click"""
    result = await db.ads.update_one(
        {"id": ad_id, "status": AdStatus.APPROVED.value},
        {"$inc": {"clicks": 1}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Ad not found or not approved")
    return {"status": "recorded"}

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
        
        pending_ads = await db.ads.count_documents({"status": AdStatus.PENDING.value})
        active_ads = await db.ads.count_documents({"status": AdStatus.APPROVED.value, "is_active": True})
        
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
    
    # Get approved ads targeting this location
    ads_query = {
        "status": AdStatus.APPROVED.value,
        "is_active": True,
        "$or": [
            {"targeting.is_global": True},
            {"targeting.hotspot_ids": hotspot_id},
            {"targeting.wards": hotspot.get("ward")},
            {"targeting.constituencies": hotspot.get("constituency")},
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
    # Verify ad is approved
    ad = await db.ads.find_one(
        {"id": ad_id, "status": AdStatus.APPROVED.value},
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

# ==================== Seed Data Route ====================

@api_router.post("/seed")
async def seed_data():
    """Seed initial packages and demo data"""
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
    
    # Create super admin if not exists
    admin_email = "admin@caiwave.com"
    existing_admin = await db.users.find_one({"email": admin_email})
    if not existing_admin:
        admin = User(
            email=admin_email,
            name="CAIWAVE Admin",
            role=UserRole.SUPER_ADMIN,
            phone="+254700000000"
        )
        admin_dict = admin.model_dump()
        admin_dict["password_hash"] = hash_password("admin123")
        admin_dict["created_at"] = admin_dict["created_at"].isoformat()
        await db.users.insert_one(admin_dict)
    
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
    
    return {"message": "Seed data created successfully - packages updated to new pricing"}

# Root endpoint
@api_router.get("/")
async def root():
    return {
        "message": "CAIWAVE Wi-Fi Hotspot Billing Platform API",
        "version": "2.0.0",
        "powered_by": "CAIWAVE © 2026"
    }

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
api_router.include_router(ads_router)
api_router.include_router(campaigns_router)
api_router.include_router(analytics_router)
api_router.include_router(locations_router)
api_router.include_router(radius_router)
api_router.include_router(notifications_router)
api_router.include_router(settings_router)
api_router.include_router(vouchers_router)
api_router.include_router(marketplace_router)

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
