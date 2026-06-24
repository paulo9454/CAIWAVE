from datetime import datetime


class ProvisioningRecord:
    """
    Persistent provisioning history record
    """

    def __init__(
        self,
        router_id: str,
        status: str,
        script: str = "",
        logs: list = None,
        error: str = None,
    ):
        self.router_id = router_id
        self.status = status
        self.script = script
        self.logs = logs or []
        self.error = error
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self):
        return {
            "router_id": self.router_id,
            "status": self.status,
            "script": self.script,
            "logs": self.logs,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
