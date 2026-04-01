# claims.py - Create claim (lost person claims found item); admin approve/reject

from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from bson import ObjectId

from app.database import claim_requests_collection, legacy_claims_collection, lost_items_collection, found_items_collection
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
    col = claim_requests_collection()
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

    # Block duplicate pending/approved claim for same pair
    existing = col.find_one({
        "found_item_id": body.found_item_id,
        "lost_item_id": body.lost_item_id,
        "status": {"$in": ["pending", "approved"]},
    })
    if existing:
        raise HTTPException(status_code=400, detail="Claim already exists for this pair")

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

    # Keep legacy/admin claims collection in sync for historical views and compatibility.
    legacy_col = legacy_claims_collection()
    try:
        legacy_col.insert_one({**doc, "_id": ins.inserted_id})
    except Exception:
        # ignore if duplicate key or legacy collection differs
        pass

    return {"id": str(ins.inserted_id), "message": "Claim submitted", "status": "pending"}


def _serialize_item(doc: dict) -> dict:
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    for key in ("created_at", "when_lost", "date_found", "reviewed_at"):
        val = doc.get(key)
        if isinstance(val, datetime):
            doc[key] = val.isoformat()
    return doc


@router.get("/claimable-items")
def list_claimable_items():
    """
    Public: list lost and found reports for claim section UI.
    Includes student and admin found reports.
    """
    lost_items = []
    found_items = []

    for item in lost_items_collection().find({}).sort("created_at", -1):
        lost_items.append(_serialize_item(item))

    for item in found_items_collection().find({}).sort("created_at", -1):
        found_items.append(_serialize_item(item))

    return {"lost_items": lost_items, "found_items": found_items}


@router.get("")
def list_claims(admin: dict = Depends(require_admin)):
    """Admin: list all claims. Filter by status if needed."""
    cols = [claim_requests_collection(), legacy_claims_collection()]
    lost_col = lost_items_collection()
    found_col = found_items_collection()

    claims = []
    seen_ids = set()
    for col in cols:
        for c in col.find({}).sort("created_at", -1):
            cid = c.get("_id")
            if cid is None:
                continue
            if cid in seen_ids:
                continue
            seen_ids.add(cid)
            c["id"] = str(cid)

            lost_doc = None
            found_doc = None
            try:
                if c.get("lost_item_id"):
                    lost_doc = lost_col.find_one({"_id": ObjectId(c["lost_item_id"])})
            except Exception:
                lost_doc = None
            try:
                if c.get("found_item_id"):
                    found_doc = found_col.find_one({"_id": ObjectId(c["found_item_id"])})
            except Exception:
                found_doc = None

            c["lost_item"] = _serialize_item(lost_doc) if lost_doc else None
            c["found_item"] = _serialize_item(found_doc) if found_doc else None
            if isinstance(c.get("created_at"), datetime):
                c["created_at"] = c["created_at"].isoformat()
            if isinstance(c.get("reviewed_at"), datetime):
                c["reviewed_at"] = c["reviewed_at"].isoformat()

            del c["_id"]
            claims.append(c)

    # Best-effort newest-first across both collections.
    claims.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return {"claims": claims}


@router.patch("/{claim_id}")
def update_claim(claim_id: str, body: ClaimUpdateBody, admin: dict = Depends(require_admin)):
    """Admin: approve or reject claim. On approve, set both items to claimed and email lost person."""
    if body.status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="status must be approved or rejected")

    col_new = claim_requests_collection()
    col_legacy = legacy_claims_collection()
    lost_col = lost_items_collection()
    found_col = found_items_collection()

    try:
        cid = ObjectId(claim_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid claim id")

    claim = col_new.find_one({"_id": cid})
    target_col = col_new
    if not claim:
        claim = col_legacy.find_one({"_id": cid})
        target_col = col_legacy
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Claim already reviewed")

    update_fields = {
        "status": body.status,
        "reviewed_at": datetime.utcnow(),
        "reviewed_by": str(admin["_id"]),
    }

    # Update both main and admin/legacy claim collections for consistent history.
    col_new.update_one({"_id": cid}, {"$set": update_fields})
    col_legacy.update_one({"_id": cid}, {"$set": update_fields})

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
