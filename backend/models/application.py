"""
Pydantic models for the `employee_applications` collection.

The application document is designed to hold every field the future public
Employee Registration Form will submit, so no data is lost when that portal
is built later. Superadmin currently only reads/approves/rejects these.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationInfo

from utils.validation import is_valid_mobile


class RejectApplicationRequest(BaseModel):
    reason: str = Field(..., min_length=3, description="Rejection reason (required)")


class ApplicationCreateRequest(BaseModel):
    """Public Employee Registration Form submission payload."""

    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72, description="Password for the future employee login account")
    confirm_password: str = Field(..., min_length=8, max_length=72, description="Must match password")
    mobile: str = Field(..., description="10-digit mobile number")
    dob: str = Field(..., description="Date of birth, e.g. 1998-04-12")
    gender: str = Field(..., description="Male, Female or Other")
    address: str = Field(..., min_length=5, max_length=500)
    department: str = Field(..., min_length=2, max_length=100)
    designation: str = Field(..., min_length=2, max_length=100, description="Applied position")
    qualification: str = Field(..., min_length=2, max_length=150)
    experience: str = Field(..., min_length=1, max_length=100)
    resume_url: Optional[str] = None
    id_proof_url: Optional[str] = None
    registration_token: Optional[str] = Field(
        default=None, description="Optional token from a SuperAdmin-generated registration link"
    )

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v: str) -> str:
        v = v.strip()
        if not is_valid_mobile(v):
            raise ValueError("Enter a valid 10-digit mobile number")
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        v = v.strip()
        if v not in ("Male", "Female", "Other"):
            raise ValueError("Gender must be Male, Female or Other")
        return v

    @field_validator("confirm_password")
    @classmethod
    def validate_password_match(cls, v: str, info: ValidationInfo) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Password and Verify Password do not match")
        return v


class ApplicationOut(BaseModel):
    application_id: str
    # Personal
    full_name: str
    dob: Optional[str] = None
    gender: Optional[str] = None
    profile_photo_url: Optional[str] = None
    # Contact
    email: EmailStr
    mobile: str
    alternate_mobile: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    # Professional
    applied_position: str
    department: Optional[str] = None
    qualification: Optional[str] = None
    experience_level: Optional[str] = None
    total_experience: Optional[str] = None
    previous_company: Optional[str] = None
    previous_designation: Optional[str] = None
    skills: Optional[list] = []
    # Joining
    expected_joining_date: Optional[str] = None
    employment_type: Optional[str] = None
    # Emergency
    emergency_contact_name: Optional[str] = None
    emergency_relationship: Optional[str] = None
    emergency_contact_number: Optional[str] = None
    # Documents
    resume_url: Optional[str] = None
    id_proof_url: Optional[str] = None
    # Declaration
    declaration_text: Optional[str] = None
    declaration_accepted: Optional[bool] = False
    # Application meta
    status: str = "PENDING"
    submitted_date: datetime
    reviewed_date: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    rejection_reason: Optional[str] = None

    class Config:
        from_attributes = True
