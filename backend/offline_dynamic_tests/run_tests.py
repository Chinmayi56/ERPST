import sys, os, asyncio, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
STUBS = os.path.join(HERE, "stubs")
BACKEND = os.path.dirname(HERE)  # backend/ (this folder's parent)
sys.path.insert(0, STUBS)   # fastapi/passlib/jose/motor/pymongo stand-ins
sys.path.insert(0, BACKEND)  # the REAL, unmodified project source

os.environ["MONGO_URL"] = "mongodb://localhost:27017"
os.environ["JWT_SECRET"] = "test-secret"

from fakedb import FakeDB
import database.mongodb as mongodb_module

fake_db = FakeDB()
mongodb_module.mongodb.db = fake_db  # inject our fake in place of the real motor db

from services import application_service, employee_auth_service, registration_service
from fastapi import HTTPException

results = []

def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    mark = "PASS" if cond else "FAIL"
    print(f"[{mark}] {name}" + (f" -- {detail}" if detail and not cond else ""))


async def main():
    reviewer = {"user_id": "USR-SUPERADMIN", "role": "SUPERADMIN"}

    # Seed one ACTIVE SuperAdmin user so broadcast_to_role("SUPERADMIN", ...)
    # has somewhere real to deliver notifications, matching production where
    # the SuperAdmin account already exists before any employee registers.
    await fake_db.users.insert_one({
        "user_id": "USR-SUPERADMIN",
        "email": "superadmin@strivenest.com",
        "role": "SUPERADMIN",
        "status": "ACTIVE",
    })

    # ---- TEST 1: registration creates PENDING application ----
    app_payload = {
        "full_name": "Test Employee",
        "email": "newemployee@test.com",
        "password": "Test@12345",
        "mobile": "9876500001",
        "dob": "1998-01-01",
        "gender": "Male",
        "address": "123 Test Street",
        "department": "Engineering",
        "designation": "Software Engineer",
        "qualification": "B.Tech",
        "experience": "2 years",
    }
    created = await application_service.create_application(app_payload)
    check("TEST1 Registration creates application", created["status"] == "PENDING")
    check("TEST1 Password hash never returned to caller", "password_hash" not in created)

    # ---- TEST 2: SuperAdmin sees it in the pending list ----
    pending_list = await application_service.list_applications("PENDING")
    check("TEST2 SuperAdmin sees new PENDING application",
          any(a["email"] == "newemployee@test.com" for a in pending_list))

    # ---- TEST 3: View application, no password/hash leaked ----
    detail = await application_service.get_application(created["application_id"])
    check("TEST3 View application returns details", detail["full_name"] == "Test Employee")
    check("TEST3 View application never exposes password_hash", "password_hash" not in detail)

    # ---- TEST 4: Approve -> Application/User/Employee all synced ----
    approved = await application_service.approve_application(created["application_id"], reviewer)
    check("TEST4 Application becomes APPROVED", approved["status"] == "APPROVED")

    user = await fake_db.users.find_one({"email": "newemployee@test.com", "role": "EMPLOYEE"})
    check("TEST4 User created with status ACTIVE, role EMPLOYEE",
          user is not None and user["status"] == "ACTIVE" and user["role"] == "EMPLOYEE")

    employee = await fake_db.employees.find_one({"email": "newemployee@test.com"})
    check("TEST4 Employee created with status ACTIVE",
          employee is not None and employee["status"] == "ACTIVE")

    check("TEST25 No desync: APPROVED implies User ACTIVE + Employee ACTIVE",
          approved["status"] == "APPROVED" and user["status"] == "ACTIVE" and employee["status"] == "ACTIVE")

    # ---- TEST 5 (idempotency): approving again must not duplicate anything ----
    dup_error = None
    try:
        await application_service.approve_application(created["application_id"], reviewer)
    except HTTPException as e:
        dup_error = e
    check("TEST5 Double-approve is rejected, not silently duplicated",
          dup_error is not None and dup_error.status_code == 409)
    check("TEST5 Double-approve gives friendly message",
          dup_error is not None and "already approved" in dup_error.detail.lower())

    users_count = await fake_db.users.count_documents({"email": "newemployee@test.com"})
    employees_count = await fake_db.employees.count_documents({"email": "newemployee@test.com"})
    check("TEST5 Still exactly one user record after double-approve", users_count == 1, f"got {users_count}")
    check("TEST5 Still exactly one employee record after double-approve", employees_count == 1, f"got {employees_count}")

    # ---- TEST 6: employee login with the SAME credentials from registration ----
    login_result = await employee_auth_service.login_employee("newemployee@test.com", "Test@12345")
    check("TEST6 Login succeeds with registration credentials", "access_token" in login_result)
    check("TEST6 Login issues a JWT-shaped token",
          isinstance(login_result["access_token"], str) and login_result["access_token"].count(".") == 2)

    wrong_pw_error = None
    try:
        await employee_auth_service.login_employee("newemployee@test.com", "WrongPassword1")
    except HTTPException as e:
        wrong_pw_error = e
    check("TEST6b Wrong password rejected", wrong_pw_error is not None and wrong_pw_error.status_code == 401)

    # ---- TEST 7: pending employee cannot log in, gets correct message ----
    pending_payload = dict(app_payload)
    pending_payload["email"] = "pendingemployee@test.com"
    pending_payload["mobile"] = "9876500002"
    pending_app = await application_service.create_application(pending_payload)

    pending_login_error = None
    try:
        await employee_auth_service.login_employee("pendingemployee@test.com", "Test@12345")
    except HTTPException as e:
        pending_login_error = e
    check("TEST7 Pending applicant cannot log in",
          pending_login_error is not None and pending_login_error.status_code == 401)
    check("TEST7 Pending applicant gets a pending-specific message (not generic invalid-credentials)",
          pending_login_error is not None and "pending" in pending_login_error.detail.lower())

    # ---- TEST 8: rejected employee cannot log in, gets correct message ----
    rejected_payload = dict(app_payload)
    rejected_payload["email"] = "rejectedemployee@test.com"
    rejected_payload["mobile"] = "9876500003"
    rejected_app = await application_service.create_application(rejected_payload)
    await application_service.reject_application(rejected_app["application_id"], "Not a fit", reviewer)

    rejected_login_error = None
    try:
        await employee_auth_service.login_employee("rejectedemployee@test.com", "Test@12345")
    except HTTPException as e:
        rejected_login_error = e
    check("TEST8 Rejected applicant cannot log in",
          rejected_login_error is not None and rejected_login_error.status_code == 401)
    check("TEST8 Rejected applicant gets a rejection-specific message",
          rejected_login_error is not None and "rejected" in rejected_login_error.detail.lower())

    # ---- TEST 9/status polling: application-status endpoint logic ----
    status_resp = await application_service.get_application_status_by_email("pendingemployee@test.com")
    check("TEST9 Status polling reports PENDING", status_resp["status"] == "PENDING")

    status_resp2 = await application_service.get_application_status_by_email("newemployee@test.com")
    check("TEST9 Status polling reports APPROVED after approval", status_resp2["status"] == "APPROVED")
    check("TEST9 Approved status message tells applicant they can log in",
          "login" in status_resp2["message"].lower())

    # ---- TEST 9/12/17/18: Registration links (generate/copy-url/disable/expire/used-count) ----
    link = await registration_service.create_registration_link(7, "Batch hiring", reviewer)
    check("TEST9 Registration link URL contains the token once, in full",
          link["url"].startswith("http") and "token=" in link["url"])
    raw_token = link["url"].split("token=")[1]

    links_list = await registration_service.list_registration_links()
    check("TEST9 Listed links never re-expose the raw token/url",
          all("url" not in l for l in links_list))

    # valid token consumption bumps used_count
    await registration_service.validate_and_consume_token(raw_token)
    links_after = await registration_service.list_registration_links()
    used_link = next(l for l in links_after if l["link_id"] == link["link_id"])
    check("TEST12 Used Count increments in the DB on successful use", used_link["used_count"] == 1,
          f"got {used_link['used_count']}")

    # disable then try to use again
    await registration_service.disable_registration_link(link["link_id"], reviewer)
    disabled_error = None
    try:
        await registration_service.validate_and_consume_token(raw_token)
    except HTTPException as e:
        disabled_error = e
    check("TEST10 Disabled link rejects further registration",
          disabled_error is not None and disabled_error.status_code == 400)

    # expired link
    import datetime
    expired_link = await registration_service.create_registration_link(7, "Will expire", reviewer)
    expired_raw = expired_link["url"].split("token=")[1]
    # simulate time passing by rewriting expiry_date directly in the fake db
    doc = await fake_db.registration_links.find_one({"link_id": expired_link["link_id"]})
    await fake_db.registration_links.update_one(
        {"link_id": expired_link["link_id"]},
        {"$set": {"expiry_date": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)}},
    )
    expired_error = None
    try:
        await registration_service.validate_and_consume_token(expired_raw)
    except HTTPException as e:
        expired_error = e
    check("TEST11 Expired link rejects registration",
          expired_error is not None and "expired" in expired_error.detail.lower())

    # ---- registration with a duplicate email is rejected ----
    dup_reg_error = None
    try:
        await application_service.create_application(app_payload)  # same email as TEST1/4
    except HTTPException as e:
        dup_reg_error = e
    check("Duplicate email registration rejected", dup_reg_error is not None and dup_reg_error.status_code == 409)

    # ---- reject idempotency (mirror of the approve idempotency test) ----
    dup_reject_error = None
    try:
        await application_service.reject_application(rejected_app["application_id"], "again", reviewer)
    except HTTPException as e:
        dup_reject_error = e
    check("Double-reject is rejected with a friendly message",
          dup_reject_error is not None and dup_reject_error.status_code == 409
          and "already rejected" in dup_reject_error.detail.lower())

    approve_after_reject_error = None
    try:
        await application_service.approve_application(rejected_app["application_id"], reviewer)
    except HTTPException as e:
        approve_after_reject_error = e
    check("Cannot approve an application that was already rejected",
          approve_after_reject_error is not None and approve_after_reject_error.status_code == 400)

    # ---- TEST 21: dashboard stats reflect real DB state ----
    from services import superadmin_service
    summary = await superadmin_service.get_dashboard_summary()
    check("TEST21 Dashboard total_employees matches DB (1 approved employee)",
          summary["total_employees"] == 1, f"got {summary['total_employees']}")
    check("TEST21 Dashboard pending_applications matches DB (1 pending)",
          summary["pending_applications"] == 1, f"got {summary['pending_applications']}")
    check("TEST21 Dashboard approved_applications matches DB (1 approved)",
          summary["approved_applications"] == 1, f"got {summary['approved_applications']}")
    check("TEST21 Dashboard rejected_applications matches DB (1 rejected)",
          summary["rejected_applications"] == 1, f"got {summary['rejected_applications']}")

    # ---- TEST 23: a notification was delivered to the SuperAdmin for each new application ----
    superadmin_notifs = await fake_db.notifications.count_documents(
        {"recipient_user_id": "USR-SUPERADMIN", "type": "NEW_APPLICATION"}
    )
    check("TEST23 SuperAdmin receives one notification per new application (3 registrations above)",
          superadmin_notifs == 3, f"got {superadmin_notifs}")
    sample_notif = await fake_db.notifications.find_one({"recipient_user_id": "USR-SUPERADMIN"})
    check("TEST23 Notification references the application it's about",
          sample_notif is not None and sample_notif.get("related_application_id") is not None)

    print()
    total = len(results)
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"=== {passed}/{total} checks passed ===")
    return passed == total


if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
