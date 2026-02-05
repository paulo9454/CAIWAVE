"""
CAIWAVE Location Routes
Handles Kenya counties and constituencies data.
"""
from fastapi import APIRouter
from typing import Optional

from ..utils.locations import get_all_counties, get_constituencies, get_all_constituencies

router = APIRouter(prefix="/locations", tags=["Locations"])


@router.get("/counties")
async def list_counties():
    """Get all Kenya counties."""
    return {"counties": get_all_counties()}


@router.get("/constituencies")
async def list_constituencies(county: Optional[str] = None):
    """Get constituencies, optionally filtered by county."""
    if county:
        return {"constituencies": get_constituencies(county)}
    return {"constituencies": get_all_constituencies()}
