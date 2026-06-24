"""
CAIWAVE Paystack Payment Service
Handles all payment operations using Paystack API
Supports M-Pesa mobile money payments in Kenya
"""
import httpx
import hmac
import hashlib
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr

logger = logging.getLogger(__name__)


class PaystackConfig:
    """Paystack configuration"""
    def __init__(self, secret_key: str, public_key: str, environment: str = "live"):
        self.secret_key = secret_key
        self.public_key = public_key
        self.environment = environment
        self.base_url = "https://api.paystack.co"
        self.headers = {
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json"
        }
    
    def is_configured(self) -> bool:
        return bool(self.secret_key and self.public_key)


class SubaccountCreateRequest(BaseModel):
    """Request to create a subaccount for a hotspot owner"""
    business_name: str
    settlement_bank: str  # Bank code
    account_number: str
    percentage_charge: float  # Owner's percentage (platform keeps the rest)
    primary_contact_email: Optional[str] = None
    primary_contact_phone: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TransactionInitRequest(BaseModel):
    """Request to initialize a transaction"""
    email: EmailStr
    amount: float  # In KES
    reference: Optional[str] = None
    callback_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    subaccount_code: Optional[str] = None
    bearer: str = "account"  # 'account' or 'subaccount' for who bears charges


class MobileMoneyChargeRequest(BaseModel):
    """Request to charge via mobile money (M-Pesa)"""
    email: EmailStr
    amount: float  # In KES
    phone_number: str  # Format: 254XXXXXXXXX
    provider: str = "mpesa"
    reference: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    subaccount_code: Optional[str] = None  # For split payments to hotspot owner
    split_percentage: Optional[float] = None  # Owner's percentage of the transaction


