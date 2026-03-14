# matcher.py - Match lost items with found items using MongoDB text search
# Run on every new lost/found submit and hourly via APScheduler

import logging
from typing import List

from bson import ObjectId
from app.database import lost_items_collection, found_items_collection
from app.services.email import send_match_notification
from app.config import settings

logger = logging.getLogger(__name__)


def _ensure_text_indexes():
    """Create text indexes if not exist (idempotent)."""
    lost = lost_items_collection()
    found = found_items_collection()
    try:
        lost.create_index([("item_name", "text"), ("description", "text"), ("where_lost", "text")])
    except Exception:
        pass
    try:
        found.create_index([("item_name", "text"), ("description", "text"), ("location", "text")])
    except Exception:
        pass


def _get_lost_doc(lost_col, lost_id: str):
    """Get lost document by id (string or ObjectId)."""
    try:
        return lost_col.find_one({"_id": ObjectId(lost_id)})
    except Exception:
        return lost_col.find_one({"_id": lost_id})


def _get_found_doc(found_col, found_id: str):
    """Get found document by id (string or ObjectId)."""
    try:
        return found_col.find_one({"_id": ObjectId(found_id)})
    except Exception:
        return found_col.find_one({"_id": found_id})


def run_matching_for_lost_item(lost_id: str) -> List[str]:
    """
    Given a new lost item id, find matching found items (open only).
    Update both documents with matched ids and send email to lost person.
    Returns list of found_item ids that matched.
    """
    _ensure_text_indexes()
    lost_col = lost_items_collection()
    found_col = found_items_collection()

    lost_doc = _get_lost_doc(lost_col, lost_id)
    if not lost_doc:
        return []
    lost_id_str = str(lost_doc["_id"])

    search_text = f"{lost_doc.get('item_name', '')} {lost_doc.get('description', '')} {lost_doc.get('where_lost', '')}"
    if not search_text.strip():
        return []

    # MongoDB text search on found_items
    cursor = found_col.find(
        {"$text": {"$search": search_text}, "status": "open"},
        {"score": {"$meta": "textScore"}},
    ).sort([("score", {"$meta": "textScore"})]).limit(5)

    matched_found_ids = []
    for fd in cursor:
        fid = str(fd["_id"])
        matched_found_ids.append(fid)
        # Update found item's matched_lost_ids
        lost_ids = fd.get("matched_lost_ids") or []
        if lost_id_str not in lost_ids:
            lost_ids.append(lost_id_str)
        found_col.update_one({"_id": fd["_id"]}, {"$set": {"matched_lost_ids": lost_ids}})

        # Email lost person
        claim_url = f"{settings.API_BASE_URL}/claim.html?found_id={fid}&lost_id={lost_id_str}"
        send_match_notification(
            lost_doc.get("college_email", ""),
            lost_doc.get("item_name", "Item"),
            fd.get("description", ""),
            claim_url,
        )

    # Update lost item's matched_found_ids
    if matched_found_ids:
        lost_col.update_one(
            {"_id": lost_doc["_id"]},
            {"$set": {"matched_found_ids": matched_found_ids}},
        )

    return matched_found_ids


def run_matching_for_found_item(found_id: str) -> List[str]:
    """
    Given a new found item id, find matching lost items (open only).
    Update both documents and send email to lost person.
    Returns list of lost_item ids that matched.
    """
    _ensure_text_indexes()
    lost_col = lost_items_collection()
    found_col = found_items_collection()

    found_doc = _get_found_doc(found_col, found_id)
    if not found_doc:
        return []
    found_id_str = str(found_doc["_id"])

    search_text = f"{found_doc.get('item_name', '')} {found_doc.get('description', '')} {found_doc.get('location', '')}"
    if not search_text.strip():
        return []

    cursor = lost_col.find(
        {"$text": {"$search": search_text}, "status": "open"},
        {"score": {"$meta": "textScore"}},
    ).sort([("score", {"$meta": "textScore"})]).limit(5)

    matched_lost_ids = []
    for ld in cursor:
        lid = str(ld["_id"])
        matched_lost_ids.append(lid)
        # Update this lost item's matched_found_ids
        found_ids = ld.get("matched_found_ids") or []
        if found_id_str not in found_ids:
            found_ids.append(found_id_str)
        lost_col.update_one({"_id": ld["_id"]}, {"$set": {"matched_found_ids": found_ids}})

        claim_url = f"{settings.API_BASE_URL}/claim.html?found_id={found_id_str}&lost_id={lid}"
        send_match_notification(
            ld.get("college_email", ""),
            ld.get("item_name", "Item"),
            found_doc.get("description", ""),
            claim_url,
        )

    # Update found item's matched_lost_ids
    found_col.update_one(
        {"_id": found_doc["_id"]},
        {"$set": {"matched_lost_ids": matched_lost_ids}},
    )

    return matched_lost_ids


def run_hourly_matching():
    """
    Run matching for all open lost and found items (e.g. hourly job).
    Can re-run matching to catch new items or score changes.
    """
    _ensure_text_indexes()
    lost_col = lost_items_collection()
    found_col = found_items_collection()

    for lost_doc in lost_col.find({"status": "open"}):
        run_matching_for_lost_item(str(lost_doc["_id"]))

    for found_doc in found_col.find({"status": "open"}):
        run_matching_for_found_item(str(found_doc["_id"]))
