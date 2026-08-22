"""
Audit logging service. Records important actions to the `audit_logs` collection.
Never log passwords, OTP secrets, JWT secrets or database credentials.
"""
from datetime import datetime, timezone
from typing import Optional
from database.mongodb import get_db
from utils.security import generate_id


async def log_action(
    user_id: str,
    role: str,
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[dict] = None,
):
    db = get_db()
    entry = {
        "audit_id": generate_id("AUD"),
        "user_id": user_id,
        "role": role,
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "timestamp": datetime.now(timezone.utc),
        "details": details or {},
    }
    await db.audit_logs.insert_one(entry)
    return entry
