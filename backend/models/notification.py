"""
Pydantic models for the `notifications` collection.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class NotificationOut(BaseModel):
    notification_id: str
    recipient_user_id: str
    type: str
    message: str
    related_application_id: Optional[str] = None
    is_read: bool = False
    created_date: datetime

    class Config:
        from_attributes = True
