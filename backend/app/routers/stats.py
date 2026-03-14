# stats.py - Homepage stats: Item Lost, Item Found, Total Items Lost

from fastapi import APIRouter
from app.database import lost_items_collection, found_items_collection

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("")
def get_stats():
    """
    Return counts for homepage: total lost items, total found items.
    "Total Items Lost" = count of lost_items (open + claimed).
    No auth required.
    """
    lost_col = lost_items_collection()
    found_col = found_items_collection()
    total_lost = lost_col.count_documents({})
    total_found = found_col.count_documents({})
    return {
        "total_lost": total_lost,
        "total_found": total_found,
        "total_items_lost": total_lost,  # same as total_lost for display
    }
