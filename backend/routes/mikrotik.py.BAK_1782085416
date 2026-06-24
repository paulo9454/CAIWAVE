import asyncio
from fastapi import APIRouter, HTTPException

from schemas.mikrotik import MikroTikProvisionRequest
from services.mikrotik_provisioning import provision_router
from services.router_provisioning_dispatcher import dispatch_router_provisioning

mikrotik_router = APIRouter(prefix="/mikrotik", tags=["MikroTik"])


@mikrotik_router.post("/generate")
async def generate_script(payload: MikroTikProvisionRequest):

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




