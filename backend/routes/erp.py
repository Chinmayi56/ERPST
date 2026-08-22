"""
ERP module routes (clients, projects, tasks, leaves, attendance, services,
bookings, documents), shared between SuperAdmin and SubAdmin.

`build_erp_router()` is the SINGLE implementation of every ERP endpoint.
`router` (SuperAdmin, /api/superadmin/erp, require_superadmin) and
`subadmin_router` (SubAdmin, /api/subadmin/erp, require_subadmin) are both
built from it, so the two portals are guaranteed to behave identically and
read/write the exact same MongoDB collections -- there is no duplicated
logic to drift out of sync, and no separate SubAdmin database or
`subadmin_*` collections are ever created.
"""
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field
from pymongo import ReturnDocument

from database.mongodb import get_db
from utils.dependencies import require_superadmin, require_subadmin
from config import settings
from services.audit_service import log_action
from services.notification_service import notify_admins

MODULES = {"clients", "projects", "tasks", "leaves", "attendance", "services", "bookings", "documents"}
ID_FIELDS = {
    "clients": "client_id", "projects": "project_id", "tasks": "task_id", "leaves": "leave_id",
    "attendance": "attendance_id", "services": "service_id", "bookings": "booking_id",
    "documents": "document_id",
}

STATUS_VALUES = {
    "clients": {"ACTIVE", "INACTIVE"},
    "projects": {"PLANNED", "ACTIVE", "IN_PROGRESS", "ON_HOLD", "COMPLETED", "CANCELLED"},
    "tasks": {"TODO", "IN_PROGRESS", "REVIEW", "COMPLETED", "BLOCKED"},
    "leaves": {"PENDING", "APPROVED", "REJECTED"},
    "attendance": {"PRESENT", "ABSENT", "LATE", "HALF_DAY", "LEAVE"},
    "services": {"ACTIVE", "INACTIVE"},
    "bookings": {"PENDING", "CONFIRMED", "COMPLETED", "CANCELLED"},
    "documents": {"ACTIVE", "ARCHIVED"},
}

DEFAULT_STATUS = {
    "clients": "ACTIVE", "projects": "PLANNED", "tasks": "TODO", "leaves": "PENDING",
    "attendance": "PRESENT", "services": "ACTIVE", "bookings": "PENDING", "documents": "ACTIVE",
}

SEARCH_FIELDS = {
    "clients": ["name", "company_name", "contact_person", "email", "phone"],
    "projects": ["name", "client_name", "project_code", "priority"],
    "tasks": ["title", "project_name", "employee_name", "priority", "status"],
    "leaves": ["employee_name", "employee_id", "leave_type", "reason"],
    "attendance": ["employee_name", "employee_id", "date", "status"],
    "services": ["name", "description", "category"],
    "bookings": ["client_name", "service_name", "employee_name", "booking_date", "status"],
    "documents": ["name", "type", "owner_name", "owner_type"],
}

class RecordPayload(BaseModel):
    data: Dict[str, Any] = Field(default_factory=dict)

class StatusPayload(BaseModel):
    status: str


def clean(doc: Optional[dict]):
    if not doc:
        return None
    doc.pop("_id", None)
    return doc


def normalize(data: dict) -> dict:
    return {k: v for k, v in data.items() if v is not None and v != ""}


def validate(module: str, data: dict):
    status = data.get("status")
    if status and status not in STATUS_VALUES[module]:
        raise HTTPException(400, f"Invalid {module} status: {status}")
    if module == "clients" and not (data.get("name") or data.get("company_name")):
        raise HTTPException(400, "Client name or company name is required")
    if module == "projects" and not data.get("name"):
        raise HTTPException(400, "Project name is required")
    if module == "tasks" and not data.get("title"):
        raise HTTPException(400, "Task title is required")
    if module == "tasks" and data.get("progress") not in (None, ""):
        try:
            progress = float(data["progress"])
        except (TypeError, ValueError):
            raise HTTPException(400, "Progress must be a number between 0 and 100")
        if progress < 0 or progress > 100:
            raise HTTPException(400, "Progress must be between 0 and 100")
    if module == "services" and not data.get("name"):
        raise HTTPException(400, "Service name is required")
    if module == "bookings" and not data.get("client_name"):
        raise HTTPException(400, "Client is required for a booking")
    if module == "leaves" and not data.get("employee_name"):
        raise HTTPException(400, "Employee is required for a leave request")
    if module == "attendance" and not data.get("employee_name"):
        raise HTTPException(400, "Employee is required for attendance")


