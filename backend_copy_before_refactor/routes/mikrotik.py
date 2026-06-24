from fastapi import APIRouter, HTTPException

from backend.schemas.mikrotik import MikroTikProvisionRequest
from backend.services.mikrotik_provisioning import provision_router
from backend.services.router_provisioning_dispatcher import dispatch_router_provisioning
from backend.core.db import db

mikrotik_router = APIRouter(prefix="/mikrotik", tags=["MikroTik"])


@mikrotik_router.post("/generate")
def generate_script(payload: MikroTikProvisionRequest):

    result = provision_router(payload)

    if result["status"] != "success":
        return {
            "status": "error",
            "message": result.get("message", "Provisioning failed"),
            "script": None
        }

    response = dispatch_router_provisioning(
        result["router"],
        mode="script"
    )

    return {
        "status": "success",
        "script": response["script"]
    }



@mikrotik_router.get("/provisioning/{nas_id}")
async def provisioning_status(nas_id: str):

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

