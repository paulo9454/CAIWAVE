from fastapi import APIRouter
from services.provisioning_repository import repository

router = APIRouter(prefix="/provisioning", tags=["Provisioning"])


@router.get("/runs")
def list_runs():
    return repository.list_all()


@router.get("/runs/{router_id}")
def get_run(router_id: str):
    return repository.get(router_id)
