"""
Development-only diagnostic: connects to the SAME MongoDB database the
running FastAPI app uses (via database/mongodb.py) and reports the actual
state of the two demo accounts -- SuperAdmin and Employee -- straight from
MongoDB. Run this any time the demo credentials on the login pages stop
working, to see exactly which link in the chain is broken instead of
guessing.

Never prints password hashes, JWT secrets, or MongoDB credentials -- only
PASS/FAIL verification results and non-sensitive account metadata.

Usage:
    python verify_demo_accounts.py
"""
import asyncio

from config import settings
from database.mongodb import connect_to_mongo, close_mongo_connection, get_db
from utils.security import verify_password


def _yn(value: bool) -> str:
    return "YES" if value else "NO"


async def main():
    print("Connecting to MongoDB...")
    try:
        await connect_to_mongo()
    except Exception as exc:  # pragma: no cover - diagnostic path only
        print(f"MongoDB connection: FAIL ({exc.__class__.__name__})")
        return
    print(f"MongoDB connection: OK  (db={settings.DB_NAME})")

    db = get_db()

    # ---------------------------------------------------------------- #
    # SuperAdmin
    # ---------------------------------------------------------------- #
    print("\nSuperAdmin:")
    sa_email = settings.SEED_SUPERADMIN_EMAIL.strip().lower()
    sa_user = await db.users.find_one({"email": sa_email})

    if not sa_user:
        print("  Found: NO")
        print(f"  (No user document for {sa_email} -- run: python seed_superadmin.py)")
    else:
        print("  Found: YES")
        print(f"  Email: {sa_user.get('email')}")
        print(f"  Role: {sa_user.get('role')}")
        print(f"  Status: {sa_user.get('status')}")
        sa_pw_ok = verify_password(settings.SEED_SUPERADMIN_PASSWORD, sa_user.get("password_hash", ""))
        print(f"  Password verification: {'PASS' if sa_pw_ok else 'FAIL'}")
        if sa_user.get("role") != "SUPERADMIN":
            print("  WARNING: role is not SUPERADMIN")
        if sa_user.get("status") != "ACTIVE":
            print("  WARNING: status is not ACTIVE")
        if not sa_pw_ok:
            print("  WARNING: stored password hash does not match the demo password.")
            print("           Run: python seed_superadmin.py to self-heal it.")

    sa_dupe_count = await db.users.count_documents({"email": sa_email})
    if sa_dupe_count > 1:
        print(f"  WARNING: {sa_dupe_count} user documents share this email (expected 1).")

    # ---------------------------------------------------------------- #
    # Employee
    # ---------------------------------------------------------------- #
    print("\nEmployee:")
    emp_email = settings.SEED_EMPLOYEE_EMAIL.strip().lower()
    emp_user = await db.users.find_one({"email": emp_email, "role": "EMPLOYEE"})

    if not emp_user:
        print("  User found: NO")
        print(f"  (No EMPLOYEE user document for {emp_email} -- run: python seed_demo_employee.py)")
    else:
        print("  User found: YES")
        print(f"  Email: {emp_user.get('email')}")
        print(f"  Role: {emp_user.get('role')}")
        print(f"  User status: {emp_user.get('status')}")
        emp_pw_ok = verify_password(settings.SEED_EMPLOYEE_PASSWORD, emp_user.get("password_hash", ""))
        print(f"  Password verification: {'PASS' if emp_pw_ok else 'FAIL'}")
        if emp_user.get("status") != "ACTIVE":
            print("  WARNING: user status is not ACTIVE")
        if not emp_pw_ok:
            print("  WARNING: stored password hash does not match the demo password.")
            print("           Run: python seed_demo_employee.py to self-heal it.")

    print("\nEmployee record:")
    employee = await db.employees.find_one({"email": emp_email})
    if not employee:
        print("  Found: NO")
    else:
        print("  Found: YES")
        print(f"  Employee status: {employee.get('status')}")
        user_id_match = bool(emp_user) and employee.get("user_id") == emp_user.get("user_id")
        print(f"  user_id match: {_yn(user_id_match)}")
        if employee.get("status") != "ACTIVE":
            print("  WARNING: employee status is not ACTIVE")
        if emp_user and not user_id_match:
            print("  WARNING: employees.user_id does not match users.user_id -- relationship broken.")

    print("\nEmployee application:")
    application = await db.employee_applications.find_one({"email": emp_email})
    if not application:
        print("  Found: NO")
    else:
        print("  Found: YES")
        print(f"  Application status: {application.get('status')}")
        if application.get("status") != "APPROVED":
            print("  WARNING: application is not APPROVED -- employee login will be blocked.")
        if employee and employee.get("source_application_id") != application.get("application_id"):
            print("  WARNING: employees.source_application_id does not match this application -- relationship broken.")

    emp_dupe_count = await db.employee_applications.count_documents({"email": emp_email})
    if emp_dupe_count > 1:
        print(f"  WARNING: {emp_dupe_count} applications share this email (expected 1).")

    print()
    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
