# found.py - Report found item (student: OTP verify enrollment; admin: add found)

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from bson import ObjectId

from app.database import found_items_collection, users_collection
from app.routers.deps import get_current_user, require_admin
from app.services.otp import store_otp, verify_otp, generate_otp
from app.services.email import send_otp_email
from app.services.s3 import upload_file_to_s3
from app.services.matcher import run_matching_for_found_item

router = APIRouter(prefix="/found", tags=["found"])


@router.post("/student/otp/send")
def send_otp_for_student_found(email: str):
    """
    Student found: send OTP to email (student provides email to receive OTP).
    We store OTP keyed by email; on verify we can associate enrollment.
    """
    email = email.lower().strip()
    otp = generate_otp(6)
    store_otp(email, otp, purpose="verify_enrollment")
    send_otp_email(email, otp)
    return {"message": "OTP sent to your email"}


@router.post("/student/otp/verify")
def verify_otp_for_student_found(email: str, otp: str):
    """Verify OTP so student can submit found item."""
    email = email.lower().strip()
    if not verify_otp(email, otp, purpose="verify_enrollment"):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    return {"message": "Verified"}


@router.post("/student")
def create_found_item_student(
    enrollment_number: str = Form(...),
    email: str = Form(...),  # email used for OTP
    item_name: str = Form(...),
    date_found: str = Form(...),
    time_found: Optional[str] = Form(None),
    description: str = Form(...),
    location: str = Form(...),
    image: Optional[UploadFile] = File(None),
):
    """
    Student submits a found item. Email should be OTP-verified.
    Run matching instantly after insert.
    """
    try:
        date_found_date = datetime.strptime(date_found, "%Y-%m-%d").date()
        date_found_dt = datetime.combine(date_found_date, datetime.min.time())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date. Use YYYY-MM-DD")

    image_url = None
    if image and image.filename:
        content = image.file.read()
        content_type = image.content_type or "image/jpeg"
        image_url = upload_file_to_s3(content, content_type, "found", image.filename)

    doc = {
        "item_name": item_name,
        "date_found": date_found_dt,
        "time_found": time_found,
        "description": description,
        "location": location,
        "image_url": image_url,
        "submitted_by": "student",
        "enrollment_number": enrollment_number.strip().lower(),
        "status": "open",
        "matched_lost_ids": [],
        "created_at": datetime.utcnow(),
    }
    col = found_items_collection()
    ins = col.insert_one(doc)
    found_id = str(ins.inserted_id)

    matched_lost_ids = run_matching_for_found_item(found_id)

    return {
        "id": found_id,
        "message": "Found item reported",
        "matched_lost_ids": matched_lost_ids,
    }


@router.post("/admin")
def create_found_item_admin(
    admin: dict = Depends(require_admin),
    item_name: str = Form(...),
    date_found: str = Form(...),
    time_found: Optional[str] = Form(None),
    description: str = Form(...),
    location: str = Form(...),
    image: Optional[UploadFile] = File(None),
):
    """Admin adds a found item (no enrollment). Run matching instantly."""
    try:
        date_found_date = datetime.strptime(date_found, "%Y-%m-%d").date()
        date_found_dt = datetime.combine(date_found_date, datetime.min.time())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date. Use YYYY-MM-DD")

    image_url = None
    if image and image.filename:
        content = image.file.read()
        content_type = image.content_type or "image/jpeg"
        image_url = upload_file_to_s3(content, content_type, "found", image.filename)

    doc = {
        "item_name": item_name,
        "date_found": date_found_dt,
        "time_found": time_found,
        "description": description,
        "location": location,
        "image_url": image_url,
        "submitted_by": "administration",
        "enrollment_number": None,
        "status": "open",
        "matched_lost_ids": [],
        "created_at": datetime.utcnow(),
    }
    col = found_items_collection()
    ins = col.insert_one(doc)
    found_id = str(ins.inserted_id)

    matched_lost_ids = run_matching_for_found_item(found_id)

    return {
        "id": found_id,
        "message": "Found item added",
        "matched_lost_ids": matched_lost_ids,
    }
