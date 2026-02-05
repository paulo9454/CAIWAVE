"""
CAIWAVE Package Models
Pydantic models for WiFi packages.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, timezone
import uuid


class PackageBase(BaseModel):
    name: str
    price: float  # KES
    duration_minutes: int
    speed_mbps: float = 10.0
    data_limit_mb: Optional[int] = None  # None = unlimited
    description: Optional[str] = None
    is_active: bool = True


class Package(PackageBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
