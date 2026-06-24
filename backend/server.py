from backend.routes.demo import router as demo_router
from backend.routes import api_router
"""
from datetime import datetime, timedelta, timezone
import logging
CAIWAVE Wi-Fi Hotspot Billing Platform
Main FastAPI Application (RESTORED CLEAN VERSION)
"""

import os
import base64
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any

import httpx
from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.core.database import db


# ==================== APP INIT ====================

from backend.core.demo_mode import DEMO_MODE
app = FastAPI(title="CAIWAVE Wi-Fi Billing Platform")
app.middleware("http")
app.state.DEMO_MODE = DEMO_MODE
app.include_router(demo_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.caiwave.com",
        "https://caiwave.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== DATABASE ====================


# ==================== MPESA SERVICE ====================

class MPesaService:
    def __init__(self):
        self.env = os.getenv("MPESA_ENV", "sandbox")
        self.consumer_key = os.getenv("MPESA_CONSUMER_KEY")
        self.consumer_secret = os.getenv("MPESA_CONSUMER_SECRET")
        self.shortcode = os.getenv("MPESA_SHORTCODE")
        self.passkey = os.getenv("MPESA_PASSKEY")
        self.callback_url = os.getenv("MPESA_CALLBACK_URL")

        self.base_url = (
            "https://sandbox.safaricom.co.ke"
            if self.env == "sandbox"
            else "https://api.safaricom.co.ke"
        )

    def is_configured(self) -> bool:
        return all([
            self.consumer_key,
            self.consumer_secret,
            self.shortcode,
            self.passkey
        ])

    def generate_password(self):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password_str = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode()
        return password, timestamp

    async def get_access_token(self):
        if not self.is_configured():
            raise HTTPException(status_code=503, detail="M-Pesa not configured")

        credentials = base64.b64encode(
            f"{self.consumer_key}:{self.consumer_secret}".encode()
        ).decode()

        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials",
                headers={"Authorization": f"Basic {credentials}"}
            )
            return r.json()["access_token"]

    async def stk_push(self, phone: str, amount: float, ref: str, desc: str):
        if not self.is_configured():
            return {"error": "M-Pesa not configured"}

        phone = phone.replace("+", "").replace(" ", "")
        if phone.startswith("0"):
            phone = "254" + phone[1:]

        password, timestamp = self.generate_password()

        return {
            "status": "restored_stub",
            "phone": phone,
            "amount": amount,
            "reference": ref
        }

mpesa_service = MPesaService()

# ==================== SMS SERVICE ====================

class SMSService:
    def __init__(self):
        self.api_key = os.getenv("SMS_API_KEY")
        self.username = os.getenv("SMS_USERNAME")

    def is_configured(self):
        return bool(self.api_key and self.username)

sms_service = SMSService()

# ==================== BASIC ROUTES ====================

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "CAIWAVE",
        "time": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    return {"message": "CAIWAVE API RESTORED SUCCESSFULLY"}

# ==================== INCLUDE ROUTER ====================

app.include_router(api_router, prefix="/api")


# ==================== MODELS (SIMPLIFIED) ====================

def serialize(doc):
    if not doc:
        return None
    doc["_id"] = str(doc.get("_id"))
    return doc

# ==================== HOTSPOTS ====================

@app.get("/hotspots")
async def get_hotspots():
    hotspots = await db.hotspots.find({}, {"_id": 0}).to_list(100)
    return {"hotspots": hotspots}


# ==================== ADS ====================

@app.get("/ads")
async def get_ads():
    ads = await db.ads.find({"is_active": True}, {"_id": 0}).to_list(50)
    return {"ads": ads}

# ==================== FREE SESSION ====================

@app.post("/portal/free-session")
async def create_free_session(hotspot_id: str, ad_id: str, user_mac: str = None, user_ip: str = None):

    user_identifier = user_mac or user_ip or "unknown"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    free_count = await db.sessions.count_documents({
        "is_free": True,
        "hotspot_id": hotspot_id,
        "$or": [
            {"user_mac": user_identifier},
            {"user_ip": user_identifier}
        ],
        "date": today
    })

    if free_count >= 2:
        raise HTTPException(status_code=403, detail="Daily free limit reached")

    ad = await db.ads.find_one({"id": ad_id, "is_active": True})
    if not ad:
        raise HTTPException(status_code=400, detail="Invalid ad")

    session = {
        "id": str(datetime.utcnow().timestamp()),
        "hotspot_id": hotspot_id,
        "user_mac": user_identifier,
        "is_free": True,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(minutes=15)).isoformat(),
        "date": today
    }

    await db.sessions.insert_one(session)

    return {
        "status": "active",
        "minutes": 15,
        "remaining": 2 - free_count - 1
    }

@app.get("/portal/free-session-status")
async def free_session_status(hotspot_id: str, user_mac: str = None, user_ip: str = None):

    user_identifier = user_mac or user_ip or "unknown"

    sessions = await db.sessions.find({
        "hotspot_id": hotspot_id,
        "$or": [
            {"user_mac": user_identifier},
            {"user_ip": user_identifier}
        ],
        "is_free": True
    }).to_list(10)

    return {
        "active_sessions": len(sessions),
        "sessions": sessions
    }

# ==================== MPESA CALLBACK ====================

