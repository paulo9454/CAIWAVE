from backend.schemas.router import RouterSchema
from pydantic import ValidationError


def validate_router(raw_router: dict) -> RouterSchema:
    """
    HARD GATE:
    If router is invalid → STOP EVERYTHING.
    No fallback, no silent fixes.
    """

    try:
        return RouterSchema(**raw_router)
    except ValidationError as e:
        raise ValueError(f"INVALID ROUTER CONFIG: {e}")
