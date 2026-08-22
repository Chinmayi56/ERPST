"""
Employee management service: list, view, update, disable.
"""
from fastapi import HTTPException, status
from database.mongodb import get_db
from services.audit_service import log_action
from services.notification_service import create_notification


async def list_employees(status_filter: str = None) -> list:
    db = get_db()
    query = {}
    if status_filter:
        query["status"] = status_filter.upper()
    cursor = db.employees.find(query).sort("created_date", -1)
    results = []
    async for doc in cursor:
        doc.pop("_id", None)
        results.append(doc)
    return results


async def get_employee(employee_id: str) -> dict:
    db = get_db()
    doc = await db.employees.find_one({"employee_id": employee_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    doc.pop("_id", None)
    return doc


async def update_employee(employee_id: str, updates: dict, actor: dict) -> dict:
    db = get_db()
    updates = {k: v for k, v in updates.items() if v is not None}
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided to update")

    result = await db.employees.find_one_and_update(
        {"employee_id": employee_id},
        {"$set": updates},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    await log_action(actor["user_id"], actor["role"], "UPDATE_EMPLOYEE", "employee", employee_id, details=updates)
    result.pop("_id", None)
    return result


async def disable_employee(employee_id: str, actor: dict) -> dict:
    db = get_db()
    result = await db.employees.find_one_and_update(
        {"employee_id": employee_id},
        {"$set": {"status": "DISABLED"}},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    if result.get("user_id"):
        await db.users.update_one({"user_id": result["user_id"]}, {"$set": {"status": "DISABLED"}})
        await create_notification(
            recipient_user_id=result["user_id"],
            notif_type="ACCOUNT_DEACTIVATED",
            message="Your employee account has been deactivated by an administrator.",
        )

    await log_action(actor["user_id"], actor["role"], "DISABLE_EMPLOYEE", "employee", employee_id)
    result.pop("_id", None)
    return result


async def set_employee_status(employee_id: str, new_status: str, actor: dict) -> dict:
    """Activate or deactivate an employee. Also flips the linked login account
    so a DISABLED employee is immediately blocked from logging in."""
    new_status = (new_status or "").upper()
    if new_status not in ("ACTIVE", "DISABLED"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status must be ACTIVE or DISABLED")

    db = get_db()
    result = await db.employees.find_one_and_update(
        {"employee_id": employee_id},
        {"$set": {"status": new_status}},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    if result.get("user_id"):
        await db.users.update_one({"user_id": result["user_id"]}, {"$set": {"status": new_status}})
        notif_type = "ACCOUNT_ACTIVATED" if new_status == "ACTIVE" else "ACCOUNT_DEACTIVATED"
        message = (
            "Your employee account has been activated. You can now log in."
            if new_status == "ACTIVE"
            else "Your employee account has been deactivated by an administrator."
        )
        await create_notification(recipient_user_id=result["user_id"], notif_type=notif_type, message=message)

    await log_action(actor["user_id"], actor["role"], "SET_EMPLOYEE_STATUS", "employee", employee_id, details={"status": new_status})
    result.pop("_id", None)
    return result
