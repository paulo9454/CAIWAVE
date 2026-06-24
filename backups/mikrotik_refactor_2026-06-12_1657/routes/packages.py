"""
CAIWAVE Package Routes
Handles WiFi packages management.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from ..database import db
from ..models import PackageBase, Package
from ..utils.auth import require_admin

router = APIRouter(prefix="/packages", tags=["Packages"])


@router.get("/", response_model=List[Package])
async def get_packages(active_only: bool = True):
    """Get all WiFi packages."""
    query = {"is_active": True} if active_only else {}
    packages = await db.packages.find(query, {"_id": 0}).sort("price", 1).to_list(100)
    return packages


@router.get("/{package_id}", response_model=Package)
async def get_package(package_id: str):
    """Get a specific package."""
    package = await db.packages.find_one({"id": package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    return package


@router.post("/", response_model=Package)
async def create_package(
    package_data: PackageBase,
    user: dict = Depends(require_admin)
):
    """Create a new package (Admin only)."""
    package = Package(**package_data.model_dump())
    package_dict = package.model_dump()
    package_dict["created_at"] = package_dict["created_at"].isoformat()
    await db.packages.insert_one(package_dict)
    return package


@router.put("/{package_id}", response_model=Package)
async def update_package(
    package_id: str,
    package_data: PackageBase,
    user: dict = Depends(require_admin)
):
    """Update a package (Admin only)."""
    result = await db.packages.find_one_and_update(
        {"id": package_id},
        {"$set": package_data.model_dump()},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Package not found")
    result.pop("_id", None)
    return result
