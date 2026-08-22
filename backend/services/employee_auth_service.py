"""
Employee authentication. An employee login account is only ever created at
the moment a SuperAdmin approves their application (see application_service),
so a pending/rejected applicant has no `users` record and cannot authenticate.
This is the backend-enforced guarantee required by the security rule: login
eligibility is never decided by the frontend alone.

Login enforces, in order:
  1. A `users` record exists for this email with role EMPLOYEE, and the
     password matches.
  2. The user account status is ACTIVE.
  3. The linked `employees` record exists and is ACTIVE.
  4. The source application (if still resolvable) is APPROVED.
Only then is a JWT issued. Every other outcome returns a specific,
spec-required message so the employee knows exactly why they can't log in.
"""
from datetime import datetime, timezone
from fastapi import HTTPException, status

from database.mongodb import get_db
from utils.security import verify_password
from utils.jwt import create_access_token
from services.audit_service import log_action
from services import attendance_service

PENDING_LIKE_STATUSES = ("PENDING", "UNDER_REVIEW")

MSG_INVALID_CREDENTIALS = "Invalid email or password"
MSG_PENDING = "Your employee application is still pending SuperAdmin approval."
MSG_REJECTED = "Your employee application was rejected. Please contact the administrator."
MSG_INACTIVE = "Your employee account is currently inactive."


async def login_employee(email: str, password: str) -> dict:
    db = get_db()
    email_norm = email.strip().lower()

    user = await db.users.find_one({"email": email_norm, "role": "EMPLOYEE"})

    if user is not None:
        # A login account exists — verify the password before revealing
        # anything else about account state.
        if not verify_password(password, user.get("password_hash", "")):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=MSG_INVALID_CREDENTIALS)

        if user.get("status") != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=MSG_INACTIVE)

        # Defense in depth: re-verify the underlying employee record (and its
        # source application) is approved and active, even though a user
        # record only exists post-approval.
        employee = await db.employees.find_one({"user_id": user["user_id"]})
        if not employee or employee.get("status") != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=MSG_INACTIVE)

        application = await db.employee_applications.find_one(
            {"application_id": employee.get("source_application_id")}
        )
        if application and application.get("status") != "APPROVED":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=MSG_PENDING)

        now = datetime.now(timezone.utc)
        await db.employees.update_one({"employee_id": employee["employee_id"]}, {"$set": {"last_login": now}})

        # Automatically record today's attendance (check-in) for this login --
        # real MongoDB write, immediately visible in the SuperAdmin Attendance
        # module. Never blocks login if attendance recording itself fails.
        try:
            await attendance_service.record_login(employee)
        except Exception:
            pass

        token = create_access_token(user["user_id"], user["role"], user["email"], employee_id=employee["employee_id"])
        await log_action(user["user_id"], user["role"], "LOGIN_EMPLOYEE", "user", user["user_id"])
        return {"access_token": token, "token_type": "bearer", "user": user}

    # No login account yet — this only happens pre-approval (PENDING/
    # UNDER_REVIEW) or post-rejection (REJECTED accounts are never created).
    # Look up the application so the employee gets an accurate, spec-required
    # message instead of a bare "invalid credentials".
    application = await db.employee_applications.find_one({"email": email_norm})
    if application:
        app_status = application.get("status")
        if app_status in PENDING_LIKE_STATUSES:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=MSG_PENDING)
        if app_status == "REJECTED":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=MSG_REJECTED)

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=MSG_INVALID_CREDENTIALS)
