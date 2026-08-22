"""
Authentication routes: email/password login, mobile OTP login, logout, current user.
"""
from fastapi import APIRouter, Depends, Query

from models.user import (
    EmailPasswordLoginRequest,
    SendOtpRequest,
    VerifyOtpRequest,
    TokenResponse,
    UserPublic,
    EmployeeLoginRequest,
)
from services import auth_service, employee_auth_service, application_service, attendance_service
from database.mongodb import get_db
from utils.dependencies import get_current_user
from config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.get(
    "/demo-config",
    summary="Public demo-mode info for login pages (never exposes real credentials)",
)
async def demo_config():
    """
    Lets any login page (SuperAdmin/SubAdmin) show the correct demo OTP
    without hardcoding it in frontend source -- it always reflects the
    backend's actual settings.DEMO_OTP / settings.DEMO_MODE, so the two can
    never drift out of sync. Returns demo_otp=None whenever DEMO_MODE is
    off (which is enforced/guaranteed off in production by server.py's
    startup guard), so no OTP value is ever surfaced outside demo mode.
    Exposes no credentials, no user data, and requires no auth -- it is
    exactly as sensitive as the DEMO_OTP value already documented in
    .env.example.
    """
    return {
        "demo_mode": settings.DEMO_MODE,
        "demo_otp": settings.DEMO_OTP if settings.DEMO_MODE else None,
        # Mobile OTP login only succeeds for a mobile number that already
        # belongs to an ACTIVE seeded user of the matching role (see
        # services/auth_service.send_demo_otp) -- unlike the original,
        # riskier spec, this deliberately does NOT accept arbitrary
        # unregistered numbers. These seeded numbers are already
        # non-secret, documented values (see .env.example), so surfacing
        # them here lets each portal's login page show the one demo
        # mobile number that will actually work for it.
        "demo_superadmin_mobile": settings.SEED_SUPERADMIN_MOBILE if settings.DEMO_MODE else None,
        "demo_subadmin_mobile": settings.SEED_SUBADMIN_MOBILE if settings.DEMO_MODE else None,
    }


@router.post("/superadmin/login", response_model=TokenResponse, summary="SuperAdmin email/password login")
async def superadmin_login(payload: EmailPasswordLoginRequest):
    result = await auth_service.login_with_email_password(payload.email, payload.password)
    return result


@router.post("/superadmin/send-otp", summary="Send demo OTP to SuperAdmin's mobile (development only)")
async def superadmin_send_otp(payload: SendOtpRequest):
    return await auth_service.send_demo_otp(payload.mobile)


@router.post("/superadmin/verify-otp", response_model=TokenResponse, summary="Verify demo OTP and log in")
async def superadmin_verify_otp(payload: VerifyOtpRequest):
    result = await auth_service.verify_demo_otp(payload.mobile, payload.otp)
    return result


@router.post("/subadmin/login", response_model=TokenResponse, summary="SubAdmin email/password login")
async def subadmin_login(payload: EmailPasswordLoginRequest):
    result = await auth_service.login_with_email_password(payload.email, payload.password, role="SUBADMIN")
    return result


@router.post("/subadmin/send-otp", summary="Send demo OTP to SubAdmin's mobile (development only)")
async def subadmin_send_otp(payload: SendOtpRequest):
    return await auth_service.send_demo_otp(payload.mobile, role="SUBADMIN")


@router.post("/subadmin/verify-otp", response_model=TokenResponse, summary="Verify demo OTP and log in")
async def subadmin_verify_otp(payload: VerifyOtpRequest):
    result = await auth_service.verify_demo_otp(payload.mobile, payload.otp, role="SUBADMIN")
    return result


@router.post(
    "/employee/login",
    response_model=TokenResponse,
    summary="Employee email/password login (blocked until SuperAdmin approval creates the account)",
)
async def employee_login(payload: EmployeeLoginRequest):
    result = await employee_auth_service.login_employee(payload.email, payload.password)
    return result


@router.get(
    "/employee/application-status",
    summary="Check an employee application's status by email (public, unauthenticated)",
)
async def employee_application_status(email: str = Query(..., description="Email used at registration")):
    # Unauthenticated by design: an applicant has no login account (and thus
    # no JWT) until a SuperAdmin approves them, so this is how the Employee
    # portal polls for approval before that account exists.
    return await application_service.get_application_status_by_email(email)


@router.post("/logout", summary="Logout (client should discard the JWT)")
async def logout(current_user: dict = Depends(get_current_user)):
    # JWTs are stateless; logout is handled by the client discarding the token.
    # This endpoint exists for a consistent API contract and future token
    # blacklist support if needed.
    if current_user.get("role") == "EMPLOYEE":
        # Best-effort: record today's check-out time on the real attendance
        # record created at login. Never fails logout itself.
        try:
            db = get_db()
            employee = await db.employees.find_one({"user_id": current_user["user_id"]})
            if employee:
                await attendance_service.record_logout(employee["employee_id"])
        except Exception:
            pass
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserPublic, summary="Get the currently authenticated user")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
