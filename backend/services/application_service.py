"""
Employee application service: public submission, list, view details, approve, reject.
Approving an application also creates the corresponding employee record AND a
gated employee login account (backend-enforced -- an applicant cannot log in
before SuperAdmin approval, because no user account exists until then).
"""
from datetime import datetime, timezone
from fastapi import HTTPException, status

from database.mongodb import get_db
from utils.security import generate_id, hash_password
from services.notification_service import create_notification, notify_admins
from services.audit_service import log_action
from services.id_service import generate_application_id, generate_employee_id

PENDING_LIKE_STATUSES = ("PENDING", "UNDER_REVIEW")


async def create_application(data: dict) -> dict:
    db = get_db()

    email = data["email"].strip().lower()
    mobile = data["mobile"].strip()

    existing_application = await db.employee_applications.find_one(
        {
            "$or": [{"email": email}, {"mobile": mobile}],
            "status": {"$in": [*PENDING_LIKE_STATUSES, "APPROVED"]},
        }
    )
    if existing_application:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An application with this email or mobile number already exists.",
        )

    existing_employee = await db.employees.find_one({"$or": [{"email": email}, {"mobile": mobile}]})
    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An employee with this email or mobile number already exists.",
        )

    application_id = await generate_application_id()
    now = datetime.now(timezone.utc)

    doc = {
        "application_id": application_id,
        "full_name": data["full_name"].strip(),
        "dob": data["dob"],
        "gender": data["gender"],
        "email": email,
        "mobile": mobile,
        "address": data["address"].strip(),
        "applied_position": data["designation"].strip(),
        "department": data["department"].strip(),
        "qualification": data["qualification"].strip(),
        "total_experience": data["experience"].strip(),
        "resume_url": data.get("resume_url"),
        "id_proof_url": data.get("id_proof_url"),
        # The applicant's chosen password is hashed immediately and never
        # stored or logged in plain text. It becomes the employee's login
        # password once a SuperAdmin approves this application.
        "password_hash": hash_password(data["password"]),
        "declaration_accepted": True,
        "status": "PENDING",
        "submitted_date": now,
        "reviewed_date": None,
        "reviewed_by": None,
        "rejection_reason": None,
    }
    await db.employee_applications.insert_one(doc)

    await notify_admins(
        notif_type="NEW_APPLICATION",
        message=f"New employee application received from {doc['full_name']}.",
        related_application_id=application_id,
    )

    doc.pop("_id", None)
    doc.pop("password_hash", None)  # never expose the hash via the API
    return doc


async def list_applications(status_filter: str = None) -> list:
    db = get_db()
    query = {}
    if status_filter:
        query["status"] = status_filter.upper()
    cursor = db.employee_applications.find(query).sort("submitted_date", -1)
    results = []
    async for doc in cursor:
        doc.pop("_id", None)
        doc.pop("password_hash", None)  # never expose the hash via the API
        results.append(doc)
    return results


STATUS_MESSAGES = {
    "PENDING": "Your application is still pending approval.",
    "UNDER_REVIEW": "Your application is still pending approval.",
    "APPROVED": "Your application has been approved. You can now login.",
    "REJECTED": "Your application was rejected.",
}


async def get_application_status_by_email(email: str) -> dict:
    """
    Public, unauthenticated lookup used by the Employee portal to poll its
    own application status before a login account exists (an applicant has
    no JWT until SuperAdmin approval creates one). Returns only the minimal
    status info needed for the UI -- never the password hash or other
    applicant PII.
    """
    db = get_db()
    email_norm = email.strip().lower()
    application = await db.employee_applications.find_one(
        {"email": email_norm}, sort=[("submitted_date", -1)]
    )
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No application found for this email")

    app_status = application.get("status", "PENDING")
    return {
        "application_id": application["application_id"],
        "status": app_status,
        "message": STATUS_MESSAGES.get(app_status, "Your application status is unknown. Please contact the administrator."),
    }


