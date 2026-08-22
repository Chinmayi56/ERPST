"""
Pydantic models for the `registration_links` collection.
Only a token HASH is stored server-side; the raw token is returned once at
creation time as part of the shareable URL and never persisted in plain form.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CreateRegistrationLinkRequest(BaseModel):
    expires_in_days: int = Field(default=7, ge=1, le=90)
    note: Optional[str] = None


class RegistrationLinkOut(BaseModel):
    link_id: str
    url: Optional[str] = None  # only populated on creation response
    status: str  # ACTIVE, EXPIRED, USED, DISABLED
    created_by: str
    created_date: datetime
    expiry_date: datetime
    used_count: int = 0
    note: Optional[str] = None

    class Config:
        from_attributes = True
