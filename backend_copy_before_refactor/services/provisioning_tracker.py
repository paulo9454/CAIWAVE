import hashlib
from datetime import datetime


def hash_script(script: str):
    return hashlib.sha256(script.encode()).hexdigest()


async def log_provisioning(router: dict, script: str, status="generated"):
    record = {
        "router_name": router.get("name", "unknown"),
        "nas_identifier": router["nas_identifier"],
        "status": status,
        "script_hash": hash_script(script),
        "script": script,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    await ProvisioningRepository.collection().insert_one(record)
    return record
