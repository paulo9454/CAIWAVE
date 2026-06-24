from fastapi import APIRouter
from services.demo.demo_mode import is_demo
from services.demo import mock_payments, mock_sessions

router = APIRouter(prefix="/demo", tags=["Demo"])

@router.post("/pay")
def demo_pay(data: dict):
    if is_demo():
        return mock_payments.simulate_payment(
            data.get("amount"),
            data.get("phone")
        )
    return {"error": "Not in demo mode"}

@router.post("/session")
def demo_session(data: dict):
    return mock_sessions.create_session(
        data.get("user_id"),
        data.get("package")
    )

@router.get("/status")
def system_status():
    return {
        "mode": "demo",
        "system": "CAIWAVE DEMO ACTIVE"
    }
