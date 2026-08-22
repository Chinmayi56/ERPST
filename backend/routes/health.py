"""
Health check route — used to verify the API and MongoDB connection are up.
"""
from fastapi import APIRouter
from database.mongodb import get_db

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health", summary="API and database health check")
async def health_check():
    db_status = "unknown"
    try:
        db = get_db()
        await db.command("ping")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "ok",
        "service": "Strivenest Technologies SuperAdmin API",
        "database": db_status,
    }
