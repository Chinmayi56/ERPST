"""
Public-facing Employee Application API, per spec:
  POST   /api/employee-applications                (public — employee submits)
  GET    /api/employee-applications                 (SuperAdmin only)
  GET    /api/employee-applications/{id}             (SuperAdmin only)
  POST   /api/employee-applications/{id}/approve     (SuperAdmin only)
  POST   /api/employee-applications/{id}/reject      (SuperAdmin only)

This is a thin, spec-shaped alias over the same service layer used by the
existing /api/superadmin/applications routes, so nothing already shipped is
broken -- both route sets share one source of truth in MongoDB.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query

from models.application import ApplicationCreateRequest, RejectApplicationRequest
from services import application_service
from services.registration_service import validate_and_consume_token
from utils.dependencies import require_superadmin

router = APIRouter(prefix="/api/employee-applications", tags=["Employee Registration"])


@router.post("", summary="Submit a new employee application (public)")
async def submit_application(payload: ApplicationCreateRequest):
    if payload.registration_token:
        await validate_and_consume_token(payload.registration_token)
    return await application_service.create_application(payload.model_dump())


@router.get("", summary="List employee applications (SuperAdmin only)")
async def get_applications(
    status: Optional[str] = Query(None, description="PENDING, UNDER_REVIEW, APPROVED or REJECTED"),
    current_user: dict = Depends(require_superadmin),
):
    return await application_service.list_applications(status)


@router.get("/{application_id}", summary="Get full application details (SuperAdmin only)")
async def get_application_detail(application_id: str, current_user: dict = Depends(require_superadmin)):
    return await application_service.get_application(application_id)


@router.post("/{application_id}/approve", summary="Approve a pending application (SuperAdmin only)")
async def approve_application(application_id: str, current_user: dict = Depends(require_superadmin)):
    return await application_service.approve_application(application_id, current_user)


@router.post("/{application_id}/reject", summary="Reject a pending application (SuperAdmin only, reason required)")
async def reject_application(
    application_id: str,
    payload: RejectApplicationRequest,
    current_user: dict = Depends(require_superadmin),
):
    return await application_service.reject_application(application_id, payload.reason, current_user)
