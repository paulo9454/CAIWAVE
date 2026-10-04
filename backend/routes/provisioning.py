from fastapi import APIRouter
from backend.services.provisioning_repository import repository

router = APIRouter(prefix="/provisioning", tags=["Provisioning"])


@router.get("/runs")
async def list_runs():
    return await repository.list_all()


@router.get("/runs/{router_id}")
async def get_run(router_id: str):
    result = await repository.get(router_id)

    if not result:
        return {
            "status": "not_found",
            "data": None,
        }

    return {
        "status": "success",
        "data": result,
    }
