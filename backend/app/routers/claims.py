# claims.py - Create claim (lost person claims found item); admin approve/reject

from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from bson import ObjectId

from app.database import claims_collection, lost_items_collection, found_items_collection
from app.routers.deps import get_current_user_id, require_admin
from app.services.email import send_claim_approved, send_claim_rejected

router = APIRouter(prefix="/claims", tags=["claims"])


class ClaimCreateBody(BaseModel):
    found_item_id: str
    lost_item_id: str


class ClaimUpdateBody(BaseModel):
    status: str  # "approved" | "rejected"


@router.post("")
def create_claim(body: ClaimCreateBody, user_id: str = Depends(get_current_user_id)):
    """
    Lost person claims a found item. Check that lost item belongs to this user (by email or user_id).
    For simplicity we allow any authenticated user to claim; in production you'd check lost_item.college_email
    matches user or lost_item has a user_id.
    """
    col = claims_collection()
    lost_col = lost_items_collection()
    found_col = found_items_collection()

    try:
        fid = ObjectId(body.found_item_id)
        lid = ObjectId(body.lost_item_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ids")

    lost_doc = lost_col.find_one({"_id": lid})
    found_doc = found_col.find_one({"_id": fid})
    if not lost_doc or not found_doc:
        raise HTTPException(status_code=404, detail="Lost or found item not found")
    if lost_doc.get("status") == "claimed":
        raise HTTPException(status_code=400, detail="Lost item already claimed")
    if found_doc.get("status") == "claimed":
        raise HTTPException(status_code=400, detail="Found item already claimed")

    # Check if there's already an approved claim for this pair
    existing = col.find_one({
        "found_item_id": body.found_item_id,
        "lost_item_id": body.lost_item_id,
        "status": "approved",
    })
    if existing:
        raise HTTPException(status_code=400, detail="Claim already approved")

    doc = {
        "found_item_id": body.found_item_id,
        "lost_item_id": body.lost_item_id,
        "claimed_by": user_id,
        "status": "pending",
        "created_at": datetime.utcnow(),
        "reviewed_at": None,
        "reviewed_by": None,
    }
    ins = col.insert_one(doc)
    return {"id": str(ins.inserted_id), "message": "Claim submitted", "status": "pending"}


@router.get("")
def list_claims(admin: dict = Depends(require_admin)):
    """Admin: list all claims. Filter by status if needed."""
    col = claims_collection()
    claims = []
    for c in col.find({}).sort("created_at", -1):
        c["id"] = str(c["_id"])
        del c["_id"]
        claims.append(c)
    return {"claims": claims}


@router.patch("/{claim_id}")
def update_claim(claim_id: str, body: ClaimUpdateBody, admin: dict = Depends(require_admin)):
    """Admin: approve or reject claim. On approve, set both items to claimed and email lost person."""
    if body.status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="status must be approved or rejected")

    col = claims_collection()
    lost_col = lost_items_collection()
    found_col = found_items_collection()

    try:
        cid = ObjectId(claim_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid claim id")

    claim = col.find_one({"_id": cid})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Claim already reviewed")

    col.update_one(
        {"_id": cid},
        {
            "$set": {
                "status": body.status,
                "reviewed_at": datetime.utcnow(),
                "reviewed_by": str(admin["_id"]),
            }
        },
    )

    if body.status == "approved":
        lost_col.update_one({"_id": ObjectId(claim["lost_item_id"])}, {"$set": {"status": "claimed"}})
        found_col.update_one({"_id": ObjectId(claim["found_item_id"])}, {"$set": {"status": "claimed"}})
        lost_doc = lost_col.find_one({"_id": ObjectId(claim["lost_item_id"])})
        if lost_doc and lost_doc.get("college_email"):
            send_claim_approved(lost_doc["college_email"], lost_doc.get("item_name", "Item"))
    else:
        lost_doc = lost_col.find_one({"_id": ObjectId(claim["lost_item_id"])})
        if lost_doc and lost_doc.get("college_email"):
            send_claim_rejected(lost_doc["college_email"], lost_doc.get("item_name", "Item"))

    return {"message": f"Claim {body.status}"}
