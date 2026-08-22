"""
Notification routes, shared between SuperAdmin and SubAdmin.
`notification_service` is already keyed purely by `recipient_user_id`
(role-agnostic), so both routers just call it with the authenticated
user's own user_id -- a SubAdmin only ever sees notifications addressed to
their own account, exactly like SuperAdmin.
"""
from typing import Callable
from fastapi import APIRouter, Depends

from services import notification_service
from utils.dependencies import require_superadmin, require_subadmin


def build_notifications_router(prefix: str, require_role: Callable) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=["Notifications"])

    @router.get("", summary="List notifications for the authenticated user")
    async def get_notifications(current_user: dict = Depends(require_role)):
        return await notification_service.list_notifications(current_user["user_id"])

    @router.patch("/{notification_id}/read", summary="Mark a notification as read")
    async def mark_read(notification_id: str, current_user: dict = Depends(require_role)):
        return await notification_service.mark_notification_read(notification_id, current_user["user_id"])

    return router


# SuperAdmin: unchanged prefix, unchanged role gate, unchanged behavior.
router = build_notifications_router("/api/superadmin/notifications", require_superadmin)

# SubAdmin: identical implementation, same `notifications` collection.
subadmin_router = build_notifications_router("/api/subadmin/notifications", require_subadmin)
