"""Live SuperAdmin dashboard aggregation from MongoDB."""
from datetime import datetime, timezone
from database.mongodb import get_db

_ACTIVITY_LABELS = {
    "LOGIN_EMAIL_PASSWORD": "logged in",
    "LOGIN_MOBILE_OTP": "logged in (OTP)",
    "LOGIN_EMPLOYEE": "logged in",
    "UPDATE_EMPLOYEE": "updated an employee record",
    "DISABLE_EMPLOYEE": "disabled an employee",
    "SET_EMPLOYEE_STATUS": "changed an employee's status",
    "CREATE_REGISTRATION_LINK": "created a registration link",
    "DISABLE_REGISTRATION_LINK": "disabled a registration link",
    "APPROVE_APPLICATION": "approved an application",
    "REJECT_APPLICATION": "rejected an application",
}


def _clean(doc):
    doc.pop("_id", None)
    doc.pop("password_hash", None)
    return doc


async def get_dashboard_summary() -> dict:
    db = get_db()
    today = datetime.now(timezone.utc).date().isoformat()

    recent_applications = [_clean(d) async for d in db.employee_applications.find({}).sort("submitted_date", -1).limit(5)]
    recent_notifications = [_clean(d) async for d in db.notifications.find({}).sort("created_date", -1).limit(5)]
    recent_activities = []
    async for doc in db.audit_logs.find({}).sort("timestamp", -1).limit(10):
        doc = _clean(doc)
        action = doc.get("action", "")
        doc["label"] = _ACTIVITY_LABELS.get(action, action.replace("_", " ").title())
        recent_activities.append(doc)

    return {
        "total_employees": await db.employees.count_documents({}),
        "active_employees": await db.employees.count_documents({"status": "ACTIVE"}),
        "disabled_employees": await db.employees.count_documents({"status": "DISABLED"}),
        "pending_applications": await db.employee_applications.count_documents({"status": "PENDING"}),
        "approved_applications": await db.employee_applications.count_documents({"status": "APPROVED"}),
        "rejected_applications": await db.employee_applications.count_documents({"status": "REJECTED"}),
        "pending_employees": await db.employee_applications.count_documents({"status": "PENDING"}),
        "unread_notifications": await db.notifications.count_documents({"is_read": False}),
        "clients_total": await db.clients.count_documents({}),
        "active_clients": await db.clients.count_documents({"status": "ACTIVE"}),
        "active_projects": await db.projects.count_documents({"status": {"$in": ["ACTIVE", "IN_PROGRESS"]}}),
        "projects_total": await db.projects.count_documents({}),
        "pending_leaves": await db.leaves.count_documents({"status": "PENDING"}),
        "approved_leaves": await db.leaves.count_documents({"status": "APPROVED"}),
        "today_attendance": await db.attendance.count_documents({"date": today}),
        "today_present": await db.attendance.count_documents({"date": today, "status": {"$in": ["PRESENT", "LATE", "HALF_DAY"]}}),
        "active_services": await db.services.count_documents({"status": "ACTIVE"}),
        "active_bookings": await db.bookings.count_documents({"status": {"$in": ["PENDING", "CONFIRMED"]}}),
        "documents_total": await db.documents.count_documents({}),
        "tasks_total": await db.tasks.count_documents({}),
        "pending_tasks": await db.tasks.count_documents({"status": {"$in": ["TODO", "IN_PROGRESS", "REVIEW"]}}),
        "completed_tasks": await db.tasks.count_documents({"status": "COMPLETED"}),
        "recent_applications": recent_applications,
        "recent_notifications": recent_notifications,
        "recent_activities": recent_activities,
    }


async def list_users() -> list:
    cursor = get_db().users.find({}).sort("created_date", -1)
    users = []
    async for doc in cursor:
        users.append(_clean(doc))
    return users