async def get_application(application_id: str) -> dict:
    db = get_db()
    doc = await db.employee_applications.find_one({"application_id": application_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    doc.pop("_id", None)
    doc.pop("password_hash", None)  # never expose the hash via the API
    return doc


async def approve_application(application_id: str, reviewer: dict) -> dict:
    db = get_db()
    application = await db.employee_applications.find_one({"application_id": application_id})
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    if application["status"] == "APPROVED":
        # Idempotent by design: a double-click (or a retried request) on an
        # already-approved application must never create a second user /
        # employee record. Tell the caller plainly instead of a generic error.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Application is already approved.")
    if application["status"] == "REJECTED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This application has already been rejected and cannot be approved.")
    if application["status"] not in PENDING_LIKE_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending applications can be approved")

    existing_employee = await db.employees.find_one({"source_application_id": application_id})
    if existing_employee:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An employee already exists for this application")

    now = datetime.now(timezone.utc)
    updated_app = await db.employee_applications.find_one_and_update(
        {"application_id": application_id, "status": application["status"]},
        {"$set": {
            "status": "APPROVED",
            "reviewed_date": now,
            "reviewed_by": reviewer["user_id"],
        }},
        return_document=True,
    )
    if not updated_app:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Application is already approved.")

    employee_id = await generate_employee_id()

    # The applicant's own password (hashed at submission time) becomes their
    # employee login password — never a system-generated temporary one.
    user_doc = {
        "user_id": generate_id("USR"),
        "name": application["full_name"],
        "email": application["email"],
        "mobile": application["mobile"],
        "password_hash": application["password_hash"],
        "role": "EMPLOYEE",
        "status": "ACTIVE",
        "created_date": now,
        "must_change_password": False,
    }
    await db.users.insert_one(user_doc)

    employee_doc = {
        "employee_id": employee_id,
        "full_name": application["full_name"],
        "email": application["email"],
        "mobile": application["mobile"],
        "position": application["applied_position"],
        "department": application.get("department"),
        "joining_date": application.get("expected_joining_date"),
        "status": "ACTIVE",
        "source_application_id": application_id,
        "approved_by": reviewer["user_id"],
        "approved_date": now,
        "user_id": user_doc["user_id"],
        "created_date": now,
    }
    await db.employees.insert_one(employee_doc)

    # Employee-facing notifications. The employee's login account (and thus
    # their notification inbox) only starts existing at this moment, so we
    # backfill a "submitted" entry alongside "approved" for a complete history
    # on their first login.
    await create_notification(
        recipient_user_id=user_doc["user_id"],
        notif_type="APPLICATION_SUBMITTED",
        message=f"Your application {application_id} was received and reviewed.",
        related_application_id=application_id,
    )
    await create_notification(
        recipient_user_id=user_doc["user_id"],
        notif_type="APPLICATION_APPROVED",
        message="Your employee application has been approved. Welcome to Strivenest Technologies!",
        related_application_id=application_id,
    )

    await notify_admins(
        notif_type="APPLICATION_APPROVED",
        message=f"Application {application_id} for {application['full_name']} was approved.",
        related_application_id=application_id,
    )
    await log_action(
        reviewer["user_id"], reviewer["role"], "APPROVE_APPLICATION",
        "employee_application", application_id, details={"employee_id": employee_id},
    )

    updated = await db.employee_applications.find_one({"application_id": application_id})
    updated.pop("_id", None)
    updated.pop("password_hash", None)  # never expose the hash via the API
    updated["employee_id"] = employee_id
    updated["employee_login_email"] = application["email"]
    return updated


async def reject_application(application_id: str, reason: str, reviewer: dict) -> dict:
    db = get_db()
    application = await db.employee_applications.find_one({"application_id": application_id})
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    if application["status"] == "REJECTED":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Application is already rejected.")
    if application["status"] == "APPROVED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This application has already been approved and cannot be rejected.")
    if application["status"] not in PENDING_LIKE_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending applications can be rejected")

    now = datetime.now(timezone.utc)
    result = await db.employee_applications.find_one_and_update(
        {"application_id": application_id, "status": application["status"]},
        {"$set": {
            "status": "REJECTED",
            "reviewed_date": now,
            "reviewed_by": reviewer["user_id"],
            "rejection_reason": reason,
        }},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Application was already reviewed")

    await notify_admins(
        notif_type="APPLICATION_REJECTED",
        message=f"Application {application_id} for {application['full_name']} was rejected.",
        related_application_id=application_id,
    )
    await log_action(
        reviewer["user_id"], reviewer["role"], "REJECT_APPLICATION",
        "employee_application", application_id, details={"reason": reason},
    )

    updated = await db.employee_applications.find_one({"application_id": application_id})
    updated.pop("_id", None)
    updated.pop("password_hash", None)  # never expose the hash via the API
    return updated
