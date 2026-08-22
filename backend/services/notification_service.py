"""
Notification service: create and read notifications for SuperAdmin users.
"""
from datetime import datetime, timezone
from fastapi import HTTPException, status
from database.mongodb import get_db
from utils.security import generate_id


async def create_notification(
    recipient_user_id: str,
    notif_type: str,
    message: str,
    related_application_id: str = None,
):
    db = get_db()
    doc = {
        "notification_id": generate_id("NTF"),
        "recipient_user_id": recipient_user_id,
        "type": notif_type,
        "message": message,
        "related_application_id": related_application_id,
        "is_read": False,
        "created_date": datetime.now(timezone.utc),
    }
    await db.notifications.insert_one(doc)
    return doc


async def broadcast_to_role(
    role: str,
    notif_type: str,
    message: str,
    related_application_id: str = None,
) -> list:
    """Create one notification per ACTIVE user of the given role (e.g. every SUPERADMIN)."""
    db = get_db()
    created = []
    async for user in db.users.find({"role": role, "status": "ACTIVE"}):
        doc = await create_notification(
            recipient_user_id=user["user_id"],
            notif_type=notif_type,
            message=message,
            related_application_id=related_application_id,
        )
        created.append(doc)
    return created


async def notify_admins(
    notif_type: str,
    message: str,
    related_application_id: str = None,
) -> list:
    """
    Broadcast to every ACTIVE admin user -- both SUPERADMIN and SUBADMIN --
    so events created from either portal (a leave request, a new
    application, an approval/rejection) show up in both portals'
    notification inboxes. SubAdmin shares the same admin-facing ERP data as
    SuperAdmin, so it should share these cross-role notifications too.
    """
    created = []
    for role in ("SUPERADMIN", "SUBADMIN"):
        created.extend(await broadcast_to_role(role, notif_type, message, related_application_id))
    return created


async def list_notifications(recipient_user_id: str) -> list:
    db = get_db()
    cursor = db.notifications.find({"recipient_user_id": recipient_user_id}).sort("created_date", -1)
    results = []
    async for doc in cursor:
        doc.pop("_id", None)
        results.append(doc)
    return results


async def mark_notification_read(notification_id: str, recipient_user_id: str) -> dict:
    db = get_db()
    result = await db.notifications.find_one_and_update(
        {"notification_id": notification_id, "recipient_user_id": recipient_user_id},
        {"$set": {"is_read": True}},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    result.pop("_id", None)
    return result


async def mark_all_read(recipient_user_id: str) -> dict:
    db = get_db()
    result = await db.notifications.update_many(
        {"recipient_user_id": recipient_user_id, "is_read": False},
        {"$set": {"is_read": True}},
    )
    return {"updated": result.modified_count}
