from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'caitech-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Create the main app
app = FastAPI(title="CAITECH Wi-Fi Hotspot Billing Platform")

# Create routers
api_router = APIRouter(prefix="/api")
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
packages_router = APIRouter(prefix="/packages", tags=["Packages"])
hotspots_router = APIRouter(prefix="/hotspots", tags=["Hotspots"])
sessions_router = APIRouter(prefix="/sessions", tags=["Sessions"])
payments_router = APIRouter(prefix="/payments", tags=["Payments"])
ads_router = APIRouter(prefix="/ads", tags=["Advertisements"])
campaigns_router = APIRouter(prefix="/campaigns", tags=["Campaigns"])
analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])
locations_router = APIRouter(prefix="/locations", tags=["Locations"])

security = HTTPBearer()

# Enums
class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    HOTSPOT_OWNER = "hotspot_owner"
    ADVERTISER = "advertiser"
    END_USER = "end_user"

class AdType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    TEXT = "text"
    LINK = "link"

class CampaignStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"

class SessionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

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

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    phone: Optional[str]
    role: UserRole
    is_active: bool
    balance: float

# Package Models
class PackageBase(BaseModel):
    name: str
    price: float
    duration_minutes: int
    speed_mbps: float = 10.0
    description: Optional[str] = None
    is_active: bool = True

class PackageCreate(PackageBase):
    pass

