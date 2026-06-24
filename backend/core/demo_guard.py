from backend.core.demo_mode import DEMO_MODE
from fastapi import HTTPException

def require_not_demo(action: str = "this action"):
    """
    Blocks destructive actions in demo mode.
    Safe to import everywhere.
    """
    if DEMO_MODE:
        raise HTTPException(
            status_code=403,
            detail=f"Demo mode active: {action} is disabled"
        )
