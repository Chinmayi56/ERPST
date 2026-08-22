"""
Reproduces the reported bug (demo Employee login fails with "Invalid email
or password" because the demo account was never seeded) against the real,
unmodified employee_auth_service.login_employee, then verifies that
seed_demo_employee.seed_core() -- the same function server.py's startup
lifespan now calls automatically -- fixes it, is idempotent across repeated
startups, and self-heals a corrupted password hash.
"""
import sys, os, asyncio

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
STUBS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stubs")
sys.path.insert(0, STUBS)
sys.path.insert(0, HERE)

os.environ["MONGO_URL"] = "mongodb://localhost:27017"
os.environ["JWT_SECRET"] = "test-secret"

from fakedb import FakeDB
import database.mongodb as mongodb_module
from config import settings
from utils.security import hash_password

fake_db = FakeDB()
mongodb_module.mongodb.db = fake_db

from services import employee_auth_service
from fastapi import HTTPException

results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" -- {detail}" if detail and not cond else ""))

async def main():
    # Reproduce the EXACT reported bug scenario:
    # SuperAdmin already seeded (login works), demo Employee was NEVER seeded.
    await fake_db.users.insert_one({
        "user_id": "USR-SUPERADMIN",
        "email": settings.SEED_SUPERADMIN_EMAIL,
        "role": "SUPERADMIN",
        "status": "ACTIVE",
        "password_hash": hash_password(settings.SEED_SUPERADMIN_PASSWORD),
    })

    pre_fix_error = None
    try:
        await employee_auth_service.login_employee(settings.SEED_EMPLOYEE_EMAIL, settings.SEED_EMPLOYEE_PASSWORD)
    except HTTPException as e:
        pre_fix_error = e
    check("BUG REPRODUCED before fix: demo employee login fails with 'Invalid email or password'",
          pre_fix_error is not None and pre_fix_error.status_code == 401
          and pre_fix_error.detail == "Invalid email or password",
          f"got {pre_fix_error.detail if pre_fix_error else None}")

    # Exactly what server.py's lifespan now runs on every startup.
    from seed_demo_employee import seed_core
    await seed_core(fake_db)

    login_result = await employee_auth_service.login_employee(settings.SEED_EMPLOYEE_EMAIL, settings.SEED_EMPLOYEE_PASSWORD)
    check("FIXED: demo employee logs in successfully after startup seeding",
          "access_token" in login_result)

    user = await fake_db.users.find_one({"email": settings.SEED_EMPLOYEE_EMAIL, "role": "EMPLOYEE"})
    check("Demo employee user record: role EMPLOYEE, status ACTIVE",
          user is not None and user["role"] == "EMPLOYEE" and user["status"] == "ACTIVE")
    employee = await fake_db.employees.find_one({"email": settings.SEED_EMPLOYEE_EMAIL})
    check("Demo employee employee-record status ACTIVE", employee is not None and employee["status"] == "ACTIVE")

    # Idempotency: simulate the server restarting (lifespan runs again).
    await seed_core(fake_db)
    await seed_core(fake_db)
    users_count = await fake_db.users.count_documents({"email": settings.SEED_EMPLOYEE_EMAIL})
    employees_count = await fake_db.employees.count_documents({"email": settings.SEED_EMPLOYEE_EMAIL})
    apps_count = await fake_db.employee_applications.count_documents({"email": settings.SEED_EMPLOYEE_EMAIL})
    check("Repeated startups (idempotent): exactly one user record", users_count == 1, f"got {users_count}")
    check("Repeated startups (idempotent): exactly one employee record", employees_count == 1, f"got {employees_count}")
    check("Repeated startups (idempotent): exactly one application record", apps_count == 1, f"got {apps_count}")

    login_result2 = await employee_auth_service.login_employee(settings.SEED_EMPLOYEE_EMAIL, settings.SEED_EMPLOYEE_PASSWORD)
    check("Login still works after repeated startup seeding", "access_token" in login_result2)

    # Self-healing: a corrupted password hash must be repaired on next startup.
    await fake_db.users.update_one({"email": settings.SEED_EMPLOYEE_EMAIL}, {"$set": {"password_hash": "corrupted"}})
    broken_login = None
    try:
        await employee_auth_service.login_employee(settings.SEED_EMPLOYEE_EMAIL, settings.SEED_EMPLOYEE_PASSWORD)
    except HTTPException as e:
        broken_login = e
    check("Sanity: corrupted hash does break login (test validity check)", broken_login is not None)

    await seed_core(fake_db)
    healed_login = await employee_auth_service.login_employee(settings.SEED_EMPLOYEE_EMAIL, settings.SEED_EMPLOYEE_PASSWORD)
    check("Self-healing: next startup repairs a corrupted password hash", "access_token" in healed_login)

    print()
    total = len(results)
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"=== {passed}/{total} checks passed ===")
    return passed == total

if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
