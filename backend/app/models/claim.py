# claim.py - Pydantic schemas for claims (linking lost item to found item)

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ClaimCreate(BaseModel):
    """Payload when lost person claims a found item."""
    found_item_id: str
    lost_item_id: str


class ClaimUpdate(BaseModel):
    """Admin updates claim status."""
    status: str  # "approved" | "rejected"


class ClaimResponse(BaseModel):
    """Claim as returned by API."""
    id: str
    found_item_id: str
    lost_item_id: str
    claimed_by: Optional[str] = None  # user id or email
    status: str  # "pending" | "approved" | "rejected"
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None

    class Config:
        from_attributes = True
