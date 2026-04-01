# admin.py - Admin endpoints: password login, /me, etc.

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from app.routers.deps import require_admin
from app.database import users_collection
from app.utils.security import create_access_token
from app.config import settings

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminPasswordLogin(BaseModel):
    """Admin email + password login (no OTP, for admin panel only)."""
    email: EmailStr
    password: str


@router.post("/login-password")
def admin_login_password(body: AdminPasswordLogin):
    """
    Admin login using email + password (no OTP).
    Only emails in ADMIN_EMAILS can log in this way.
    """
    email = body.email.lower().strip()
    if email not in settings.admin_emails_list:
        raise HTTPException(status_code=401, detail="This email is not an admin.")

    if not settings.ADMIN_PANEL_PASSWORD:
        raise HTTPException(status_code=500, detail="Admin panel password is not configured on server.")

    if body.password != settings.ADMIN_PANEL_PASSWORD:
        raise HTTPException(status_code=401, detail="Incorrect admin password.")

    col = users_collection()
    user = col.find_one({"email": email})
    if not user:
        doc = {
            "email": email,
            "enrollment_number": None,
            "role": "admin",
            "is_verified": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        ins = col.insert_one(doc)
        user = col.find_one({"_id": ins.inserted_id})

    user_id = str(user["_id"])
    col.update_one(
        {"_id": user["_id"]},
        {"$set": {"role": "admin", "is_verified": True, "updated_at": datetime.utcnow()}},
    )

    token = create_access_token(sub=user_id, email=email, role="admin")
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": email,
            "enrollment_number": user.get("enrollment_number"),
            "role": "admin",
            "is_verified": True,
        },
    }


@router.post("/direct-login")
def admin_direct_login():
    """
    Direct admin login without password (for local/dev convenience).
    Uses the first email from ADMIN_EMAILS and returns an admin token.
    """
    col = users_collection()

    # Dev fallback: if ADMIN_EMAILS isn't configured, promote an existing user to admin.
    if not settings.admin_emails_list:
        user = col.find_one({})
        if not user:
            raise HTTPException(status_code=500, detail="No users exist to promote to admin.")
        email = user.get("email")
        user_id = str(user["_id"])
        col.update_one(
            {"_id": user["_id"]},
            {"$set": {"role": "admin", "is_verified": True, "updated_at": datetime.utcnow()}},
        )
        token = create_access_token(sub=user_id, email=email, role="admin")
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "email": email,
                "enrollment_number": user.get("enrollment_number"),
                "role": "admin",
                "is_verified": True,
            },
        }

    email = settings.admin_emails_list[0]
    user = col.find_one({"email": email})
    if not user:
        doc = {
            "email": email,
            "enrollment_number": None,
            "role": "admin",
            "is_verified": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        ins = col.insert_one(doc)
        user = col.find_one({"_id": ins.inserted_id})

    user_id = str(user["_id"])
    col.update_one(
        {"_id": user["_id"]},
        {"$set": {"role": "admin", "is_verified": True, "updated_at": datetime.utcnow()}},
    )

    token = create_access_token(sub=user_id, email=email, role="admin")
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": email,
            "enrollment_number": user.get("enrollment_number"),
            "role": "admin",
            "is_verified": True,
        },
    }


@router.get("/me")
def admin_me(admin: dict = Depends(require_admin)):
    """Return current admin user (for frontend)."""
    return {
        "id": str(admin["_id"]),
        "email": admin.get("email"),
        "role": admin.get("role"),
    }
