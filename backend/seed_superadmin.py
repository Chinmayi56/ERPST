"""
Seeds the ONE demo SuperAdmin account into MongoDB, and keeps it usable.

- Idempotent: running this multiple times never creates duplicate accounts.
- Self-healing: if a SuperAdmin record already exists for the demo email but
  its password hash does not match the configured demo password (e.g. an
  earlier run used a different SEED_SUPERADMIN_PASSWORD, or the record was
  edited by hand), the hash is regenerated and updated in place. The
  existing user_id and every other field are preserved -- the account is
  synchronized, never replaced.
- Connects through database/mongodb.py, the exact same connection module the
  running FastAPI app uses (same MONGO_URL / DB_NAME / `users` collection),
  so this can never seed a different database than the API reads from.
- Passwords are hashed with bcrypt via utils/security.py -- the project's
  existing hashing utility, not a second implementation. The plain password
  is never written to the database.

Usage:
    python seed_superadmin.py
"""
import asyncio
from datetime import datetime, timezone

from config import settings
from database.mongodb import connect_to_mongo, close_mongo_connection, get_db
from utils.security import hash_password, verify_password, generate_id


async def seed_core(db) -> None:
    """The actual seeding logic, taking an already-connected db handle.

    Split out from seed() so server.py's startup lifespan can run this same,
    already-idempotent/self-healing logic automatically on every boot --
    mirroring seed_subadmin.py / seed_demo_employee.py exactly. This is the
    fix for SuperAdmin login failing with "Invalid email or password" in a
    fresh production deployment: previously the SuperAdmin account only
    ever existed if someone manually ran `python seed_superadmin.py` on the
    Render host (a separate, easy-to-skip step); if that step was never run,
    no `users` record exists at all, so login_with_email_password's
    `if not user` branch is hit on every attempt no matter how correct the
    email/password are. Calling this on every startup guarantees the
    SuperAdmin account always exists and always matches
    SEED_SUPERADMIN_EMAIL/PASSWORD, without ever creating a duplicate or
    touching unrelated fields.
    """
    existing = await db.users.find_one({"email": settings.SEED_SUPERADMIN_EMAIL})

    if not existing:
        user_doc = {
            "user_id": generate_id("USR"),
            "name": settings.SEED_SUPERADMIN_NAME,
            "email": settings.SEED_SUPERADMIN_EMAIL,
            "mobile": settings.SEED_SUPERADMIN_MOBILE,
            "password_hash": hash_password(settings.SEED_SUPERADMIN_PASSWORD),
            "role": "SUPERADMIN",
            "status": "ACTIVE",
            "created_date": datetime.now(timezone.utc),
        }
        await db.users.insert_one(user_doc)
        print("[seed] Demo SuperAdmin created successfully.")
    else:
        print("SuperAdmin exists.")
        print("Verifying password...")

        updates = {}

        password_ok = verify_password(settings.SEED_SUPERADMIN_PASSWORD, existing.get("password_hash", ""))
        if not password_ok:
            print("Password mismatch detected.")
            print("Updating SuperAdmin password hash...")
            updates["password_hash"] = hash_password(settings.SEED_SUPERADMIN_PASSWORD)
        else:
            print("Password verified.")

        # Ensure role/status invariants without touching anything else --
        # user_id and all other existing fields are preserved as-is.
        if existing.get("role") != "SUPERADMIN":
            updates["role"] = "SUPERADMIN"
        if existing.get("status") != "ACTIVE":
            updates["status"] = "ACTIVE"
        # `is_active` is not part of this project's user schema (only
        # `status` is used), so there is nothing further to normalize there.

        if updates:
            await db.users.update_one({"_id": existing["_id"]}, {"$set": updates})
            print("SuperAdmin account synchronized successfully.")
        else:
            print("SuperAdmin demo account is already configured correctly.")

    # Never print the password or password hash (see project security
    # rules) -- only confirm the non-secret identifiers so an operator can
    # tell the account is ready without any secret ever hitting logs.
    print("[seed] SuperAdmin ready.")
    print(f"[seed]   Email:  {settings.SEED_SUPERADMIN_EMAIL}")
    print("[seed]   Status: ACTIVE")
    print("[seed]   Role:   SUPERADMIN")


async def seed():
    await connect_to_mongo()
    db = get_db()
    print("Checking SuperAdmin...")
    await seed_core(db)
    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(seed())
