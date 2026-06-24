from fastapi import APIRouter, HTTPException

from backend.schemas.mikrotik import MikroTikProvisionRequest
from backend.services.mikrotik_provisioning import provision_router
from backend.services.router_provisioning_dispatcher import dispatch_router_provisioning

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




