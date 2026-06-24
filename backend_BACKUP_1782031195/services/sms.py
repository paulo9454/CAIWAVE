"""
CAIWAVE SMS Service
Integration with Africa's Talking and Centipid SMS providers.
"""
import logging
import httpx

from ..config import SMS_PROVIDER, SMS_API_KEY, SMS_USERNAME, SMS_SENDER_ID


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


# Singleton instance
sms_service = SMSService()
