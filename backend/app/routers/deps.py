# deps.py - Shared dependencies (current user, admin only)

from typing import Optional
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.database import users_collection
from app.utils.security import decode_access_token

security = HTTPBearer(auto_error=False)


def get_current_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """Extract and validate JWT; return user id (sub)."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return str(payload["sub"])


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    """Return full user document from DB."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    from bson import ObjectId
    sub = payload["sub"]
    try:
        uid = ObjectId(sub)
    except Exception:
        uid = sub
    user = users_collection().find_one({"_id": uid})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Allow only admin users."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user
