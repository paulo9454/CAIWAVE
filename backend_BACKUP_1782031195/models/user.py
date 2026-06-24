"""
CAIWAVE User Models
Pydantic models for user-related data.
"""
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, Dict
from datetime import datetime, timezone
import uuid
from .enums import UserRole


class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    role: UserRole = UserRole.END_USER


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    balance: float = 0.0
    notification_preferences: Dict[str, bool] = Field(default_factory=lambda: {
        "sms_enabled": True,
        "whatsapp_enabled": False,
        "email_enabled": True
    })


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    phone: Optional[str]
    role: UserRole
    is_active: bool
    balance: float
