"""
Seeds ONE demo Employee account, and keeps it usable.

Unlike SuperAdmin (a direct `users` insert), an employee login account can
only ever come into existence through the real application -> SuperAdmin
approval flow (see services/application_service.py). This script walks that
exact flow -- submitting a demo application and approving it with the seeded
SuperAdmin as reviewer -- instead of inserting a parallel/duplicate auth
record. This keeps a single source of truth for how employee accounts get
created.

- Idempotent: running this multiple times never creates duplicates.
- Self-healing: if the demo Employee's `users` record already exists but its
  password hash does not match the configured demo password (e.g. an
  earlier run used a different SEED_EMPLOYEE_PASSWORD, or the record was
  edited by hand), the hash is regenerated and updated in place -- the same
  targeted fix seed_superadmin.py applies, reusing the same hashing utility.
  No new login/authentication logic is introduced; only the stored hash on
  the existing record is corrected.
- Requires the demo SuperAdmin to already exist (run seed_superadmin.py
  first), since approval requires a reviewer.
- Passwords are hashed with bcrypt via utils/security.py. The plain password
  is never written to the database.

Usage:
    python seed_demo_employee.py
"""
import asyncio

from config import settings
from database.mongodb import connect_to_mongo, close_mongo_connection, get_db
from services import application_service
from utils.security import hash_password, verify_password


async def seed_core(db) -> None:
    """The actual seeding logic, taking an already-connected db handle.
    Split out from seed() so server.py's startup lifespan can run this same,
    already-idempotent/self-healing logic automatically on every boot --
    without opening/closing a second Mongo connection on top of the app's
    own. This is the fix for demo Employee login failing with "Invalid email
    or password": that account only ever existed if someone manually ran
    `python seed_demo_employee.py` after `seed_superadmin.py`; if that step
    was skipped, no `users`/`employees`/`employee_applications` record for
    nithin@strivenest.com exists at all, so login correctly (per the
    existing auth code) falls through to the generic invalid-credentials
    message. No authentication logic changes -- the account now just always
    exists, created through the exact same real
    application -> SuperAdmin-approval flow as before.
    """
    print("Checking demo Employee...")
    existing_employee = await db.employees.find_one({"email": settings.SEED_EMPLOYEE_EMAIL})

    if not existing_employee:
        reviewer = await db.users.find_one({"email": settings.SEED_SUPERADMIN_EMAIL, "role": "SUPERADMIN"})
        if not reviewer:
            print("[seed] Demo SuperAdmin not found. Run seed_superadmin.py first — skipping.")
            return

        existing_application = await db.employee_applications.find_one({"email": settings.SEED_EMPLOYEE_EMAIL})
        if existing_application:
            application_id = existing_application["application_id"]
            if existing_application["status"] != "APPROVED":
                await application_service.approve_application(application_id, reviewer)
                print("[seed] Existing demo application approved.")
        else:
            application = await application_service.create_application({
                "full_name": settings.SEED_EMPLOYEE_NAME,
                "email": settings.SEED_EMPLOYEE_EMAIL,
                "password": settings.SEED_EMPLOYEE_PASSWORD,
                "mobile": settings.SEED_EMPLOYEE_MOBILE,
                "dob": "1998-01-01",
                "gender": "Other",
                "address": "Demo Address, Bengaluru",
                "department": "Engineering",
                "designation": "Software Engineer",
                "qualification": "B.Tech",
                "experience": "2 years",
            })
            await application_service.approve_application(application["application_id"], reviewer)
            print("[seed] Demo Employee application submitted and approved.")

        existing_employee = await db.employees.find_one({"email": settings.SEED_EMPLOYEE_EMAIL})
    else:
        print("Demo Employee exists.")

    # Self-heal the login account (`users` record) whether it was just
    # created above or already existed, so a stale/incorrect password hash
    # from an earlier run never leaves the demo account unusable.
    print("Verifying password...")
    user = await db.users.find_one({"email": settings.SEED_EMPLOYEE_EMAIL, "role": "EMPLOYEE"})

    if not user:
        print("[seed] WARNING: no Employee login account found for this email — cannot verify password.")
    else:
        updates = {}

        password_ok = verify_password(settings.SEED_EMPLOYEE_PASSWORD, user.get("password_hash", ""))
        if not password_ok:
            print("Password mismatch detected.")
            print("Updating Employee password hash...")
            updates["password_hash"] = hash_password(settings.SEED_EMPLOYEE_PASSWORD)
        else:
            print("Password verified.")

        if user.get("status") != "ACTIVE":
            updates["status"] = "ACTIVE"

        if updates:
            await db.users.update_one({"_id": user["_id"]}, {"$set": updates})
            print("Employee account synchronized successfully.")
        else:
            print("Demo Employee account is already configured correctly.")

        if existing_employee and existing_employee.get("status") != "ACTIVE":
            await db.employees.update_one({"_id": existing_employee["_id"]}, {"$set": {"status": "ACTIVE"}})

    print("[seed] Demo Employee ready.")
    print(f"[seed]   Demo Email:    {settings.SEED_EMPLOYEE_EMAIL}")
    # Never print the password or password hash -- see seed_superadmin.py.
    print("[seed]   Status: ACTIVE")
    print("[seed]   Role:   EMPLOYEE")


async def seed():
    """CLI entrypoint (python seed_demo_employee.py) -- unchanged behavior,
    now just delegates to seed_core() for the actual logic."""
    await connect_to_mongo()
    db = get_db()
    await seed_core(db)
    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(seed())