@app.post("/mpesa/callback")
async def mpesa_callback(request: Request):
    data = await request.json()
    logging.info(f"MPESA CALLBACK: {data}")

    try:
        body = data.get("Body", {}).get("stkCallback", {})
        result_code = body.get("ResultCode")
        checkout_id = body.get("CheckoutRequestID")

        if result_code == 0:
            metadata = body.get("CallbackMetadata", {}).get("Item", [])
            amount = None
            phone = None
            receipt = None

            for item in metadata:
                if item.get("Name") == "Amount":
                    amount = item.get("Value")
                if item.get("Name") == "PhoneNumber":
                    phone = item.get("Value")
                if item.get("Name") == "MpesaReceiptNumber":
                    receipt = item.get("Value")

            await db.payments.insert_one({
                "checkout_id": checkout_id,
                "amount": amount,
                "phone": phone,
                "receipt": receipt,
                "status": "success",
                "created_at": datetime.utcnow().isoformat()
            })

        else:
            await db.payments.insert_one({
                "checkout_id": checkout_id,
                "status": "failed",
                "created_at": datetime.utcnow().isoformat()
            })

    except Exception as e:
        logging.error(f"Callback error: {e}")

    return {"status": "ok"}

# ==================== MPESA PAYMENT INIT ====================

@app.post("/payments/stk-push")
async def stk_push_payment(phone: str, amount: float, account_ref: str = "CAIWAVE"):

    if not mpesa_service.is_configured():
        raise HTTPException(status_code=503, detail="M-Pesa not configured")

    try:
        access_token = await mpesa_service.get_access_token()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    password, timestamp = mpesa_service.generate_password()

    payload = {
        "BusinessShortCode": mpesa_service.shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone,
        "PartyB": mpesa_service.shortcode,
        "PhoneNumber": phone,
        "CallBackURL": mpesa_service.callback_url or "https://example.com/mpesa/callback",
        "AccountReference": account_ref,
        "TransactionDesc": "CAIWAVE WiFi Payment"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{mpesa_service.base_url}/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )

    result = response.json()

    await db.payments.insert_one({
        "phone": phone,
        "amount": amount,
        "status": "pending",
        "response": result,
        "created_at": datetime.utcnow().isoformat()
    })

    return result

# ==================== PAYMENT STATUS ====================

@app.get("/payments")
async def get_payments():
    payments = await db.payments.find({}, {"_id": 0}).to_list(100)
    return {"payments": payments}

@app.get("/payments/{phone}")
async def get_payment_by_phone(phone: str):
    payments = await db.payments.find({"phone": phone}, {"_id": 0}).to_list(100)
    return {"payments": payments}

# ==================== HOTSPOT ACCESS ENGINE ====================

async def activate_hotspot_access(phone: str, amount: float):
    """
    Converts successful payment into internet access session
    """

    package = await db.packages.find_one(
        {"price": {"$lte": amount}, "is_active": True},
        sort=[("price", -1)]
    )

    if not package:
        logging.warning("No matching package found for payment")
        return None

    session = {
        "id": str(datetime.utcnow().timestamp()),
        "phone": phone,
        "package_id": package["id"],
        "bandwidth": package.get("bandwidth", "1M/1M"),
        "duration_minutes": package.get("duration", 60),
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(minutes=package.get("duration", 60))).isoformat()
    }

    await db.sessions.insert_one(session)

    return session

# ==================== PAYMENT → ACCESS LINK ====================

async def handle_successful_payment(phone: str, amount: float):
    session = await activate_hotspot_access(phone, amount)

    if session:
        logging.info(f"Hotspot activated for {phone}: {session['id']}")

    return session


@app.post("/mpesa/callback-enhanced")
async def mpesa_callback_enhanced(request: Request):
    data = await request.json()
    logging.info(f"MPESA CALLBACK (ENHANCED): {data}")

    try:
        body = data.get("Body", {}).get("stkCallback", {})
        result_code = body.get("ResultCode")
        checkout_id = body.get("CheckoutRequestID")

        if result_code == 0:
            metadata = body.get("CallbackMetadata", {}).get("Item", [])

            amount = None
            phone = None
            receipt = None

            for item in metadata:
                if item.get("Name") == "Amount":
                    amount = item.get("Value")
                if item.get("Name") == "PhoneNumber":
                    phone = item.get("Value")
                if item.get("Name") == "MpesaReceiptNumber":
                    receipt = item.get("Value")

            await db.payments.insert_one({
                "checkout_id": checkout_id,
                "amount": amount,
                "phone": phone,
                "receipt": receipt,
                "status": "success",
                "created_at": datetime.utcnow().isoformat()
            })

            # 🔥 KEY MOMENT: ACTIVATE INTERNET
            await handle_successful_payment(phone, amount)

        else:
            await db.payments.insert_one({
                "checkout_id": checkout_id,
                "status": "failed",
                "created_at": datetime.utcnow().isoformat()
            })

    except Exception as e:
        logging.error(f"Enhanced callback error: {e}")

    return {"status": "ok"}

# ==================== RADIUS / MIKROTIK LAYER ====================

class RadiusService:
    """
    Stub for MikroTik / RADIUS integration
    Replace later with real router API calls
    """

    async def create_user(self, username: str, password: str, bandwidth: str):
        logging.info(f"[RADIUS] Creating user {username} with {bandwidth}")

        # Placeholder for MikroTik API call
        return {
            "username": username,
            "password": password,
            "bandwidth": bandwidth,
            "status": "created"
        }

radius_service = RadiusService()

# ==================== SESSION PROVISIONING ====================

async def provision_user_session(session: dict):
    """
    Push session to MikroTik/RADIUS system
    """

    username = f"user_{session['id'][:8]}"
    password = "auto123"

    result = await radius_service.create_user(
        username=username,
        password=password,
        bandwidth=session.get("bandwidth", "1M/1M")
    )

    await db.radius_users.insert_one({
        "session_id": session["id"],
        "username": username,
        "created_at": datetime.utcnow().isoformat(),
        "status": result["status"]
    })

    return result
