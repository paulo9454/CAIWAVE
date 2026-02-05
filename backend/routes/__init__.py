"""
CAIWAVE Routes Package
Export all route modules.
"""
from .auth import router as auth_router
from .packages import router as packages_router
from .locations import router as locations_router

__all__ = [
    "auth_router",
    "packages_router",
    "locations_router"
]
