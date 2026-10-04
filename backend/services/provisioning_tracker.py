import hashlib
from datetime import datetime

from backend.services.provisioning_repository import ProvisioningRepository


def hash_script(script: str):
    return hashlib.sha256(script.encode()).hexdigest()


async def log_provisioning(
    router: dict,
    script: str,
    status="generated",
    error: str | None = None,
):
    now = datetime.utcnow()

    record = {
        "router_id": router.get("id"),
        "router_name": router.get("name", "unknown"),
        "owner_id": router.get("owner_id"),
        "hotspot_id": router.get("hotspot_id"),
        "nas_identifier": router["nas_identifier"],
        "status": status,
        "script_hash": hash_script(script),
        "script": script,
        "created_at": now,
        "updated_at": now,
    }

    if error:
        record["error"] = error

    await ProvisioningRepository.insert(record)

    return record
