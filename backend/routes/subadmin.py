"""
SubAdmin dashboard route.

Reuses `services.superadmin_service` (get_dashboard_summary / list_users)
unchanged -- both functions already aggregate live counts across the shared
MongoDB collections with no role filtering baked in, so SubAdmin sees the
exact same real-time numbers SuperAdmin does. Nothing is hardcoded.

`list_users` returns every platform user (including SUPERADMIN accounts),
which is fine here: it is read-only (no endpoint exists anywhere in this
backend that lets a caller change a user's role), so surfacing it to
SubAdmin cannot be used to self-elevate to SUPERADMIN.
"""
from fastapi import APIRouter, Depends

from services.superadmin_service import get_dashboard_summary, list_users
from utils.dependencies import require_subadmin

router = APIRouter(prefix="/api/subadmin", tags=["SubAdmin Dashboard"])


@router.get("/dashboard", summary="Real-time dashboard summary counts")
async def dashboard(current_user: dict = Depends(require_subadmin)):
    return await get_dashboard_summary()


@router.get("/users", summary="List all platform users (read-only; User & Role Management)")
async def get_users(current_user: dict = Depends(require_subadmin)):
    return await list_users()