def build_erp_router(prefix: str, require_role: Callable) -> APIRouter:
    """
    Build one complete ERP router (options endpoints + full CRUD for every
    module) gated by `require_role`. Called once per portal so SuperAdmin
    and SubAdmin get byte-for-byte identical behavior over the same
    collections -- the only difference between the two routers is which
    role dependency guards them.
    """
    router = APIRouter(prefix=prefix, tags=[f"{prefix.split('/')[2].title()} ERP"])

    @router.get("/options/employees")
    async def employee_options(current_user: dict = Depends(require_role)):
        cursor = get_db().employees.find({"status": "ACTIVE"}, {"_id": 0, "employee_id": 1, "full_name": 1, "email": 1}).sort("full_name", 1)
        return [doc async for doc in cursor]

    @router.get("/options/clients")
    async def client_options(current_user: dict = Depends(require_role)):
        cursor = get_db().clients.find({"status": "ACTIVE"}, {"_id": 0, "client_id": 1, "name": 1, "company_name": 1}).sort("company_name", 1)
        return [doc async for doc in cursor]

    @router.get("/options/services")
    async def service_options(current_user: dict = Depends(require_role)):
        cursor = get_db().services.find({"status": "ACTIVE"}, {"_id": 0, "service_id": 1, "name": 1}).sort("name", 1)
        return [doc async for doc in cursor]

    @router.get("/options/projects")
    async def project_options(current_user: dict = Depends(require_role)):
        cursor = get_db().projects.find(
            {"status": {"$nin": ["COMPLETED", "CANCELLED"]}}, {"_id": 0, "project_id": 1, "name": 1}
        ).sort("name", 1)
        return [doc async for doc in cursor]

    @router.get("/{module}")
    async def list_records(
        module: str,
        q: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
        page: int = Query(1, ge=1),
        page_size: int = Query(25, ge=1, le=100),
        current_user: dict = Depends(require_role),
    ):
        if module not in MODULES:
            raise HTTPException(404, "Unknown ERP module")
        if status and status not in STATUS_VALUES[module]:
            raise HTTPException(400, "Invalid status filter")

        db = get_db()
        query: dict = {}
        if status:
            query["status"] = status
        if q:
            query["$or"] = [{f: {"$regex": q, "$options": "i"}} for f in SEARCH_FIELDS[module]]

        total = await db[module].count_documents(query)
        cursor = db[module].find(query).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size)
        items = []
        async for doc in cursor:
            items.append(clean(doc))
        return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": max(1, (total + page_size - 1) // page_size)}

    @router.get("/{module}/stats")
    async def module_stats(module: str, current_user: dict = Depends(require_role)):
        if module not in MODULES:
            raise HTTPException(404, "Unknown ERP module")
        db = get_db()
        stats = {status: await db[module].count_documents({"status": status}) for status in STATUS_VALUES[module]}
        stats["total"] = await db[module].count_documents({})
        return stats

    @router.post("/{module}")
    async def create_record(module: str, payload: RecordPayload, current_user: dict = Depends(require_role)):
        if module not in MODULES:
            raise HTTPException(404, "Unknown ERP module")
        data = normalize(dict(payload.data))
        validate(module, data)
        key = ID_FIELDS[module]
        now = datetime.now(timezone.utc)
        data.setdefault(key, f"{module[:3].upper()}-{uuid.uuid4().hex[:8].upper()}")
        data.setdefault("status", DEFAULT_STATUS[module])
        data.setdefault("created_at", now.isoformat())
        data["updated_at"] = now.isoformat()
        data["created_by"] = current_user.get("user_id")

        if module == "leaves":
            data["approval_history"] = [{"status": "PENDING", "by": current_user.get("email"), "at": now.isoformat()}]
        await get_db()[module].insert_one(data)
        await log_action(current_user.get("user_id"), current_user.get("role"), f"CREATE_{module.upper()}", module, data[key])
        if module == "leaves":
            await notify_admins("LEAVE_REQUEST", f"New leave request from {data.get('employee_name', 'employee')}")
        return clean(data)

    @router.put("/{module}/{record_id}")
    async def update_record(module: str, record_id: str, payload: RecordPayload, current_user: dict = Depends(require_role)):
        if module not in MODULES:
            raise HTTPException(404, "Unknown ERP module")
        key = ID_FIELDS[module]
        data = normalize(dict(payload.data))
        data.pop(key, None)
        validate(module, data)
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        result = await get_db()[module].find_one_and_update({key: record_id}, {"$set": data}, return_document=ReturnDocument.AFTER)
        if not result:
            raise HTTPException(404, "Record not found")
        await log_action(current_user.get("user_id"), current_user.get("role"), f"UPDATE_{module.upper()}", module, record_id)
        return clean(result)

    @router.delete("/{module}/{record_id}")
    async def delete_record(module: str, record_id: str, current_user: dict = Depends(require_role)):
        if module not in MODULES:
            raise HTTPException(404, "Unknown ERP module")
        key = ID_FIELDS[module]
        db = get_db()
        existing = await db[module].find_one({key: record_id})
        result = await db[module].delete_one({key: record_id})
        if not result.deleted_count:
            raise HTTPException(404, "Record not found")
        if module == "documents" and existing:
            # Best-effort cleanup of the uploaded file on disk. Never fails the
            # delete if the file is already gone or the URL isn't a local upload.
            url = existing.get("url") or ""
            if url.startswith("/uploads/"):
                stored_path = os.path.join(settings.UPLOAD_DIR, os.path.basename(url))
                try:
                    if os.path.isfile(stored_path):
                        os.remove(stored_path)
                except OSError:
                    pass
        await log_action(current_user.get("user_id"), current_user.get("role"), f"DELETE_{module.upper()}", module, record_id)
        return {"success": True, "id": record_id}

    @router.patch("/leaves/{record_id}/status")
    async def leave_status(record_id: str, payload: StatusPayload, current_user: dict = Depends(require_role)):
        if payload.status not in STATUS_VALUES["leaves"]:
            raise HTTPException(400, "Invalid leave status")
        now = datetime.now(timezone.utc).isoformat()
        db = get_db()
        result = await db.leaves.find_one_and_update(
            {"leave_id": record_id},
            {"$set": {"status": payload.status, "reviewed_by": current_user.get("email"), "reviewed_at": now},
             "$push": {"approval_history": {"status": payload.status, "by": current_user.get("email"), "at": now}}},
            return_document=ReturnDocument.AFTER,
        )
        if not result:
            raise HTTPException(404, "Leave request not found")
        await log_action(current_user.get("user_id"), current_user.get("role"), f"{payload.status}_LEAVE", "leaves", record_id)
        return clean(result)

    @router.patch("/{module}/{record_id}/status")
    async def update_status(module: str, record_id: str, payload: StatusPayload, current_user: dict = Depends(require_role)):
        if module not in MODULES:
            raise HTTPException(404, "Unknown ERP module")
        if payload.status not in STATUS_VALUES[module]:
            raise HTTPException(400, "Invalid status")
        key = ID_FIELDS[module]
        result = await get_db()[module].find_one_and_update({key: record_id}, {"$set": {"status": payload.status, "updated_at": datetime.now(timezone.utc).isoformat()}}, return_document=ReturnDocument.AFTER)
        if not result:
            raise HTTPException(404, "Record not found")
        await log_action(current_user.get("user_id"), current_user.get("role"), f"STATUS_{module.upper()}", module, record_id, {"status": payload.status})
        return clean(result)

    @router.post("/documents/upload")
    async def upload_document(file: UploadFile = File(...), current_user: dict = Depends(require_role)):
        ext = os.path.splitext(file.filename or "")[1].lower()
        allowed = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx", ".xls", ".xlsx", ".txt"}
        if ext not in allowed:
            raise HTTPException(400, "Unsupported document type")
        content = await file.read()
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(400, f"File too large. Maximum {settings.MAX_UPLOAD_SIZE_MB}MB")
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        stored = f"{uuid.uuid4().hex}{ext}"
        with open(os.path.join(settings.UPLOAD_DIR, stored), "wb") as handle:
            handle.write(content)
        return {"url": f"/uploads/{stored}", "filename": file.filename, "stored_filename": stored}

    return router


# SuperAdmin ERP: unchanged prefix, unchanged role gate, unchanged behavior.
router = build_erp_router("/api/superadmin/erp", require_superadmin)

# SubAdmin ERP: same implementation, same MongoDB collections, gated by
# require_subadmin instead. No separate database, no subadmin_* collections.
subadmin_router = build_erp_router("/api/subadmin/erp", require_subadmin)
