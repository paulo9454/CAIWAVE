"""
CAIWAVE Wi-Fi Hotspot Billing Platform
Main FastAPI Application - Refactored Version

This server has been refactored to use a modular architecture:
- /models: Pydantic models and enums
- /services: Business logic (M-Pesa, SMS, WhatsApp, Notifications)
- /utils: Helper functions (auth, vouchers, revenue, locations)
- /config.py: Configuration management
- /database.py: MongoDB connection
"""
from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Form, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import os
import logging
import json
from pathlib import Path
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import shutil
import mimetypes

# Import from modular structure
from config import (
    ROOT_DIR, UPLOAD_DIR, UPLOAD_DIR_IMAGES, UPLOAD_DIR_VIDEOS,
    MAX_IMAGE_SIZE, MAX_VIDEO_SIZE, ALLOWED_IMAGE_TYPES, ALLOWED_VIDEO_TYPES,
    SUBSCRIPTION_PRICE_KES, TRIAL_DAYS, GRACE_PERIOD_DAYS, RADIUS_HOST,
    RADIUS_SECRET, RADIUS_AUTH_PORT, RADIUS_ACCT_PORT
)
from database import db, client
from models import (
    # Enums
    UserRole, AdType, AdStatus, SessionStatus, PaymentStatus, PaymentMethod,
    HotspotStatus, NotificationType, CampaignStatus, StreamAccessType,
    SubsidizedUptimeStatus, AdCoverageScope, AdPackageStatus, InvoiceStatus,
    SubscriptionStatus,
    # User models
    UserBase, UserCreate, UserLogin, User, UserResponse,
    # Package models
    PackageBase, Package,
    # Hotspot models
    MikroTikConfig, HotspotBase, HotspotCreate, Hotspot,
    # Invoice models
    Invoice, InvoiceCreate, InvoicePaymentRequest,
    # Session models
    SessionBase, SessionCreate, Session,
    # Payment models
    PaymentBase, PaymentCreate, Payment, MPesaSTKPushRequest, MPesaSTKCallback,
    # Ad models
    AdPackage, AdPackageCreate, AdPackageUpdate, AdTargeting, Ad, AdApproval, AdPaymentRequest,
    # Voucher models
    VoucherBase, Voucher,
    # Campaign models
    CampaignBase, CampaignCreate, Campaign, StreamBase, StreamCreate, Stream,
    SubsidizedUptimeBase, SubsidizedUptimeCreate, SubsidizedUptime,
    # Settings models
    NotificationRequest, RevenueConfig, DynamicRevenue, SystemSettings, MarketplaceItem
)
from utils import (
    hash_password, verify_password, create_token, get_current_user,
    require_role, require_admin, security,
    generate_voucher_code, generate_radius_credentials,
    calculate_dynamic_revenue,
    get_all_counties, get_constituencies, get_all_constituencies, KENYA_LOCATIONS
)
from services import (
    mpesa_service, sms_service, whatsapp_service, notification_service
)
from pydantic import BaseModel, EmailStr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the main app
app = FastAPI(title="CAIWAVE Wi-Fi Hotspot Billing Platform", version="2.1.0")

# Mount static files for ad media
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR.parent)), name="uploads")

# Create routers
api_router = APIRouter(prefix="/api")
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
packages_router = APIRouter(prefix="/packages", tags=["Packages"])
hotspots_router = APIRouter(prefix="/hotspots", tags=["Hotspots"])
sessions_router = APIRouter(prefix="/sessions", tags=["Sessions"])
payments_router = APIRouter(prefix="/payments", tags=["Payments"])
mpesa_router = APIRouter(prefix="/mpesa", tags=["M-Pesa"])
ads_router = APIRouter(prefix="/ads", tags=["Advertisements"])
ad_packages_router = APIRouter(prefix="/ad-packages", tags=["Ad Packages"])
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
invoices_router = APIRouter(prefix="/invoices", tags=["Invoices"])
subscriptions_router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


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
        return {"message": "If the email exists, a reset link will be sent"}
    
    reset_token = str(uuid.uuid4())
    await db.password_resets.insert_one({
        "user_id": user["id"],
        "token": reset_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "used": False
    })
    
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
    hotspot.status = HotspotStatus.ACTIVE
    hotspot.subscription_status = SubscriptionStatus.TRIAL
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
    
    owner_id = hotspot_data.owner_id or user["id"]
    await create_invoice_for_owner(owner_id, [hotspot.id], is_trial=True)
    
    return hotspot

