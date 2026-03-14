# found_item.py - Pydantic schemas for found items

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel


class FoundItemCreate(BaseModel):
    """Payload when someone reports a found item (student or admin)."""
    item_name: str
    date_found: date
    time_found: Optional[str] = None
    description: str
    location: str
    image_url: Optional[str] = None
    submitted_by: str = "student"  # "student" | "administration"
    enrollment_number: Optional[str] = None


class FoundItemResponse(BaseModel):
    """Found item as returned by API."""
    id: str
    item_name: str
    date_found: date
    time_found: Optional[str] = None
    description: str
    location: str
    image_url: Optional[str] = None
    submitted_by: str
    enrollment_number: Optional[str] = None
    status: str = "open"
    matched_lost_ids: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True


class FoundItemInDB(FoundItemCreate):
    """Found item as stored in MongoDB."""
    id: Optional[str] = None
    status: str = "open"
    matched_lost_ids: List[str] = []
    created_at: datetime = None