class Package(PackageBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Hotspot Models
class HotspotBase(BaseModel):
    name: str
    ssid: str
    location_name: str
    ward: Optional[str] = None
    constituency: Optional[str] = None
    county: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    mikrotik_ip: Optional[str] = None
    mikrotik_user: Optional[str] = None
    is_active: bool = True

class HotspotCreate(HotspotBase):
    owner_id: str

class Hotspot(HotspotBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_revenue: float = 0.0
    total_sessions: int = 0

# Session Models
class SessionBase(BaseModel):
    package_id: str
    hotspot_id: str
    user_mac: Optional[str] = None

class SessionCreate(SessionBase):
    user_id: Optional[str] = None

class Session(SessionBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    status: SessionStatus = SessionStatus.ACTIVE
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = None
    data_used_mb: float = 0.0
    is_free: bool = False

# Payment Models
class PaymentBase(BaseModel):
    amount: float
    phone_number: str
    session_id: Optional[str] = None

class PaymentCreate(PaymentBase):
    hotspot_id: str
    package_id: str

class Payment(PaymentBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hotspot_id: str
    package_id: str
    status: PaymentStatus = PaymentStatus.PENDING
    mpesa_receipt: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

# Ad Models
class AdBase(BaseModel):
    title: str
    ad_type: AdType
    content_url: Optional[str] = None
    text_content: Optional[str] = None
    link_url: Optional[str] = None
    duration_seconds: int = 10

class AdCreate(AdBase):
    pass

class Ad(AdBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    advertiser_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    impressions: int = 0
    clicks: int = 0
    is_active: bool = True

# Campaign Models
class CampaignBase(BaseModel):
    name: str
    budget: float
    start_date: datetime
    end_date: datetime
    target_global: bool = False
    target_hotspots: List[str] = []
    target_wards: List[str] = []
    target_constituencies: List[str] = []

class CampaignCreate(CampaignBase):
    ad_ids: List[str]

class Campaign(CampaignBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    advertiser_id: str
    ad_ids: List[str] = []
    status: CampaignStatus = CampaignStatus.DRAFT
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_impressions: int = 0
    total_spent: float = 0.0

# Location Models
class Location(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str  # county, constituency, ward
    parent_id: Optional[str] = None

# Analytics Models
class RevenueStats(BaseModel):
    total_revenue: float
    owner_share: float
    platform_share: float
    total_sessions: int
    active_users: int

class DashboardStats(BaseModel):
    total_hotspots: int
    active_hotspots: int
    total_users: int
    total_revenue: float
    total_sessions: int
    active_campaigns: int

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

# ==================== Packages Routes ====================

@packages_router.get("/", response_model=List[Package])
async def get_packages(active_only: bool = True):
    query = {"is_active": True} if active_only else {}
    packages = await db.packages.find(query, {"_id": 0}).to_list(100)
    return packages

@packages_router.post("/", response_model=Package)
async def create_package(
    package_data: PackageCreate,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    package = Package(**package_data.model_dump())
    package_dict = package.model_dump()
    package_dict["created_at"] = package_dict["created_at"].isoformat()
    await db.packages.insert_one(package_dict)
    return package

@packages_router.put("/{package_id}", response_model=Package)
async def update_package(
    package_id: str,
    package_data: PackageCreate,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))
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

@packages_router.delete("/{package_id}")
async def delete_package(
    package_id: str,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    result = await db.packages.delete_one({"id": package_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Package not found")
    return {"message": "Package deleted"}

# ==================== Hotspots Routes ====================

@hotspots_router.get("/", response_model=List[Hotspot])
async def get_hotspots(
    user: dict = Depends(get_current_user),
    owner_id: Optional[str] = None
):
    query = {}
    if user["role"] == UserRole.HOTSPOT_OWNER.value:
        query["owner_id"] = user["id"]
    elif owner_id:
        query["owner_id"] = owner_id
    
    hotspots = await db.hotspots.find(query, {"_id": 0}).to_list(1000)
    return hotspots

@hotspots_router.get("/{hotspot_id}", response_model=Hotspot)
async def get_hotspot(hotspot_id: str):
    hotspot = await db.hotspots.find_one({"id": hotspot_id}, {"_id": 0})
    if not hotspot:
        raise HTTPException(status_code=404, detail="Hotspot not found")
    return hotspot

@hotspots_router.post("/", response_model=Hotspot)
async def create_hotspot(
    hotspot_data: HotspotCreate,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOTSPOT_OWNER]))
):
    if user["role"] == UserRole.HOTSPOT_OWNER.value:
        hotspot_data.owner_id = user["id"]
    
    hotspot = Hotspot(**hotspot_data.model_dump())
    hotspot_dict = hotspot.model_dump()
    hotspot_dict["created_at"] = hotspot_dict["created_at"].isoformat()
    await db.hotspots.insert_one(hotspot_dict)
    return hotspot

@hotspots_router.put("/{hotspot_id}", response_model=Hotspot)
async def update_hotspot(
    hotspot_id: str,
    hotspot_data: HotspotBase,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOTSPOT_OWNER]))
):
    query = {"id": hotspot_id}
    if user["role"] == UserRole.HOTSPOT_OWNER.value:
        query["owner_id"] = user["id"]
    
    result = await db.hotspots.find_one_and_update(
        query,
        {"$set": hotspot_data.model_dump()},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Hotspot not found")
    result.pop("_id", None)
    return result

# ==================== Sessions Routes ====================

@sessions_router.post("/", response_model=Session)
async def create_session(session_data: SessionCreate):
    package = await db.packages.find_one({"id": session_data.package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    session = Session(**session_data.model_dump())
    session.expires_at = datetime.now(timezone.utc) + timedelta(minutes=package["duration_minutes"])
    
    session_dict = session.model_dump()
    session_dict["started_at"] = session_dict["started_at"].isoformat()
    session_dict["expires_at"] = session_dict["expires_at"].isoformat()
    
    await db.sessions.insert_one(session_dict)
    
    # Update hotspot stats
    await db.hotspots.update_one(
        {"id": session_data.hotspot_id},
        {"$inc": {"total_sessions": 1}}
    )
    
    return session

@sessions_router.get("/active", response_model=List[Session])
async def get_active_sessions(
    hotspot_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = {"status": SessionStatus.ACTIVE.value}
    if hotspot_id:
        query["hotspot_id"] = hotspot_id
    
    sessions = await db.sessions.find(query, {"_id": 0}).to_list(1000)
    return sessions

@sessions_router.get("/{session_id}", response_model=Session)
async def get_session(session_id: str):
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

# ==================== Payments Routes (Mock M-Pesa) ====================

@payments_router.post("/initiate", response_model=Payment)
async def initiate_payment(payment_data: PaymentCreate):
    package = await db.packages.find_one({"id": payment_data.package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    payment = Payment(**payment_data.model_dump())
    payment_dict = payment.model_dump()
    payment_dict["created_at"] = payment_dict["created_at"].isoformat()
    
    await db.payments.insert_one(payment_dict)
    
    # Mock M-Pesa STK Push - In production, this would call Daraja API
    # Simulate instant success for demo
    return payment

@payments_router.post("/confirm/{payment_id}", response_model=dict)
async def confirm_payment(payment_id: str, mpesa_code: Optional[str] = None):
    """Mock payment confirmation - simulates M-Pesa callback"""
    payment = await db.payments.find_one({"id": payment_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Generate mock receipt
    receipt = mpesa_code or f"MOCK{uuid.uuid4().hex[:8].upper()}"
    
    await db.payments.update_one(
        {"id": payment_id},
        {
            "$set": {
                "status": PaymentStatus.COMPLETED.value,
                "mpesa_receipt": receipt,
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Create session automatically
    session_data = SessionCreate(
        package_id=payment["package_id"],
        hotspot_id=payment["hotspot_id"]
    )
    
    package = await db.packages.find_one({"id": payment["package_id"]}, {"_id": 0})
    session = Session(**session_data.model_dump())
    session.expires_at = datetime.now(timezone.utc) + timedelta(minutes=package["duration_minutes"])
    
    session_dict = session.model_dump()
    session_dict["started_at"] = session_dict["started_at"].isoformat()
    session_dict["expires_at"] = session_dict["expires_at"].isoformat()
    
    await db.sessions.insert_one(session_dict)
    
    # Update hotspot revenue
    await db.hotspots.update_one(
        {"id": payment["hotspot_id"]},
        {
            "$inc": {
                "total_revenue": payment["amount"],
                "total_sessions": 1
            }
        }
    )
    
    return {
        "status": "success",
        "receipt": receipt,
        "session_id": session.id,
        "expires_at": session.expires_at.isoformat()
    }

@payments_router.get("/", response_model=List[Payment])
async def get_payments(
    hotspot_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = {}
    if user["role"] == UserRole.HOTSPOT_OWNER.value:
        hotspots = await db.hotspots.find({"owner_id": user["id"]}, {"id": 1}).to_list(100)
        hotspot_ids = [h["id"] for h in hotspots]
        query["hotspot_id"] = {"$in": hotspot_ids}
    elif hotspot_id:
        query["hotspot_id"] = hotspot_id
    
    payments = await db.payments.find(query, {"_id": 0}).to_list(1000)
    return payments

# ==================== Ads Routes ====================

@ads_router.get("/", response_model=List[Ad])
async def get_ads(
    user: dict = Depends(get_current_user),
    active_only: bool = True
):
    query = {}
    if user["role"] == UserRole.ADVERTISER.value:
        query["advertiser_id"] = user["id"]
    if active_only:
        query["is_active"] = True
    
    ads = await db.ads.find(query, {"_id": 0}).to_list(1000)
    return ads

@ads_router.post("/", response_model=Ad)
async def create_ad(
    ad_data: AdCreate,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADVERTISER]))
):
    ad = Ad(**ad_data.model_dump(), advertiser_id=user["id"])
    ad_dict = ad.model_dump()
    ad_dict["created_at"] = ad_dict["created_at"].isoformat()
    await db.ads.insert_one(ad_dict)
    return ad

@ads_router.put("/{ad_id}", response_model=Ad)
async def update_ad(
    ad_id: str,
    ad_data: AdBase,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADVERTISER]))
):
    query = {"id": ad_id}
    if user["role"] == UserRole.ADVERTISER.value:
        query["advertiser_id"] = user["id"]
    
    result = await db.ads.find_one_and_update(
        query,
        {"$set": ad_data.model_dump()},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Ad not found")
    result.pop("_id", None)
    return result

@ads_router.post("/{ad_id}/impression")
async def record_impression(ad_id: str):
    result = await db.ads.update_one(
        {"id": ad_id},
        {"$inc": {"impressions": 1}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Ad not found")
    return {"status": "recorded"}

@ads_router.post("/{ad_id}/click")
async def record_click(ad_id: str):
    result = await db.ads.update_one(
        {"id": ad_id},
        {"$inc": {"clicks": 1}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Ad not found")
    return {"status": "recorded"}

# ==================== Campaigns Routes ====================

@campaigns_router.get("/", response_model=List[Campaign])
async def get_campaigns(
    user: dict = Depends(get_current_user),
    status: Optional[CampaignStatus] = None
):
    query = {}
    if user["role"] == UserRole.ADVERTISER.value:
        query["advertiser_id"] = user["id"]
    if status:
        query["status"] = status.value
    
    campaigns = await db.campaigns.find(query, {"_id": 0}).to_list(1000)
    return campaigns

@campaigns_router.post("/", response_model=Campaign)
async def create_campaign(
    campaign_data: CampaignCreate,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADVERTISER]))
):
    campaign = Campaign(**campaign_data.model_dump(), advertiser_id=user["id"])
    campaign_dict = campaign.model_dump()
    campaign_dict["created_at"] = campaign_dict["created_at"].isoformat()
    campaign_dict["start_date"] = campaign_dict["start_date"].isoformat()
    campaign_dict["end_date"] = campaign_dict["end_date"].isoformat()
    await db.campaigns.insert_one(campaign_dict)
    return campaign

@campaigns_router.put("/{campaign_id}/status", response_model=Campaign)
async def update_campaign_status(
    campaign_id: str,
    status: CampaignStatus,
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADVERTISER]))
):
    query = {"id": campaign_id}
    if user["role"] == UserRole.ADVERTISER.value:
        query["advertiser_id"] = user["id"]
    
    result = await db.campaigns.find_one_and_update(
        query,
        {"$set": {"status": status.value}},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Campaign not found")
    result.pop("_id", None)
    return result

# ==================== Analytics Routes ====================

@analytics_router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    if user["role"] == UserRole.HOTSPOT_OWNER.value:
        hotspots = await db.hotspots.find({"owner_id": user["id"]}, {"_id": 0}).to_list(1000)
        hotspot_ids = [h["id"] for h in hotspots]
        
        total_revenue = sum(h.get("total_revenue", 0) for h in hotspots)
        total_sessions = sum(h.get("total_sessions", 0) for h in hotspots)
        
        return DashboardStats(
            total_hotspots=len(hotspots),
            active_hotspots=len([h for h in hotspots if h.get("is_active")]),
            total_users=0,
            total_revenue=total_revenue,
            total_sessions=total_sessions,
            active_campaigns=0
        )
    else:
        # Admin view
        total_hotspots = await db.hotspots.count_documents({})
        active_hotspots = await db.hotspots.count_documents({"is_active": True})
        total_users = await db.users.count_documents({})
        active_campaigns = await db.campaigns.count_documents({"status": CampaignStatus.ACTIVE.value})
        
        pipeline = [{"$group": {"_id": None, "total": {"$sum": "$total_revenue"}}}]
        result = await db.hotspots.aggregate(pipeline).to_list(1)
        total_revenue = result[0]["total"] if result else 0
        
        pipeline = [{"$group": {"_id": None, "total": {"$sum": "$total_sessions"}}}]
        result = await db.hotspots.aggregate(pipeline).to_list(1)
        total_sessions = result[0]["total"] if result else 0
        
        return DashboardStats(
            total_hotspots=total_hotspots,
            active_hotspots=active_hotspots,
            total_users=total_users,
            total_revenue=total_revenue,
            total_sessions=total_sessions,
            active_campaigns=active_campaigns
        )

@analytics_router.get("/revenue/{hotspot_id}", response_model=RevenueStats)
async def get_revenue_stats(
    hotspot_id: str,
    user: dict = Depends(get_current_user)
):
    hotspot = await db.hotspots.find_one({"id": hotspot_id}, {"_id": 0})
    if not hotspot:
        raise HTTPException(status_code=404, detail="Hotspot not found")
    
    if user["role"] == UserRole.HOTSPOT_OWNER.value and hotspot["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    total_revenue = hotspot.get("total_revenue", 0)
    owner_share = total_revenue * 0.7  # 70% to owner
    platform_share = total_revenue * 0.3  # 30% to platform
    
    active_sessions = await db.sessions.count_documents({
        "hotspot_id": hotspot_id,
        "status": SessionStatus.ACTIVE.value
    })
    
    return RevenueStats(
        total_revenue=total_revenue,
        owner_share=owner_share,
        platform_share=platform_share,
        total_sessions=hotspot.get("total_sessions", 0),
        active_users=active_sessions
    )

# ==================== Locations Routes ====================

@locations_router.get("/counties")
async def get_counties():
    counties = await db.locations.find({"type": "county"}, {"_id": 0}).to_list(100)
    return counties

@locations_router.get("/constituencies")
async def get_constituencies(county_id: Optional[str] = None):
    query = {"type": "constituency"}
    if county_id:
        query["parent_id"] = county_id
    constituencies = await db.locations.find(query, {"_id": 0}).to_list(500)
    return constituencies

@locations_router.get("/wards")
async def get_wards(constituency_id: Optional[str] = None):
    query = {"type": "ward"}
    if constituency_id:
        query["parent_id"] = constituency_id
    wards = await db.locations.find(query, {"_id": 0}).to_list(2000)
    return wards

# ==================== Captive Portal Routes ====================

@api_router.get("/portal/{hotspot_id}")
async def get_portal_data(hotspot_id: str):
    """Get data for captive portal display"""
    hotspot = await db.hotspots.find_one({"id": hotspot_id}, {"_id": 0})
    if not hotspot:
        raise HTTPException(status_code=404, detail="Hotspot not found")
    
    packages = await db.packages.find({"is_active": True}, {"_id": 0}).to_list(20)
    
    # Get active ads for this location
    ads = await db.ads.find({"is_active": True}, {"_id": 0}).to_list(10)
    
    return {
        "hotspot": hotspot,
        "packages": packages,
        "ads": ads
    }

@api_router.post("/portal/free-session")
async def create_free_session(hotspot_id: str, ad_id: str, user_mac: Optional[str] = None):
    """Create a free session after watching an ad"""
    # Record ad impression
    await db.ads.update_one({"id": ad_id}, {"$inc": {"impressions": 1}})
    
    # Create 15-minute free session
    session = Session(
        package_id="free",
        hotspot_id=hotspot_id,
        user_mac=user_mac,
        is_free=True,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
    )
    
    session_dict = session.model_dump()
    session_dict["started_at"] = session_dict["started_at"].isoformat()
    session_dict["expires_at"] = session_dict["expires_at"].isoformat()
    
    await db.sessions.insert_one(session_dict)
    
    return {
        "session_id": session.id,
        "expires_at": session.expires_at.isoformat(),
        "duration_minutes": 15
    }

# ==================== Seed Data Route ====================

@api_router.post("/seed")
async def seed_data():
    """Seed initial packages and demo data"""
    # Default packages
    default_packages = [
        {"name": "Quick Access", "price": 5, "duration_minutes": 15, "speed_mbps": 5, "description": "15 minutes quick access"},
        {"name": "Half Hour", "price": 10, "duration_minutes": 30, "speed_mbps": 10, "description": "30 minutes browsing"},
        {"name": "One Hour", "price": 20, "duration_minutes": 60, "speed_mbps": 10, "description": "1 hour unlimited browsing"},
        {"name": "Half Day", "price": 50, "duration_minutes": 360, "speed_mbps": 15, "description": "6 hours premium access"},
        {"name": "Full Day", "price": 100, "duration_minutes": 1440, "speed_mbps": 20, "description": "24 hours unlimited access"},
    ]
    
    for pkg_data in default_packages:
        existing = await db.packages.find_one({"name": pkg_data["name"]})
        if not existing:
            package = Package(**pkg_data, is_active=True)
            pkg_dict = package.model_dump()
            pkg_dict["created_at"] = pkg_dict["created_at"].isoformat()
            await db.packages.insert_one(pkg_dict)
    
    # Create super admin if not exists
    admin_email = "admin@caitech.com"
    existing_admin = await db.users.find_one({"email": admin_email})
    if not existing_admin:
        admin = User(
            email=admin_email,
            name="Super Admin",
            role=UserRole.SUPER_ADMIN,
            phone="+254700000000"
        )
        admin_dict = admin.model_dump()
        admin_dict["password_hash"] = hash_password("admin123")
        admin_dict["created_at"] = admin_dict["created_at"].isoformat()
        await db.users.insert_one(admin_dict)
    
    return {"message": "Seed data created successfully"}

# Root endpoint
@api_router.get("/")
async def root():
    return {"message": "CAITECH Wi-Fi Hotspot Billing Platform API", "version": "1.0.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include all routers
api_router.include_router(auth_router)
api_router.include_router(packages_router)
api_router.include_router(hotspots_router)
api_router.include_router(sessions_router)
api_router.include_router(payments_router)
api_router.include_router(ads_router)
api_router.include_router(campaigns_router)
api_router.include_router(analytics_router)
api_router.include_router(locations_router)

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
