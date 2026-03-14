# lost_item.py - Pydantic schemas for lost items

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class LostItemCreate(BaseModel):
    """Payload when someone reports a lost item."""
    name: str
    college_email: EmailStr
    where_lost: str
    when_lost: date
    item_name: str
    description: str
    image_url: Optional[str] = None


class LostItemResponse(BaseModel):
    """Lost item as returned by API."""
    id: str
    name: str
    college_email: str
    where_lost: str
    when_lost: date
    item_name: str
    description: str
    image_url: Optional[str] = None
    status: str = "open"
    matched_found_ids: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True


class LostItemInDB(LostItemCreate):
    """Lost item as stored in MongoDB."""
    id: Optional[str] = None
    status: str = "open"
    matched_found_ids: List[str] = []
    created_at: datetime = None
