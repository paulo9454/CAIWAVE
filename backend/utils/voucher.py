"""
CAIWAVE Voucher & RADIUS Utilities
Helper functions for voucher generation and RADIUS credentials.
"""
import uuid


def generate_voucher_code() -> str:
    """Generate a unique voucher code."""
    return uuid.uuid4().hex[:8].upper()


def generate_radius_credentials(prefix: str = "") -> tuple:
    """Generate RADIUS username and password."""
    username = f"{prefix}{uuid.uuid4().hex[:6]}"
    password = uuid.uuid4().hex[:8]
    return username, password
