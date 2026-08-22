"""
Pydantic request/response models for authentication and the `users` collection.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class EmailPasswordLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class EmployeeLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class SendOtpRequest(BaseModel):
    mobile: str = Field(..., min_length=10, max_length=10)


class VerifyOtpRequest(BaseModel):
    mobile: str = Field(..., min_length=10, max_length=10)
    otp: str = Field(..., min_length=6, max_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserPublic"


class UserPublic(BaseModel):
    user_id: str
    name: str
    email: EmailStr
    mobile: str
    role: str
    status: str
    created_date: datetime

    class Config:
        from_attributes = True


TokenResponse.model_rebuild()
