from datetime import datetime, timezone
import uuid


def analytics_event(
    event_type: str,
    hotspot_id: str | None = None,
    user_mac: str | None = None,
    session_id: str | None = None,
    campaign_id: str | None = None,
    ad_id: str | None = None,
    notification_id: str | None = None,
    extra: dict | None = None,
):
    return {
        "id": str(uuid.uuid4()),
        "event": event_type,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "hotspot_id": hotspot_id,
        "user_mac": user_mac,
        "session_id": session_id,
        "campaign_id": campaign_id,
        "ad_id": ad_id,
        "notification_id": notification_id,
        "extra": extra or {},
    }
