"""
Employee management routes, shared between SuperAdmin and SubAdmin.

`build_employees_router()` is the single implementation; `router` /
`public_router` (SuperAdmin, unchanged) and `subadmin_router` /
`subadmin_public_router` (SubAdmin) are built from it so both portals read
and write the exact same `employees` collection through identical logic.
"""
from typing import Callable, Optional
from fastapi import APIRouter, Depends, Query

from models.employee import EmployeeUpdateRequest, EmployeeStatusUpdateRequest
from services import employee_service
from utils.dependencies import require_superadmin, require_subadmin


def build_employees_router(prefix: str, require_role: Callable) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=["Employees"])

    @router.get("", summary="List employees (optionally filtered by status)")
    async def get_employees(
        status: Optional[str] = Query(None, description="ACTIVE or DISABLED"),
        current_user: dict = Depends(require_role),
    ):
        return await employee_service.list_employees(status)

    @router.get("/{employee_id}", summary="Get employee details")
    async def get_employee_detail(employee_id: str, current_user: dict = Depends(require_role)):
        return await employee_service.get_employee(employee_id)

    @router.patch("/{employee_id}", summary="Update employee fields")
    async def update_employee(
        employee_id: str,
        payload: EmployeeUpdateRequest,
        current_user: dict = Depends(require_role),
    ):
        return await employee_service.update_employee(employee_id, payload.model_dump(), current_user)

    @router.post("/{employee_id}/disable", summary="Disable an employee account")
    async def disable_employee(employee_id: str, current_user: dict = Depends(require_role)):
        return await employee_service.disable_employee(employee_id, current_user)

    return router


def build_employees_public_router(prefix: str, require_role: Callable) -> APIRouter:
    """Spec-shaped alias router: GET/PUT /{prefix}, PATCH /{prefix}/{id}/status."""
    public_router = APIRouter(prefix=prefix, tags=["Employees"])

    @public_router.get("", summary="List employees")
    async def list_employees(
        status: Optional[str] = Query(None, description="ACTIVE or DISABLED"),
        current_user: dict = Depends(require_role),
    ):
        return await employee_service.list_employees(status)

    @public_router.get("/{employee_id}", summary="Get employee details")
    async def get_employee(employee_id: str, current_user: dict = Depends(require_role)):
        return await employee_service.get_employee(employee_id)

    @public_router.put("/{employee_id}", summary="Update employee fields")
    async def put_employee(
        employee_id: str,
        payload: EmployeeUpdateRequest,
        current_user: dict = Depends(require_role),
    ):
        updates = payload.model_dump(exclude={"status"})
        return await employee_service.update_employee(employee_id, updates, current_user)

    @public_router.patch("/{employee_id}/status", summary="Activate or deactivate an employee")
    async def patch_employee_status(
        employee_id: str,
        payload: EmployeeStatusUpdateRequest,
        current_user: dict = Depends(require_role),
    ):
        return await employee_service.set_employee_status(employee_id, payload.status, current_user)

    return public_router


# SuperAdmin: unchanged prefixes, unchanged role gate, unchanged behavior.
router = build_employees_router("/api/superadmin/employees", require_superadmin)
public_router = build_employees_public_router("/api/employees", require_superadmin)

# SubAdmin: identical implementation, same `employees` collection, gated by
# require_subadmin. Uses its own prefix so it never collides with the
# SuperAdmin-only /api/employees alias router above.
subadmin_router = build_employees_router("/api/subadmin/employees", require_subadmin)
