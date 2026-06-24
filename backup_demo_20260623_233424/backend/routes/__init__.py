from fastapi import APIRouter

from .packages import router as packages_router
from .locations import router as locations_router
from .mikrotik import mikrotik_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(packages_router)
api_router.include_router(locations_router)

api_router.include_router(mikrotik_router)
