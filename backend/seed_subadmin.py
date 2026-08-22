"""
Seeds the ONE demo SubAdmin account into MongoDB, and keeps it usable.

Mirrors seed_superadmin.py exactly, for the SUBADMIN role instead:

- Idempotent: running this multiple times never creates duplicate accounts.
- Self-healing: if a SubAdmin record already exists for the demo email but
  its password hash does not match the configured demo password, the hash
  is regenerated and updated in place. The existing user_id and every other
  field are preserved -- the account is synchronized, never replaced.
- Connects through database/mongodb.py, the exact same connection module the
  running FastAPI app uses (same MONGO_URL / DB_NAME / `users` collection),
  so this can never seed a different database than the API reads from.
- Passwords are hashed with bcrypt via utils/security.py.
- Uses a different email/mobile/password from the SuperAdmin demo account
  (SEED_SUBADMIN_* in config.py) so SubAdmin credentials are never identical
  to SuperAdmin's, and the `users` collection's unique email/mobile indexes
  guarantee the two accounts can never collide.

Usage:
    python seed_subadmin.py
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
    without opening/closing a second Mongo connection on top of the app's
    own. This is the fix for SubAdmin login failing with "Invalid email or
    password": that account only ever existed if someone manually ran
    `python seed_subadmin.py` (a separate step from `seed_superadmin.py` in
    RUN_COMMANDS.txt, easy to skip); if that step was skipped, no `users`
    record for subadmin@strivenest.com exists at all, so
    services/auth_service.py::login_with_email_password correctly (per the
    existing auth code, unchanged here) falls through to the generic
    invalid-credentials message. No authentication logic changes -- the
    account now just always exists, created through the exact same direct
    `users` insert as before. Mirrors the equivalent fix already applied to
    the demo Employee account (see seed_demo_employee.py::seed_core).
    """
    if settings.ENVIRONMENT == "production" and settings.DEMO_MODE:
        print(
            "[seed] Refusing to seed the demo SubAdmin account: "
            "ENVIRONMENT=production with DEMO_MODE=true -- skipping."
        )
        return

    print("Checking SubAdmin...")
    existing = await db.users.find_one({"email": settings.SEED_SUBADMIN_EMAIL})

    if not existing:
        user_doc = {
            "user_id": generate_id("USR"),
            "name": settings.SEED_SUBADMIN_NAME,
            "email": settings.SEED_SUBADMIN_EMAIL,
            "mobile": settings.SEED_SUBADMIN_MOBILE,
            "password_hash": hash_password(settings.SEED_SUBADMIN_PASSWORD),
            "role": "SUBADMIN",
            "status": "ACTIVE",
            "created_date": datetime.now(timezone.utc),
        }
        await db.users.insert_one(user_doc)
        print("[seed] Demo SubAdmin created successfully.")
    else:
        print("SubAdmin exists.")
        print("Verifying password...")

        updates = {}

        password_ok = verify_password(settings.SEED_SUBADMIN_PASSWORD, existing.get("password_hash", ""))
        if not password_ok:
            print("Password mismatch detected.")
            print("Updating SubAdmin password hash...")
            updates["password_hash"] = hash_password(settings.SEED_SUBADMIN_PASSWORD)
        else:
            print("Password verified.")

        # Ensure role/status invariants without touching anything else --
        # user_id and all other existing fields are preserved as-is.
        if existing.get("role") != "SUBADMIN":
            updates["role"] = "SUBADMIN"
        if existing.get("status") != "ACTIVE":
            updates["status"] = "ACTIVE"

        if updates:
            await db.users.update_one({"_id": existing["_id"]}, {"$set": updates})
            print("SubAdmin account synchronized successfully.")
        else:
            print("SubAdmin demo account is already configured correctly.")

    print("[seed] Demo SubAdmin ready.")
    print(f"[seed]   Demo Email:    {settings.SEED_SUBADMIN_EMAIL}")
    # Never print the password or password hash -- see seed_superadmin.py.
    print("[seed]   Status: ACTIVE")
    print("[seed]   Role:   SUBADMIN")
    print(f"[seed]   Demo OTP for mobile login: {settings.DEMO_OTP}")


async def seed():
    """CLI entrypoint (python seed_subadmin.py) -- unchanged behavior,
    now just delegates to seed_core() for the actual logic."""
    await connect_to_mongo()
    db = get_db()
    await seed_core(db)
    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(seed())
