"""
Authentication business logic: email/password login and demo mobile OTP login
for SuperAdmin. Issues JWT access tokens on success.
"""
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status

from config import settings
from database.mongodb import get_db
from utils.security import verify_password
from utils.jwt import create_access_token
from utils.validation import is_valid_mobile, is_valid_otp
from services.audit_service import log_action

# In-memory OTP store for the DEMO OTP flow only.
# This is intentionally simple for the development phase; a real provider
# (SMS gateway) integration would replace this with a persisted, expiring
# OTP record instead of an in-memory dict.
_otp_store: dict = {}


async def login_with_email_password(email: str, password: str, role: str = "SUPERADMIN") -> dict:
    """
    Email/password login for a single-role portal (SuperAdmin or SubAdmin).
    `role` is a server-side parameter supplied by the route the caller hit
    (e.g. /api/auth/subadmin/login always passes role="SUBADMIN") -- it is
    never taken from the request body, so a SubAdmin cannot log in as
    SuperAdmin (or vice versa) by tweaking the payload.
    """
    db = get_db()
    email_norm = email.strip().lower()
    user = await db.users.find_one({"email": email_norm})

    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if user.get("role") != role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{role.title()} access required",
        )

    if user.get("status") != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    token = create_access_token(user["user_id"], user["role"], user["email"])
    await log_action(user["user_id"], user["role"], "LOGIN_EMAIL_PASSWORD", "user", user["user_id"])
    return {"access_token": token, "token_type": "bearer", "user": user}


def _require_demo_mode() -> None:
    # This codebase has no real SMS/OTP provider integrated -- the only OTP
    # mechanism that exists is the fixed/mock one below. It must never be
    # reachable unless DEMO_MODE is explicitly on, and server.py's startup
    # guard additionally refuses to boot at all with DEMO_MODE=true in
    # production. This is defense in depth, not the only gate.
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mobile OTP login is not available (no SMS provider configured).",
        )


async def send_demo_otp(mobile: str, role: str = "SUPERADMIN") -> dict:
    _require_demo_mode()
    if not is_valid_mobile(mobile):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid mobile number")

    db = get_db()
    user = await db.users.find_one({"mobile": mobile, "role": role})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No {role.title()} account found for this mobile number")

    # DEMO/MOCK ONLY: fixed OTP (settings.DEMO_OTP), "sent" by being logged
    # and returned in the response below -- no real SMS provider is called.
    # Keyed by (mobile, role) so a SuperAdmin and SubAdmin OTP request for
    # numbers that happen to collide can never be verified against the
    # wrong role's record.
    _otp_store[(mobile, role)] = {
        "otp": settings.DEMO_OTP,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    print(f"[demo-sms] OTP for {role} {mobile}: {settings.DEMO_OTP} (mock provider, no SMS sent)")
    return {
        "message": "OTP sent (demo mode)",
        "demo_otp_hint": f"Use {settings.DEMO_OTP} in development",
    }


async def verify_demo_otp(mobile: str, otp: str, role: str = "SUPERADMIN") -> dict:
    _require_demo_mode()
    if not is_valid_mobile(mobile):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid mobile number")
    if not is_valid_otp(otp):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP format")

    record = _otp_store.get((mobile, role))
    if not record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No OTP was requested for this mobile number")

    if datetime.now(timezone.utc) > record["expires_at"]:
        del _otp_store[(mobile, role)]
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP has expired, please request a new one")

    if otp != record["otp"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect OTP")

    db = get_db()
    user = await db.users.find_one({"mobile": mobile, "role": role})
    if not user or user.get("status") != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled or not found")

    del _otp_store[(mobile, role)]

    token = create_access_token(user["user_id"], user["role"], user["email"])
    await log_action(user["user_id"], user["role"], "LOGIN_MOBILE_OTP", "user", user["user_id"])
    return {"access_token": token, "token_type": "bearer", "user": user}
