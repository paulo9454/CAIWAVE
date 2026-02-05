"""
CAIWAVE Authentication Routes
Handles user registration, login, and profile management.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import EmailStr
from datetime import datetime, timezone, timedelta
import uuid

from ..database import db
from ..models import UserCreate, UserLogin, User, UserResponse, UserRole
from ..utils.auth import (
    hash_password, verify_password, create_token, get_current_user
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=dict)
async def register(user_data: UserCreate):
    """Register a new user."""
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(**user_data.model_dump(exclude={"password"}))
    user_dict = user.model_dump()
    user_dict["password_hash"] = hash_password(user_data.password)
    user_dict["created_at"] = user_dict["created_at"].isoformat()
    
    await db.users.insert_one(user_dict)
    token = create_token(user.id, user.role.value)
    
    return {
        "token": token,
        "user": UserResponse(**user_dict).model_dump()
    }


@router.post("/login", response_model=dict)
async def login(credentials: UserLogin):
    """Login with email and password."""
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"], user["role"])
    return {
        "token": token,
        "user": UserResponse(**user).model_dump()
    }


@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    """Get current user profile."""
    return UserResponse(**user)


@router.post("/forgot-password")
async def forgot_password(email: EmailStr):
    """Request password reset."""
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a reset link will be sent"}
    
    # Generate reset token
    reset_token = str(uuid.uuid4())
    await db.password_resets.insert_one({
        "user_id": user["id"],
        "token": reset_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "used": False
    })
    
    # TODO: Send email with reset link
    return {"message": "If the email exists, a reset link will be sent"}