@hotspots_router.put("/{hotspot_id}/packages", response_model=Hotspot)
async def update_hotspot_packages(
    hotspot_id: str,
    package_ids: List[str],
    user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.HOTSPOT_OWNER]))
):
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
async def initiate_stk_push(request: MPesaSTKPushRequest):
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
    phone_number: str
    invoice_id: str

class AdvertiserPayment(BaseModel):
    phone_number: str
    ad_id: str

class ClientWiFiPayment(BaseModel):
    phone_number: str
    package_id: str
    hotspot_id: str

@mpesa_router.post("/owner/pay-subscription")
async def owner_pay_subscription(
    payment: OwnerSubscriptionPayment,
    user: dict = Depends(require_role([UserRole.HOTSPOT_OWNER, UserRole.SUPER_ADMIN]))
):
    invoice = await db.invoices.find_one({"id": payment.invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if user["role"] == UserRole.HOTSPOT_OWNER.value and invoice["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if invoice["status"] == InvoiceStatus.PAID.value:
        raise HTTPException(status_code=400, detail="Invoice already paid")
    
    amount = invoice["amount"]
    account_ref = f"SUB-{invoice['invoice_number']}"
    
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
    
    result = await mpesa_service.stk_push(
        phone_number=payment.phone_number,
        amount=amount,
        account_ref=account_ref,
        description="CAIWAVE Sub"
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
    ad = await db.ads.find_one({"id": payment.ad_id}, {"_id": 0})
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    
    if user["role"] == UserRole.ADVERTISER.value and ad["advertiser_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if ad["status"] != AdStatus.APPROVED.value:
        raise HTTPException(status_code=400, detail="Ad must be approved before payment")
    
    amount = ad.get("package_price", 0)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid ad price")
    
    account_ref = f"AD-{ad['id'][:8].upper()}"
    
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
    
    result = await mpesa_service.stk_push(
        phone_number=payment.phone_number,
        amount=amount,
        account_ref=account_ref,
        description=f"CAIWAVE Ad"
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
    package = await db.packages.find_one({"id": payment.package_id, "is_active": True}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="Package not found or inactive")
    
    hotspot = await db.hotspots.find_one({"id": payment.hotspot_id}, {"_id": 0})
    if not hotspot:
        raise HTTPException(status_code=404, detail="Hotspot not found")
    
    if hotspot["status"] != HotspotStatus.ACTIVE.value:
        raise HTTPException(status_code=400, detail="Hotspot is not active")
    
    amount = package["price"]
    account_ref = f"WIFI-{payment.hotspot_id[:4].upper()}-{str(uuid.uuid4())[:4].upper()}"
    
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
    
    result = await mpesa_service.stk_push(
        phone_number=payment.phone_number,
        amount=amount,
        account_ref=account_ref,
        description=f"CAIWAVE WiFi"
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
    try:
        callback_data = await request.json()
        logging.info(f"M-Pesa Callback received: {json.dumps(callback_data, indent=2)}")
    except Exception as e:
        logging.error(f"Failed to parse callback data: {e}")
        return {"ResultCode": 0, "ResultDesc": "Accepted"}
    
    body = callback_data.get("Body", {})
    stk_callback = body.get("stkCallback", {})
    
    checkout_request_id = stk_callback.get("CheckoutRequestID")
    result_code = stk_callback.get("ResultCode")
    result_desc = stk_callback.get("ResultDesc")
    
    logging.info(f"Callback - CheckoutID: {checkout_request_id}, ResultCode: {result_code}, Desc: {result_desc}")
    
    transaction = await db.mpesa_transactions.find_one(
        {"mpesa_checkout_id": checkout_request_id},
        {"_id": 0}
    )
    
    if not transaction:
        transaction = await db.payments.find_one(
            {"mpesa_checkout_request_id": checkout_request_id},
            {"_id": 0}
        )
        if transaction:
            await handle_legacy_payment_callback(transaction, stk_callback, result_code)
            return {"ResultCode": 0, "ResultDesc": "Accepted"}
        
        logging.warning(f"Transaction not found for checkout: {checkout_request_id}")
        return {"ResultCode": 0, "ResultDesc": "Accepted"}
    
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
        
        payment_type = transaction.get("type")
        
        if payment_type == "subscription":
            await handle_subscription_payment_success(transaction, mpesa_receipt)
        elif payment_type == "advertising":
            await handle_ad_payment_success(transaction, mpesa_receipt)
        elif payment_type == "wifi":
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
    invoice_id = transaction.get("invoice_id")
    owner_id = transaction.get("owner_id")
    
    if not invoice_id:
        logging.error(f"No invoice_id in subscription transaction: {transaction['id']}")
        return
    
    now = datetime.now(timezone.utc)
    next_billing_end = now + timedelta(days=30)
    
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
    ad_id = transaction.get("ad_id")
    
    if not ad_id:
        logging.error(f"No ad_id in advertising transaction: {transaction['id']}")
        return
    
    now = datetime.now(timezone.utc)
    
    ad = await db.ads.find_one({"id": ad_id}, {"_id": 0})
    if not ad:
        logging.error(f"Ad not found: {ad_id}")
        return
    
    package = await db.ad_packages.find_one({"id": ad.get("package_id")})
    duration_days = package.get("duration_days", 7) if package else 7
    
    expires_at = now + timedelta(days=duration_days)
    
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
    hotspot_id = transaction.get("hotspot_id")
    package_id = transaction.get("package_id")
    phone_number = transaction.get("phone_number")
    amount = transaction.get("amount", 0)
    
    if not all([hotspot_id, package_id]):
        logging.error(f"Missing data in wifi transaction: {transaction['id']}")
        return
    
    package = await db.packages.find_one({"id": package_id}, {"_id": 0})
    hotspot = await db.hotspots.find_one({"id": hotspot_id}, {"_id": 0})
    
    if not package or not hotspot:
        logging.error(f"Package or hotspot not found for transaction: {transaction['id']}")
        return
    
    now = datetime.now(timezone.utc)
    
    revenue = await calculate_dynamic_revenue(hotspot_id, amount)
    
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
    
    username, password = generate_radius_credentials(hotspot.get("username_prefix", ""))
    
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
    
    await db.payments.update_one(
        {"id": payment.id},
        {"$set": {"session_id": session.id}}
    )
    
    await db.hotspots.update_one(
        {"id": hotspot_id},
        {"$inc": {"total_revenue": amount, "total_sessions": 1}}
    )
    
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
    transaction = await db.mpesa_transactions.find_one(
        {"mpesa_checkout_id": checkout_request_id},
        {"_id": 0}
    )
    
    if transaction:
        return {
            "found_in_db": True,
            "transaction": transaction
        }
    
    result = await mpesa_service.query_stk_status(checkout_request_id)
    return {
        "found_in_db": False,
        "safaricom_response": result
    }

@mpesa_router.get("/transaction/{transaction_id}")
async def get_transaction(transaction_id: str):
    transaction = await db.mpesa_transactions.find_one(
        {"id": transaction_id},
        {"_id": 0}
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@mpesa_router.get("/wifi-credentials/{checkout_request_id}")
async def get_wifi_credentials(checkout_request_id: str):
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
    query = {}
    if payment_type:
        query["type"] = payment_type
    if status:
        query["status"] = status
    
    transactions = await db.mpesa_transactions.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    
    stats = {
        "total": await db.mpesa_transactions.count_documents({}),
        "completed": await db.mpesa_transactions.count_documents({"status": "completed"}),
        "pending": await db.mpesa_transactions.count_documents({"status": "pending"}),
        "failed": await db.mpesa_transactions.count_documents({"status": "failed"})
    }
    
    return {
        "transactions": transactions,
        "stats": stats
    }