class PaystackService:
    """
    Paystack Payment Service for CAIWAVE
    
    Handles:
    - Transaction initialization
    - M-Pesa mobile money charges
    - Transaction verification
    - Subaccount management for hotspot owners
    - Webhook signature verification
    """
    
    def __init__(self, config: PaystackConfig):
        self.config = config
        self.base_url = config.base_url
        self.headers = config.headers
    
    def is_configured(self) -> bool:
        return self.config.is_configured()
    
    def _convert_to_kobo(self, amount_kes: float) -> int:
        """Convert KES to kobo (smallest unit)"""
        return int(round(amount_kes * 100))
    
    def _convert_from_kobo(self, amount_kobo: int) -> float:
        """Convert kobo to KES"""
        return amount_kobo / 100
    
    async def initialize_transaction(self, request: TransactionInitRequest) -> Dict[str, Any]:
        """
        Initialize a transaction - returns authorization URL for payment
        
        For M-Pesa payments, use channels=["mobile_money"]
        """
        if not self.is_configured():
            return {"status": False, "message": "Paystack not configured"}
        
        payload = {
            "email": request.email,
            "amount": self._convert_to_kobo(request.amount),
            "currency": "KES",
            "channels": ["mobile_money", "card", "bank"],  # Allow multiple channels
            "metadata": request.metadata or {}
        }
        
        if request.reference:
            payload["reference"] = request.reference
        
        if request.callback_url:
            payload["callback_url"] = request.callback_url
        
        if request.subaccount_code:
            payload["subaccount"] = request.subaccount_code
            payload["bearer"] = request.bearer
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/transaction/initialize",
                    json=payload,
                    headers=self.headers
                )
                result = response.json()
                logger.info(f"Transaction init response: {result}")
                return result
        except Exception as e:
            logger.error(f"Transaction init error: {e}")
            return {"status": False, "message": str(e)}
    
    async def charge_mobile_money(self, request: MobileMoneyChargeRequest) -> Dict[str, Any]:
        """
        Charge customer via M-Pesa mobile money
        This initiates an STK Push to the customer's phone
        
        For Kenya M-Pesa, phone must be in E.164 format: +254XXXXXXXXX
        """
        if not self.is_configured():
            return {"status": False, "message": "Paystack not configured"}
        
        # Format phone number to E.164 format (+254XXXXXXXXX)
        phone = request.phone_number.replace(" ", "").replace("-", "")
        if phone.startswith("+"):
            phone = phone  # Already has +
        elif phone.startswith("254"):
            phone = "+" + phone
        elif phone.startswith("0"):
            phone = "+254" + phone[1:]
        else:
            phone = "+254" + phone
        
        # Paystack charge API structure for mobile money
        payload = {
            "email": request.email,
            "amount": self._convert_to_kobo(request.amount),
            "currency": "KES",
            "channels": ["mobile_money"],
            "mobile_money": {
                "phone": phone,
                "provider": request.provider  # "mpesa" for Kenya
            },
            "metadata": request.metadata or {}
        }
        
        if request.reference:
            payload["reference"] = request.reference
        
        # Add subaccount for split payment to hotspot owner
        if request.subaccount_code:
            payload["subaccount"] = request.subaccount_code
            # Bearer determines who pays the transaction fees
            # "subaccount" means the subaccount (owner) bears the fees from their share
            payload["bearer"] = "subaccount"
            logger.info(f"Split payment enabled for subaccount: {request.subaccount_code}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/charge",
                    json=payload,
                    headers=self.headers
                )
                result = response.json()
                logger.info(f"Mobile money charge response: {result}")
                
                # If Paystack needs phone verification, handle it
                if result.get("data", {}).get("status") == "send_phone":
                    # Submit phone for verification
                    submit_response = await client.post(
                        f"{self.base_url}/charge/submit_phone",
                        json={
                            "phone": phone,
                            "reference": result["data"]["reference"]
                        },
                        headers=self.headers
                    )
                    result = submit_response.json()
                    logger.info(f"Phone submission response: {result}")
                
                return result
        except Exception as e:
            logger.error(f"Mobile money charge error: {e}")
            return {"status": False, "message": str(e)}
    
    async def verify_transaction(self, reference: str) -> Dict[str, Any]:
        """Verify a transaction by reference"""
        if not self.is_configured():
            return {"status": False, "message": "Paystack not configured"}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/transaction/verify/{reference}",
                    headers=self.headers
                )
                result = response.json()
                logger.info(f"Transaction verify response: {result}")
                return result
        except Exception as e:
            logger.error(f"Transaction verify error: {e}")
            return {"status": False, "message": str(e)}
    
    async def create_subaccount(self, request: SubaccountCreateRequest) -> Dict[str, Any]:
        """
        Create a subaccount for a hotspot owner
        This enables automatic revenue splitting
        """
        if not self.is_configured():
            return {"status": False, "message": "Paystack not configured"}
        
        payload = {
            "business_name": request.business_name,
            "settlement_bank": request.settlement_bank,
            "account_number": request.account_number,
            "percentage_charge": request.percentage_charge,
        }
        
        if request.primary_contact_email:
            payload["primary_contact_email"] = request.primary_contact_email
        if request.primary_contact_phone:
            payload["primary_contact_phone"] = request.primary_contact_phone
        if request.metadata:
            payload["metadata"] = request.metadata
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/subaccount",
                    json=payload,
                    headers=self.headers
                )
                result = response.json()
                logger.info(f"Subaccount create response: {result}")
                return result
        except Exception as e:
            logger.error(f"Subaccount create error: {e}")
            return {"status": False, "message": str(e)}
    
    async def list_banks(self, country: str = "kenya") -> Dict[str, Any]:
        """List available banks for subaccount creation"""
        if not self.is_configured():
            return {"status": False, "message": "Paystack not configured"}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/bank?country={country}",
                    headers=self.headers
                )
                return response.json()
        except Exception as e:
            logger.error(f"List banks error: {e}")
            return {"status": False, "message": str(e)}
    
    async def fetch_subaccount(self, id_or_code: str) -> Dict[str, Any]:
        """Fetch subaccount details"""
        if not self.is_configured():
            return {"status": False, "message": "Paystack not configured"}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/subaccount/{id_or_code}",
                    headers=self.headers
                )
                return response.json()
        except Exception as e:
            logger.error(f"Fetch subaccount error: {e}")
            return {"status": False, "message": str(e)}
    
    async def update_subaccount(self, id_or_code: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update subaccount details"""
        if not self.is_configured():
            return {"status": False, "message": "Paystack not configured"}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(
                    f"{self.base_url}/subaccount/{id_or_code}",
                    json=updates,
                    headers=self.headers
                )
                return response.json()
        except Exception as e:
            logger.error(f"Update subaccount error: {e}")
            return {"status": False, "message": str(e)}
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature using HMAC-SHA512
        """
        if not self.config.secret_key:
            return False
        
        computed = hmac.new(
            self.config.secret_key.encode(),
            payload,
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(computed, signature)
    
    async def get_transaction(self, id_or_reference: str) -> Dict[str, Any]:
        """Get transaction details by ID or reference"""
        if not self.is_configured():
            return {"status": False, "message": "Paystack not configured"}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/transaction/{id_or_reference}",
                    headers=self.headers
                )
                return response.json()
        except Exception as e:
            logger.error(f"Get transaction error: {e}")
            return {"status": False, "message": str(e)}
    
    async def list_transactions(
        self,
        page: int = 1,
        per_page: int = 50,
        status: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """List transactions with optional filters"""
        if not self.is_configured():
            return {"status": False, "message": "Paystack not configured"}
        
        params = {"perPage": per_page, "page": page}
        if status:
            params["status"] = status
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/transaction",
                    params=params,
                    headers=self.headers
                )
                return response.json()
        except Exception as e:
            logger.error(f"List transactions error: {e}")
            return {"status": False, "message": str(e)}


# Kenya Banks for Paystack (common ones)
KENYA_BANKS = [
    {"code": "01", "name": "Kenya Commercial Bank"},
    {"code": "02", "name": "Standard Chartered Bank Kenya"},
    {"code": "03", "name": "Barclays Bank of Kenya"},
    {"code": "07", "name": "Commercial Bank of Africa"},
    {"code": "11", "name": "Co-operative Bank of Kenya"},
    {"code": "12", "name": "National Bank of Kenya"},
    {"code": "14", "name": "Oriental Commercial Bank"},
    {"code": "16", "name": "Citibank N.A Kenya"},
    {"code": "18", "name": "Middle East Bank Kenya"},
    {"code": "19", "name": "Bank of Africa Kenya"},
    {"code": "23", "name": "Consolidated Bank of Kenya"},
    {"code": "25", "name": "Credit Bank"},
    {"code": "31", "name": "CFC Stanbic Bank"},
    {"code": "35", "name": "African Banking Corporation"},
    {"code": "39", "name": "Imperial Bank Kenya"},
    {"code": "41", "name": "NIC Bank"},
    {"code": "43", "name": "Giro Commercial Bank"},
    {"code": "49", "name": "Equatorial Commercial Bank"},
    {"code": "51", "name": "Development Bank of Kenya"},
    {"code": "54", "name": "Fidelity Commercial Bank"},
    {"code": "55", "name": "Guardian Bank"},
    {"code": "57", "name": "I&M Bank"},
    {"code": "61", "name": "Housing Finance Company of Kenya"},
    {"code": "63", "name": "Diamond Trust Bank Kenya"},
    {"code": "66", "name": "K-Rep Bank"},
    {"code": "68", "name": "Equity Bank Kenya"},
    {"code": "70", "name": "Family Bank"},
    {"code": "72", "name": "Gulf African Bank"},
    {"code": "74", "name": "First Community Bank"},
    {"code": "75", "name": "Jamii Bora Bank"},
    {"code": "76", "name": "Sidian Bank"},
]
