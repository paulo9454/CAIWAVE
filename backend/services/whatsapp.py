"""
CAIWAVE WhatsApp Service
Integration with Twilio WhatsApp API.
"""
import logging
import base64
import httpx

from ..config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER


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


# Singleton instance
whatsapp_service = WhatsAppService()
