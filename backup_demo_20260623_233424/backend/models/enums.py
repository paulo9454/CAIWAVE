"""
CAIWAVE Enumerations
All enum types used across the application.
"""
from enum import Enum


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    HOTSPOT_OWNER = "hotspot_owner"
    ADVERTISER = "advertiser"
    END_USER = "end_user"


class AdType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"


class AdStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAYMENT_ENABLED = "payment_enabled"
    PAID = "paid"
    ACTIVE = "active"
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


class AdCoverageScope(str, Enum):
    CONSTITUENCY = "constituency"
    COUNTY = "county"
    NATIONAL = "national"


class AdPackageStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    TRIAL = "trial"
    UNPAID = "unpaid"
    PAID = "paid"
    OVERDUE = "overdue"


class SubscriptionStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    GRACE_PERIOD = "grace_period"  # Day 15-17
    SUSPENDED = "suspended"  # Day 18+
