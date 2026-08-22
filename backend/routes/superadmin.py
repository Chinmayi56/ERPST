"""
SuperAdmin dashboard route.
"""
from fastapi import APIRouter, Depends

from services.superadmin_service import get_dashboard_summary, list_users
from utils.dependencies import require_superadmin

router = APIRouter(prefix="/api/superadmin", tags=["SuperAdmin Dashboard"])


@router.get("/dashboard", summary="Real-time dashboard summary counts")
async def dashboard(current_user: dict = Depends(require_superadmin)):
    return await get_dashboard_summary()


@router.get("/users", summary="List all platform users (User & Role Management)")
async def get_users(current_user: dict = Depends(require_superadmin)):
    return await list_users()
