"""
Registration link management service.
Generates cryptographically secure tokens for the future public Employee
Registration Form. Only the token HASH is stored in MongoDB — the raw token
is returned once, embedded in the shareable URL, at creation time.
"""
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status

from config import settings
from database.mongodb import get_db
from utils.security import generate_secure_token, hash_token, generate_id
from services.audit_service import log_action


async def create_registration_link(expires_in_days: int, note: str, actor: dict) -> dict:
    db = get_db()
    raw_token = generate_secure_token()
    token_hash = hash_token(raw_token)
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(days=expires_in_days)

    doc = {
        "link_id": generate_id("LNK"),
        "token_hash": token_hash,
        "status": "ACTIVE",
        "created_by": actor["user_id"],
        "created_date": now,
        "expiry_date": expiry,
        "used_count": 0,
        "note": note,
    }
    await db.registration_links.insert_one(doc)

    await log_action(actor["user_id"], actor["role"], "CREATE_REGISTRATION_LINK", "registration_link", doc["link_id"])

    url = f"{settings.EMPLOYEE_PORTAL_URL}/register?token={raw_token}"
    doc.pop("_id", None)
    doc.pop("token_hash", None)
    doc["url"] = url
    return doc


async def list_registration_links() -> list:
    db = get_db()
    cursor = db.registration_links.find({}).sort("created_date", -1)
    results = []
    now = datetime.now(timezone.utc)
    async for doc in cursor:
        doc.pop("_id", None)
        doc.pop("token_hash", None)
        # Compute effective status: EXPIRED overrides stale ACTIVE flag if past expiry
        if doc["status"] == "ACTIVE" and doc["expiry_date"].replace(tzinfo=timezone.utc) < now:
            doc["status"] = "EXPIRED"
        results.append(doc)
    return results


async def validate_and_consume_token(raw_token: str) -> None:
    """Validate a public registration link token (if the Employee Registration
    Form was reached via a SuperAdmin-generated link) and bump its usage count.
    Raises HTTPException if the token is unknown, disabled or expired.
    Registration tokens are optional -- open registration is also supported --
    so callers should only invoke this when a token was actually supplied."""
    db = get_db()
    token_hash = hash_token(raw_token)
    link = await db.registration_links.find_one({"token_hash": token_hash})
    if not link:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid registration link")
    if link["status"] != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This registration link is no longer active")
    now = datetime.now(timezone.utc)
    if link["expiry_date"].replace(tzinfo=timezone.utc) < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This registration link has expired")

    await db.registration_links.update_one({"link_id": link["link_id"]}, {"$inc": {"used_count": 1}})


async def disable_registration_link(link_id: str, actor: dict) -> dict:
    db = get_db()
    result = await db.registration_links.find_one_and_update(
        {"link_id": link_id},
        {"$set": {"status": "DISABLED"}},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration link not found")

    await log_action(actor["user_id"], actor["role"], "DISABLE_REGISTRATION_LINK", "registration_link", link_id)
    result.pop("_id", None)
    result.pop("token_hash", None)
    return result
