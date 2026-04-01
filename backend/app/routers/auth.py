# auth.py - JWT + Email OTP authentication
# Step 1: Send OTP to email (or enrollment lookup). Step 2: Verify OTP and get JWT.

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.database import users_collection
from app.utils.security import create_access_token
from app.services.otp import generate_otp, store_otp, verify_otp
from app.services.email import send_otp_email
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


class OtpSendRequest(BaseModel):
    """Request OTP for login. Use email (for admin/student) or enrollment_number (for student)."""
    email: Optional[EmailStr] = None
    enrollment_number: Optional[str] = None


class OtpVerifyRequest(BaseModel):
    """Verify OTP and get JWT."""
    email: Optional[EmailStr] = None
    enrollment_number: Optional[str] = None
    otp: str


def _get_user_key(email: Optional[str], enrollment_number: Optional[str]) -> str:
    """Key for OTP and user lookup: prefer email, else enrollment."""
    if email:
        return email.lower().strip()
    if enrollment_number:
        return enrollment_number.strip().lower()
    raise HTTPException(status_code=400, detail="Provide email or enrollment_number")


@router.post("/otp/send")
def send_otp(req: OtpSendRequest):
    """
    Step 1: Send OTP to user's email.
    If enrollment_number provided, we need to find that user's email in DB to send OTP;
    if not found, reject (student must have reported something first) or use a shared college email pattern.
    For simplicity: we accept email only for OTP send (admin and students with email).
    Enrollment-based: we could store enrollment -> email in users and send to that email.
    """
    key = _get_user_key(req.email, req.enrollment_number)
    # If key is enrollment, we might not have email yet - so for "student found" we verify enrollment
    # by sending OTP to a placeholder or we require email in users. Here we require email for sending OTP.
    if req.enrollment_number and not req.email:
        # Look up email by enrollment in users
        user = users_collection().find_one({"enrollment_number": req.enrollment_number.strip().lower()})
        if user and user.get("email"):
            email_to_send = user["email"]
        else:
            # New student: we don't have email. Require email in request for OTP.
            raise HTTPException(
                status_code=400,
                detail="Provide email to receive OTP, or register with enrollment first",
            )
    else:
        email_to_send = key if req.email else None
    if not email_to_send:
        raise HTTPException(status_code=400, detail="Email required to send OTP")

    otp = generate_otp(6)
    store_otp(key, otp, purpose="login")
    sent = send_otp_email(email_to_send, otp)
    if sent:
        return {"message": "OTP sent to your email"}
    # Local/dev fallback: if email provider is not configured, return OTP in response.
    return {
        "message": "Email is not configured on server. Using dev OTP fallback.",
        "dev_otp": otp,
    }


@router.post("/otp/verify", response_model=dict)
def verify_otp_and_login(req: OtpVerifyRequest):
    """
    Step 2: Verify OTP. If valid, create or get user and return JWT + user.
    """
    key = _get_user_key(req.email, req.enrollment_number)
    if not verify_otp(key, req.otp, purpose="login"):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    col = users_collection()
    # Find user by email or enrollment
    if req.email:
        user = col.find_one({"email": req.email.lower().strip()})
    else:
        user = col.find_one({"enrollment_number": req.enrollment_number.strip().lower()})

    from datetime import datetime
    from bson import ObjectId

    if not user:
        # Create new user
        doc = {
            "email": req.email.lower().strip() if req.email else None,
            "enrollment_number": req.enrollment_number.strip().lower() if req.enrollment_number else None,
            "role": "admin" if (req.email and req.email.lower() in settings.admin_emails_list) else "student",
            "is_verified": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        ins = col.insert_one(doc)
        user_id = str(ins.inserted_id)
        user = col.find_one({"_id": ins.inserted_id})
    else:
        user_id = str(user["_id"])
        col.update_one(
            {"_id": user["_id"]},
            {"$set": {"is_verified": True, "updated_at": datetime.utcnow()}},
        )
        user = col.find_one({"_id": user["_id"]})

    role = user.get("role", "student")
    email = user.get("email")
    enrollment = user.get("enrollment_number")
    token = create_access_token(sub=user_id, email=email, role=role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": email,
            "enrollment_number": enrollment,
            "role": role,
            "is_verified": True,
        },
    }
