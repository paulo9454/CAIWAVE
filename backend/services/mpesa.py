"""
CAIWAVE M-Pesa Daraja API Service
Real integration with Safaricom M-Pesa.
"""
import logging
import base64
from datetime import datetime
import httpx
from fastapi import HTTPException

from ..config import (
    MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET, MPESA_SHORTCODE,
    MPESA_PASSKEY, MPESA_CALLBACK_URL, MPESA_ENV
)


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


# Singleton instance
mpesa_service = MPesaService()
