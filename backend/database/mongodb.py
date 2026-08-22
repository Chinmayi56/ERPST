"""
Motor (async MongoDB driver) connection management.
ONE MongoDB database for the whole Strivenest platform (superadmin/subadmin/employee).
"""
import logging
import sys
import uuid

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError, ServerSelectionTimeoutError

from config import settings

logger = logging.getLogger("strivenest.mongodb")

# Every ERP module collection that has a unique-indexed "business" ID field
# (as opposed to Mongo's own _id). Kept here -- not imported from
# routes/erp.py -- to avoid a routes -> database import cycle; the format
# ("<PREFIX>-<8 hex chars>") intentionally matches the one routes/erp.py's
# create_record() already generates, so a backfilled ID is indistinguishable
# from one created through the normal API.
ERP_ID_FIELDS = {
    "clients": "client_id",
    "projects": "project_id",
    "tasks": "task_id",
    "leaves": "leave_id",
    "attendance": "attendance_id",
    "services": "service_id",
    "bookings": "booking_id",
    "documents": "document_id",
}


class MongoDB:
    client: AsyncIOMotorClient = None
    db = None


mongodb = MongoDB()


async def connect_to_mongo():
    # A short serverSelectionTimeoutMS means that if MongoDB is not running
    # locally, startup fails fast with a clear error instead of hanging
    # silently during ensure_indexes() -- a hang here made every request
    # (including the browser's CORS preflight) time out with no response,
    # which shows up in DevTools as an unexplained "CORS error" even though
    # CORS itself was configured correctly.
    mongodb.client = AsyncIOMotorClient(
        settings.MONGO_URL,
        serverSelectionTimeoutMS=5000,
    )
    mongodb.db = mongodb.client[settings.DB_NAME]
    try:
        await mongodb.client.admin.command("ping")
    except ServerSelectionTimeoutError as exc:
        logger.error(
            "Could not connect to MongoDB at %s. Is MongoDB running? "
            "Start it before starting the API server. Original error: %s",
            settings.MONGO_URL,
            exc,
        )
        print(
            f"\n[STARTUP ERROR] Could not reach MongoDB at {settings.MONGO_URL}.\n"
            "Start MongoDB first (e.g. run `mongod`, or start the MongoDB service), "
            "then restart the backend.\n",
            file=sys.stderr,
        )
        raise
    await backfill_missing_erp_ids()
    await ensure_indexes()


async def close_mongo_connection():
    if mongodb.client:
        mongodb.client.close()


def get_db():
    return mongodb.db


async def backfill_missing_erp_ids():
    """
    One-time-per-document migration, safe to run on every startup.

    Root cause of `DuplicateKeyError ... project_id_1 ... dup key:
    { project_id: null }`: MongoDB's unique index treats every document that
    is *missing* the indexed field (or has it explicitly set to null) as
    having the value null. If two or more `projects` documents had no
    `project_id` -- e.g. rows inserted before this field was required, or a
    seed/import that didn't set it -- creating a unique index on
    `project_id` fails immediately, because Mongo sees two "duplicate" nulls.
    This is not specific to `projects`; every ERP module collection
    (clients, projects, leaves, attendance, services, bookings, documents)
    has the exact same unique-index-on-a-business-ID pattern in
    ensure_indexes() below, so the same failure could occur for any of them.

    This function must run BEFORE ensure_indexes() creates those unique
    indexes. It finds every document in each ERP collection whose ID field
    is missing or null and assigns it a fresh, collision-checked ID in the
    same "<PREFIX>-<8 hex chars>" format routes/erp.py already generates for
    new records -- no existing document is deleted or otherwise modified,
    and no project/client/etc. data is touched other than filling in the
    one missing field.

    Idempotent by construction: the query is `{field: null} OR
    {field: {$exists: false}}`, so once every document has a real ID, this
    function matches zero documents and does nothing on every subsequent
    startup -- it never re-generates or overwrites an ID that already exists.
    """
    db = mongodb.db
    for collection_name, field in ERP_ID_FIELDS.items():
        collection = db[collection_name]
        prefix = collection_name[:3].upper()
        fixed = 0
        cursor = collection.find({"$or": [{field: None}, {field: {"$exists": False}}]})
        async for doc in cursor:
            new_id = f"{prefix}-{uuid.uuid4().hex[:8].upper()}"
            # Astronomically unlikely, but guard against a generated ID
            # colliding with one that already exists on another document.
            while await collection.find_one({field: new_id}, {"_id": 1}):
                new_id = f"{prefix}-{uuid.uuid4().hex[:8].upper()}"
            await collection.update_one({"_id": doc["_id"]}, {"$set": {field: new_id}})
            fixed += 1
        if fixed:
            message = (
                f"[startup] Backfilled {fixed} existing '{collection_name}' "
                f"document(s) that had a missing/null {field}."
            )
            print(message)
            logger.info(message)


async def ensure_indexes():
    """Create indexes required for correctness and performance. Safe to run repeatedly."""
    db = mongodb.db

    # users
    await db.users.create_index("email", unique=True)
    await db.users.create_index("mobile", unique=True)

    # employee_applications
    await db.employee_applications.create_index("application_id", unique=True)
    await db.employee_applications.create_index("status")
    await db.employee_applications.create_index("email")
    await db.employee_applications.create_index("submitted_date")

    # employees
    await db.employees.create_index("employee_id", unique=True)
    await db.employees.create_index("email", unique=True)
    await db.employees.create_index("status")
    await db.employees.create_index("source_application_id", unique=True, sparse=True)
    await db.employees.create_index("user_id", unique=True, sparse=True)

    # registration_links
    await db.registration_links.create_index("link_id", unique=True)
    await db.registration_links.create_index("token_hash", unique=True)
    await db.registration_links.create_index("status")

    # notifications
    await db.notifications.create_index("notification_id", unique=True)
    await db.notifications.create_index("recipient_user_id")
    await db.notifications.create_index("is_read")
    await db.notifications.create_index("created_date")

    # ERP modules
    for collection, field in ERP_ID_FIELDS.items():
        try:
            await db[collection].create_index(field, unique=True)
        except DuplicateKeyError:
            # Defense in depth: backfill_missing_erp_ids() above already
            # handles the documented cause of this (missing/null IDs), so
            # this should not normally trigger. If it does anyway -- e.g. a
            # document was inserted between the backfill and this call --
            # retry the backfill once for this collection and try again
            # instead of taking down the whole app on startup.
            logger.warning(
                "Unique index creation on %s.%s hit a duplicate key; "
                "re-running the ID backfill once and retrying.",
                collection,
                field,
            )
            await backfill_missing_erp_ids()
            await db[collection].create_index(field, unique=True)
        await db[collection].create_index("status")
        await db[collection].create_index("created_at")
    await db.projects.create_index("client_id")
    await db.projects.create_index("assigned_employee_ids")
    await db.tasks.create_index("project_id")
    await db.tasks.create_index("employee_id")
    await db.tasks.create_index("due_date")
    await db.leaves.create_index("employee_id")
    await db.leaves.create_index("start_date")
    await db.attendance.create_index([("employee_id", 1), ("date", -1)])
    await db.bookings.create_index([("booking_date", -1), ("status", 1)])
    await db.documents.create_index([("owner_type", 1), ("owner_id", 1)])

    # audit_logs
    await db.audit_logs.create_index("audit_id", unique=True)
    await db.audit_logs.create_index("user_id")
    await db.audit_logs.create_index("timestamp")
