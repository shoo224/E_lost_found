# lost.py - Report lost item; OTP verify college email; upload image; run matcher

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import EmailStr
from bson import ObjectId

from app.database import lost_items_collection
from app.services.otp import store_otp, verify_otp, generate_otp
from app.services.email import send_otp_email
from app.services.s3 import upload_file_to_s3
from app.services.matcher import run_matching_for_lost_item

router = APIRouter(prefix="/lost", tags=["lost"])


@router.post("/otp/send")
def send_otp_for_lost(email: str):
    """Send OTP to college email before submitting lost item."""
    email = email.lower().strip()
    otp = generate_otp(6)
    store_otp(email, otp, purpose="verify_email")
    sent = send_otp_email(email, otp)
    if sent:
        return {"message": "OTP sent to your email"}
    return {
        "message": "Email is not configured on server. Using dev OTP fallback.",
        "dev_otp": otp,
    }


@router.post("/otp/verify")
def verify_otp_for_lost(email: str, otp: str):
    """Verify OTP for college email. Frontend can then allow submit."""
    email = email.lower().strip()
    if not verify_otp(email, otp, purpose="verify_email"):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    return {"message": "Verified"}


@router.post("")
def create_lost_item(
    name: str = Form(...),
    college_email: str = Form(...),
    where_lost: str = Form(...),
    when_lost: str = Form(...),
    item_name: str = Form(...),
    description: str = Form(...),
    image: Optional[UploadFile] = File(None),
):
    """
    Submit a lost item. College email should be OTP-verified on frontend.
    Optional image uploaded to S3.
    Run matching instantly after insert.
    """
    college_email = college_email.lower().strip()
    # Parse date; BSON needs datetime, not date
    try:
        when_lost_date = datetime.strptime(when_lost, "%Y-%m-%d").date()
        when_lost_dt = datetime.combine(when_lost_date, datetime.min.time())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    image_url = None
    if image and image.filename:
        content = image.file.read()
        content_type = image.content_type or "image/jpeg"
        image_url = upload_file_to_s3(content, content_type, "lost", image.filename)

    doc = {
        "name": name,
        "college_email": college_email,
        "where_lost": where_lost,
        "when_lost": when_lost_dt,
        "item_name": item_name,
        "description": description,
        "image_url": image_url,
        "status": "open",
        "matched_found_ids": [],
        "created_at": datetime.utcnow(),
    }
    col = lost_items_collection()
    ins = col.insert_one(doc)
    lost_id = str(ins.inserted_id)

    # Run matching instantly
    matched_found_ids = run_matching_for_lost_item(lost_id)

    return {
        "id": lost_id,
        "message": "Lost item reported",
        "matched_found_ids": matched_found_ids,
    }
