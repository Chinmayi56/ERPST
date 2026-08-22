"""
Pydantic models for the `employees` collection.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class EmployeeUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    mobile: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    status: Optional[str] = None


class EmployeeStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="ACTIVE or DISABLED")


class EmployeeOut(BaseModel):
    employee_id: str
    full_name: str
    email: EmailStr
    mobile: str
    position: str
    department: Optional[str] = None
    joining_date: Optional[str] = None
    status: str = "ACTIVE"
    source_application_id: Optional[str] = None
    approved_by: Optional[str] = None
    approved_date: Optional[datetime] = None
    user_id: Optional[str] = None
    last_login: Optional[datetime] = None
    created_date: datetime

    class Config:
        from_attributes = True
