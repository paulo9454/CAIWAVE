from enum import Enum

class HotspotStatus(str, Enum):
    PENDING_SETUP = "pending_setup"
    ACTIVE = "active"
    SUSPENDED = "suspended"


def get_hotspot_status(hotspot: dict) -> str:
    return hotspot.get("status") or HotspotStatus.PENDING_SETUP.value


def is_hotspot_active(hotspot: dict) -> bool:
    return get_hotspot_status(hotspot) == HotspotStatus.ACTIVE.value
