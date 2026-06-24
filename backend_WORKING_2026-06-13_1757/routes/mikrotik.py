from backend.services.mikrotik_builder import build_mikrotik_script

from backend.services.mikrotik_builder import build_mikrotik_script
from fastapi import APIRouter
from backend.schemas.mikrotik import MikroTikProvisionRequest
from backend.services.mikrotik_provisioning import provision_router

mikrotik_router = APIRouter(prefix="/mikrotik", tags=["MikroTik"])


@mikrotik_router.post("/generate")

def generate_script(payload: MikroTikProvisionRequest):
    result = provision_router(payload)

    if result["status"] != "success":
        return {
            "status": "error",
            "message": result["message"],
            "script": None
        }

    script = build_mikrotik_script(result["router"])

    return {
        "status": "success",
        "script": script
    }
