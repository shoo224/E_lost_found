# otp.py - Generate, store, and verify OTP codes
# OTP is sent via email; we store in MongoDB with expiry

import random
import string
from datetime import datetime, timedelta

from app.config import settings
from app.database import otp_store_collection


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP (e.g. 6 digits)."""
    return "".join(random.choices(string.digits, k=length))


def store_otp(key: str, otp: str, purpose: str = "login") -> None:
    """
    Store OTP in DB. key = email or enrollment_number.
    purpose = "login" | "verify_email" | "verify_enrollment"
    """
    col = otp_store_collection()
    expires_at = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    col.update_one(
        {"key": key, "purpose": purpose},
        {"$set": {"otp": otp, "expires_at": expires_at, "created_at": datetime.utcnow()}},
        upsert=True,
    )


def verify_otp(key: str, otp: str, purpose: str = "login") -> bool:
    """Verify OTP for given key. Returns True if valid, False otherwise. Deletes OTP after use."""
    col = otp_store_collection()
    doc = col.find_one({"key": key, "purpose": purpose})
    if not doc:
        return False
    if doc["otp"] != otp:
        return False
    if doc["expires_at"] < datetime.utcnow():
        col.delete_one({"_id": doc["_id"]})
        return False
    col.delete_one({"_id": doc["_id"]})
    return True
