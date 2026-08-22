"""
Employee Portal service: read-only data for the logged-in employee's own
dashboard and profile. Every function here scopes queries to the calling
user's own `user_id` / linked `employee_id` — an employee can only ever see
their own record, never another employee's.
"""
from fastapi import HTTPException, status
from database.mongodb import get_db


async def _get_own_employee(user_id: str) -> dict:
    db = get_db()
    employee = await db.employees.find_one({"user_id": user_id})
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee record not found")
    employee.pop("_id", None)
    return employee


async def get_dashboard(current_user: dict) -> dict:
    employee = await _get_own_employee(current_user["user_id"])
    return {
        "employee_id": employee["employee_id"],
        "name": employee["full_name"],
        "email": employee["email"],
        "mobile": employee["mobile"],
        "department": employee.get("department"),
        "designation": employee.get("position"),
        "joining_date": employee.get("joining_date"),
        "status": employee.get("status"),
        "last_login": employee.get("last_login"),
    }


async def get_profile(current_user: dict) -> dict:
    db = get_db()
    employee = await _get_own_employee(current_user["user_id"])

    application = None
    if employee.get("source_application_id"):
        application = await db.employee_applications.find_one(
            {"application_id": employee["source_application_id"]}
        )
        if application:
            application.pop("_id", None)

    approved_by_name = None
    if employee.get("approved_by"):
        approver = await db.users.find_one({"user_id": employee["approved_by"]})
        if approver:
            approved_by_name = approver.get("name")

    return {
        "personal_details": {
            "full_name": employee.get("full_name"),
            "email": employee.get("email"),
            "mobile": employee.get("mobile"),
            "dob": application.get("dob") if application else None,
            "gender": application.get("gender") if application else None,
            "address": application.get("address") if application else None,
        },
        "professional_details": {
            "employee_id": employee.get("employee_id"),
            "department": employee.get("department"),
            "designation": employee.get("position"),
            "joining_date": employee.get("joining_date"),
            "qualification": application.get("qualification") if application else None,
            "experience": application.get("total_experience") if application else None,
        },
        "application_id": employee.get("source_application_id"),
        "submitted_date": application.get("submitted_date") if application else None,
        "approval_date": employee.get("approved_date"),
        "approved_by": approved_by_name or employee.get("approved_by"),
        "current_status": employee.get("status"),
        "last_login": employee.get("last_login"),
    }
