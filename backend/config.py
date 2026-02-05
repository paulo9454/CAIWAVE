"""
CAIWAVE Configuration Management
All environment variables and constants are centralized here.
"""
from pathlib import Path
from dotenv import load_dotenv
import os

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Upload directories
UPLOAD_DIR = ROOT_DIR / "uploads" / "ads"
UPLOAD_DIR_IMAGES = UPLOAD_DIR / "images"
UPLOAD_DIR_VIDEOS = UPLOAD_DIR / "videos"
UPLOAD_DIR_IMAGES.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR_VIDEOS.mkdir(parents=True, exist_ok=True)

# Media validation constants
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_VIDEO_SIZE = 20 * 1024 * 1024  # 20MB
MAX_VIDEO_DURATION = 15  # seconds
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]
ALLOWED_VIDEO_TYPES = ["video/mp4", "video/webm"]

# MongoDB connection
MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']

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
MPESA_ENV = os.environ.get('MPESA_ENV', 'sandbox')

# SMS Configuration
SMS_PROVIDER = os.environ.get('SMS_PROVIDER', 'africas_talking')
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

# Subscription Constants
SUBSCRIPTION_PRICE_KES = 500  # KES 500 per hotspot per month
TRIAL_DAYS = 14
GRACE_PERIOD_DAYS = 3  # Day 15-17
SUSPENSION_DAY = 18
