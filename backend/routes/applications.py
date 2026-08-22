"""
Employee application review routes, shared between SuperAdmin and SubAdmin.
"""
from typing import Callable, Optional
from fastapi import APIRouter, Depends, Query

from models.application import RejectApplicationRequest
from services import application_service
from utils.dependencies import require_superadmin, require_subadmin


def build_applications_router(prefix: str, require_role: Callable) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=["Employee Applications"])

    @router.get("", summary="List employee applications (optionally filtered by status)")
    async def get_applications(
        status: Optional[str] = Query(None, description="PENDING, APPROVED or REJECTED"),
        current_user: dict = Depends(require_role),
    ):
        return await application_service.list_applications(status)

    @router.get("/{application_id}", summary="Get full application details")
    async def get_application_detail(application_id: str, current_user: dict = Depends(require_role)):
        return await application_service.get_application(application_id)

    @router.post("/{application_id}/approve", summary="Approve a pending application")
    async def approve_application(application_id: str, current_user: dict = Depends(require_role)):
        return await application_service.approve_application(application_id, current_user)

    @router.post("/{application_id}/reject", summary="Reject a pending application (reason required)")
    async def reject_application(
        application_id: str,
        payload: RejectApplicationRequest,
        current_user: dict = Depends(require_role),
    ):
        return await application_service.reject_application(application_id, payload.reason, current_user)

    return router


# SuperAdmin: unchanged prefix, unchanged role gate, unchanged behavior.
router = build_applications_router("/api/superadmin/applications", require_superadmin)

# SubAdmin: identical implementation, same `employee_applications` collection.
subadmin_router = build_applications_router("/api/subadmin/applications", require_subadmin)
