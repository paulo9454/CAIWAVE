from fastapi import APIRouter, HTTPException

mikrotik_router = APIRouter(prefix="/mikrotik", tags=["MikroTik"])


@mikrotik_router.post("/generate", status_code=410)
async def generate_script():
    raise HTTPException(
        status_code=410,
        detail=(
            "The legacy MikroTik generation endpoint has been retired. "
            "Use the CAIWAVE MikroTik onboarding flow so the router can be "
            "discovered and its topology verified before provisioning."
        ),
    )
