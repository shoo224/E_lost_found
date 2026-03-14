# user.py - Pydantic schemas for users and auth tokens

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: str
    enrollment_number: Optional[str] = None
    role: str = "student"


class UserCreate(BaseModel):
    """Used when creating a user after OTP verify (email or enrollment)."""
    email: Optional[EmailStr] = None
    enrollment_number: Optional[str] = None
    # At least one of email or enrollment_number required for login


class UserInDB(UserBase):
    """User as stored in MongoDB (includes password_hash)."""
    id: Optional[str] = None
    password_hash: Optional[str] = None
    is_verified: bool = False
    created_at: datetime = None
    updated_at: datetime = None

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """User data returned to frontend (no password)."""
    id: str
    email: Optional[str] = None
    enrollment_number: Optional[str] = None
    role: str
    is_verified: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response after login."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    """Payload inside JWT (sub = user id, email, role)."""
    sub: str
    email: Optional[str] = None
    role: str = "student"
    exp: Optional[datetime] = None
