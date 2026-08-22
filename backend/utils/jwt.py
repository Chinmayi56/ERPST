"""
JWT creation and verification.
Token payload includes: user_id (sub), role, email, exp, and — for employees —
employee_id, so protected employee routes never need an extra DB lookup just
to know which employee record a token belongs to.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from config import settings


def create_access_token(user_id: str, role: str, email: str, employee_id: Optional[str] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "user_id": user_id,
        "role": role,
        "email": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    if employee_id:
        payload["employee_id"] = employee_id
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
