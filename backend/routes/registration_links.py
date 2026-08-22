"""
Registration link (Employee Registration Form link) management routes,
shared between SuperAdmin and SubAdmin.
"""
from typing import Callable
from fastapi import APIRouter, Depends

from models.registration_link import CreateRegistrationLinkRequest
from services import registration_service
from utils.dependencies import require_superadmin, require_subadmin


def build_registration_links_router(prefix: str, require_role: Callable) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=["Registration Links"])

    @router.post("", summary="Generate a new secure registration link")
    async def create_link(payload: CreateRegistrationLinkRequest, current_user: dict = Depends(require_role)):
        return await registration_service.create_registration_link(
            payload.expires_in_days, payload.note, current_user
        )

    @router.get("", summary="List all registration links")
    async def get_links(current_user: dict = Depends(require_role)):
        return await registration_service.list_registration_links()

    @router.post("/{link_id}/disable", summary="Disable a registration link")
    async def disable_link(link_id: str, current_user: dict = Depends(require_role)):
        return await registration_service.disable_registration_link(link_id, current_user)

    return router


# SuperAdmin: unchanged prefix, unchanged role gate, unchanged behavior.
router = build_registration_links_router("/api/superadmin/registration-links", require_superadmin)

# SubAdmin: identical implementation, same `registration_links` collection.
subadmin_router = build_registration_links_router("/api/subadmin/registration-links", require_subadmin)
