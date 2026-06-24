from datetime import datetime
import uuid


class ProvisioningJobService:
    def create_job(self, router_id: str, payload: dict):
        return {
            "job_id": str(uuid.uuid4()),
            "router_id": router_id,
            "status": "queued",
            "payload": payload,
            "created_at": datetime.utcnow().isoformat(),
        }


job_service = ProvisioningJobService()
