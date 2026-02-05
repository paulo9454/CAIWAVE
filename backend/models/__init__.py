"""
CAIWAVE Models Package
Export all models for easy importing.
"""
from .enums import (
    UserRole, AdType, AdStatus, SessionStatus, PaymentStatus, PaymentMethod,
    HotspotStatus, NotificationType, CampaignStatus, StreamAccessType,
    SubsidizedUptimeStatus, AdCoverageScope, AdPackageStatus, InvoiceStatus,
    SubscriptionStatus
)
from .user import UserBase, UserCreate, UserLogin, User, UserResponse
from .package import PackageBase, Package
from .hotspot import MikroTikConfig, HotspotBase, HotspotCreate, Hotspot
from .invoice import Invoice, InvoiceCreate, InvoicePaymentRequest
from .session import SessionBase, SessionCreate, Session
from .payment import PaymentBase, PaymentCreate, Payment, MPesaSTKPushRequest, MPesaSTKCallback
from .ad import (
    AdPackage, AdPackageCreate, AdPackageUpdate, AdTargeting, Ad, AdApproval, AdPaymentRequest
)
from .voucher import VoucherBase, Voucher
from .campaign import (
    CampaignBase, CampaignCreate, Campaign, StreamBase, StreamCreate, Stream,
    SubsidizedUptimeBase, SubsidizedUptimeCreate, SubsidizedUptime
)
from .settings import (
    NotificationRequest, RevenueConfig, DynamicRevenue, SystemSettings, MarketplaceItem
)

__all__ = [
    # Enums
    "UserRole", "AdType", "AdStatus", "SessionStatus", "PaymentStatus", "PaymentMethod",
    "HotspotStatus", "NotificationType", "CampaignStatus", "StreamAccessType",
    "SubsidizedUptimeStatus", "AdCoverageScope", "AdPackageStatus", "InvoiceStatus",
    "SubscriptionStatus",
    # User models
    "UserBase", "UserCreate", "UserLogin", "User", "UserResponse",
    # Package models
    "PackageBase", "Package",
    # Hotspot models
    "MikroTikConfig", "HotspotBase", "HotspotCreate", "Hotspot",
    # Invoice models
    "Invoice", "InvoiceCreate", "InvoicePaymentRequest",
    # Session models
    "SessionBase", "SessionCreate", "Session",
    # Payment models
    "PaymentBase", "PaymentCreate", "Payment", "MPesaSTKPushRequest", "MPesaSTKCallback",
    # Ad models
    "AdPackage", "AdPackageCreate", "AdPackageUpdate", "AdTargeting", "Ad", "AdApproval", "AdPaymentRequest",
    # Voucher models
    "VoucherBase", "Voucher",
    # Campaign models
    "CampaignBase", "CampaignCreate", "Campaign", "StreamBase", "StreamCreate", "Stream",
    "SubsidizedUptimeBase", "SubsidizedUptimeCreate", "SubsidizedUptime",
    # Settings models
    "NotificationRequest", "RevenueConfig", "DynamicRevenue", "SystemSettings", "MarketplaceItem"
]
