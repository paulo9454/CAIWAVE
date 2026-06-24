from datetime import datetime
from typing import Optional, Dict, Any


class ProvisioningRun:
    """
    Tracks full lifecycle of a MikroTik provisioning event
    """

    def __init__(self, router_id: str):
        self.router_id = router_id
        self.status = "pending"
        self.started_at = datetime.utcnow()
        self.finished_at: Optional[datetime] = None
        self.logs: list[str] = []
        self.error: Optional[str] = None
        self.metadata: Dict[str, Any] = {}

    def log(self, message: str):
        self.logs.append(f"[{datetime.utcnow().isoformat()}] {message}")

    def mark_success(self):
        self.status = "active"
        self.finished_at = datetime.utcnow()

    def mark_failed(self, error: str):
        self.status = "failed"
        self.error = error
        self.finished_at = datetime.utcnow()
