from fastapi import APIRouter
from backend.core.db import db

status_router = APIRouter(prefix="/mikrotik/provisioning", tags=["Provisioning Status"])


@status_router.get("/{nas_id}")
async def get_provisioning_status(nas_id: str):
    doc = await db.provisioning_logs.find_one(
        {"nas_id": nas_id},
        sort=[("created_at", -1)]
    )

    if not doc:
        return {
            "status": "not_found",
            "nas_id": nas_id,
            "message": "No provisioning record found"
        }

    doc["_id"] = str(doc["_id"])

    return {
        "status": "success",
        "data": doc
    }
