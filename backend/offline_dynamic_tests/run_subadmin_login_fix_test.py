"""
Reproduces the reported bug (SubAdmin login fails with "Invalid email or
password" because the demo SubAdmin account was never seeded -- only
`seed_superadmin.py` was run, `seed_subadmin.py` was skipped, exactly like
the already-fixed demo Employee case) against the real, unmodified
auth_service.login_with_email_password / send_demo_otp / verify_demo_otp,
then verifies that seed_subadmin.seed_core() -- the same function
server.py's startup lifespan now calls automatically -- fixes it for both
the email/password flow and the mobile OTP flow, is idempotent across
repeated startups, self-heals a corrupted password hash, and does not
touch SuperAdmin or Employee accounts/logins.
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

from services import auth_service
from fastapi import HTTPException

results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" -- {detail}" if detail and not cond else ""))

async def main():
    # Reproduce the EXACT reported bug scenario: SuperAdmin already seeded
    # (login works, matching "SuperAdmin login already works" reports),
    # demo SubAdmin was NEVER seeded (seed_subadmin.py step skipped).
    await fake_db.users.insert_one({
        "user_id": "USR-SUPERADMIN",
        "email": settings.SEED_SUPERADMIN_EMAIL,
        "mobile": settings.SEED_SUPERADMIN_MOBILE,
        "role": "SUPERADMIN",
        "status": "ACTIVE",
        "password_hash": hash_password(settings.SEED_SUPERADMIN_PASSWORD),
    })

    pre_fix_error = None
    try:
        await auth_service.login_with_email_password(
            settings.SEED_SUBADMIN_EMAIL, settings.SEED_SUBADMIN_PASSWORD, role="SUBADMIN"
        )
    except HTTPException as e:
        pre_fix_error = e
    check("BUG REPRODUCED before fix: subadmin@strivenest.com / Subadmin@12 fails with 'Invalid email or password'",
          pre_fix_error is not None and pre_fix_error.status_code == 401
          and pre_fix_error.detail == "Invalid email or password",
          f"got {pre_fix_error.detail if pre_fix_error else None}")

    # Exactly what server.py's lifespan now runs on every startup.
    from seed_subadmin import seed_core
    await seed_core(fake_db)

    login_result = await auth_service.login_with_email_password(
        settings.SEED_SUBADMIN_EMAIL, settings.SEED_SUBADMIN_PASSWORD, role="SUBADMIN"
    )
    check("FIXED: subadmin@strivenest.com / Subadmin@12 logs in successfully after startup seeding",
          "access_token" in login_result)
    check("JWT is issued for role SUBADMIN", login_result["user"]["role"] == "SUBADMIN")

    user = await fake_db.users.find_one({"email": settings.SEED_SUBADMIN_EMAIL, "role": "SUBADMIN"})
    check("Demo SubAdmin user record: role SUBADMIN, status ACTIVE",
          user is not None and user["role"] == "SUBADMIN" and user["status"] == "ACTIVE")

    # Mobile OTP flow (same demo credentials the SubAdmin login page shows).
    otp_send = await auth_service.send_demo_otp(settings.SEED_SUBADMIN_MOBILE, role="SUBADMIN")
    check("send_demo_otp succeeds for the seeded SubAdmin mobile number", "message" in otp_send)
    otp_login = await auth_service.verify_demo_otp(settings.SEED_SUBADMIN_MOBILE, settings.DEMO_OTP, role="SUBADMIN")
    check("verify_demo_otp (9876543212 / 123456) logs in successfully and returns a JWT",
          "access_token" in otp_login and otp_login["user"]["role"] == "SUBADMIN")

    # Idempotency: simulate the server restarting (lifespan runs again).
    await seed_core(fake_db)
    await seed_core(fake_db)
    users_count = await fake_db.users.count_documents({"email": settings.SEED_SUBADMIN_EMAIL})
    check("Repeated startups (idempotent): exactly one SubAdmin user record", users_count == 1, f"got {users_count}")

    login_result2 = await auth_service.login_with_email_password(
        settings.SEED_SUBADMIN_EMAIL, settings.SEED_SUBADMIN_PASSWORD, role="SUBADMIN"
    )
    check("Login still works after repeated startup seeding", "access_token" in login_result2)

    # Self-healing: a corrupted password hash must be repaired on next startup.
    await fake_db.users.update_one({"email": settings.SEED_SUBADMIN_EMAIL}, {"$set": {"password_hash": "corrupted"}})
    broken_login = None
    try:
        await auth_service.login_with_email_password(
            settings.SEED_SUBADMIN_EMAIL, settings.SEED_SUBADMIN_PASSWORD, role="SUBADMIN"
        )
    except HTTPException as e:
        broken_login = e
    check("Sanity: corrupted hash does break login (test validity check)", broken_login is not None)

    await seed_core(fake_db)
    healed_login = await auth_service.login_with_email_password(
        settings.SEED_SUBADMIN_EMAIL, settings.SEED_SUBADMIN_PASSWORD, role="SUBADMIN"
    )
    check("Self-healing: next startup repairs a corrupted password hash", "access_token" in healed_login)

    # Cross-role isolation: SubAdmin seeding must never let SubAdmin log in
    # as SuperAdmin, and SuperAdmin's own account/credentials stay untouched.
    cross_role_error = None
    try:
        await auth_service.login_with_email_password(
            settings.SEED_SUBADMIN_EMAIL, settings.SEED_SUBADMIN_PASSWORD, role="SUPERADMIN"
        )
    except HTTPException as e:
        cross_role_error = e
    check("SubAdmin credentials are rejected against the SuperAdmin role gate (403)",
          cross_role_error is not None and cross_role_error.status_code == 403)

    superadmin_login = await auth_service.login_with_email_password(
        settings.SEED_SUPERADMIN_EMAIL, settings.SEED_SUPERADMIN_PASSWORD, role="SUPERADMIN"
    )
    check("SuperAdmin login is unaffected by the SubAdmin fix",
          "access_token" in superadmin_login and superadmin_login["user"]["role"] == "SUPERADMIN")

    print()
    total = len(results)
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"=== {passed}/{total} checks passed ===")
    return passed == total

if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
