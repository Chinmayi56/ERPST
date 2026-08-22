"""
Employee Portal routes — everything an authenticated EMPLOYEE can see about
themselves. All routes are gated by `require_employee` (role check) and every
lookup is scoped to the caller's own `user_id`, so an employee can never read
another employee's data and never reach SuperAdmin-only endpoints.
"""
from fastapi import APIRouter, Depends

from services import employee_portal_service, notification_service
from utils.dependencies import require_employee

router = APIRouter(prefix="/api/employee", tags=["Employee Portal"])


@router.get("/dashboard", summary="Get the logged-in employee's dashboard summary")
async def get_my_dashboard(current_user: dict = Depends(require_employee)):
    return await employee_portal_service.get_dashboard(current_user)


@router.get("/profile", summary="Get the logged-in employee's full profile")
async def get_my_profile(current_user: dict = Depends(require_employee)):
    return await employee_portal_service.get_profile(current_user)


@router.get("/notifications", summary="List notifications for the logged-in employee")
async def get_my_notifications(current_user: dict = Depends(require_employee)):
    return await notification_service.list_notifications(current_user["user_id"])


@router.patch("/notifications/read-all", summary="Mark all of the employee's notifications as read")
async def mark_all_my_notifications_read(current_user: dict = Depends(require_employee)):
    return await notification_service.mark_all_read(current_user["user_id"])


@router.patch("/notifications/{notification_id}/read", summary="Mark one notification as read")
async def mark_my_notification_read(notification_id: str, current_user: dict = Depends(require_employee)):
    return await notification_service.mark_notification_read(notification_id, current_user["user_id"])
