"""
CAIWAVE Notification Service
Unified notification handling for SMS, WhatsApp, and Email.
"""
from .sms import sms_service
from .whatsapp import whatsapp_service


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


# Singleton instance
notification_service = NotificationService()
