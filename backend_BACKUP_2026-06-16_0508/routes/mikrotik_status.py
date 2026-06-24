from fastapi import APIRouter, HTTPException
from backend.services.provisioning_status_service import get_provisioning_status

router = APIRouter(prefix="/mikrotik", tags=["MikroTik Status"])


@router.get("/provisioning/{nas_id}")
async def provisioning_status(nas_id: str):
    result = await get_provisioning_status(nas_id)

    if result["latest_status"] == "not_found":
        raise HTTPException(status_code=404, detail="Router provisioning not found")

    return result
