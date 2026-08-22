"""
Tests for: Employee Approval -> Employee Login -> Employee Portal ->
SuperAdmin Sync. Covers the full spec end-to-end flow plus every negative
case called out in the task (wrong password, rejected, pending, inactive,
cross-employee access, SuperAdmin-only API access, unauthenticated access).
"""
import pytest

from tests.conftest import sample_application_payload, DEFAULT_APPLICANT_PASSWORD

pytestmark = pytest.mark.asyncio


async def _approve_new_employee(client, superadmin_headers, **overrides):
    submit = await client.post("/api/employee-applications", json=sample_application_payload(**overrides))
    app_id = submit.json()["application_id"]
    approve = await client.post(f"/api/employee-applications/{app_id}/approve", headers=superadmin_headers)
    assert approve.status_code == 200, approve.text
    return approve.json(), app_id


async def _employee_headers(client, email, password):
    resp = await client.post("/api/auth/employee/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 1. Login gating: pending / rejected / wrong password / inactive
# ---------------------------------------------------------------------------

async def test_pending_employee_login_shows_pending_message(client):
    submit = await client.post("/api/employee-applications", json=sample_application_payload())
    email = submit.json()["email"]

    resp = await client.post("/api/auth/employee/login", json={"email": email, "password": "anything"})
    assert resp.status_code == 401
    assert "pending" in resp.json()["detail"].lower()


async def test_rejected_employee_login_shows_rejected_message(client, superadmin_headers):
    submit = await client.post("/api/employee-applications", json=sample_application_payload())
    app_id = submit.json()["application_id"]
    await client.post(
        f"/api/employee-applications/{app_id}/reject",
        json={"reason": "Not a fit"},
        headers=superadmin_headers,
    )

    resp = await client.post(
        "/api/auth/employee/login", json={"email": submit.json()["email"], "password": "anything"}
    )
    assert resp.status_code == 401
    assert "rejected" in resp.json()["detail"].lower()


async def test_wrong_password_after_approval(client, superadmin_headers):
    creds, _ = await _approve_new_employee(client, superadmin_headers)

    resp = await client.post(
        "/api/auth/employee/login",
        json={"email": creds["employee_login_email"], "password": "totally-wrong"},
    )
    assert resp.status_code == 401
    assert "invalid" in resp.json()["detail"].lower()


async def test_inactive_employee_login_shows_inactive_message(client, superadmin_headers):
    creds, _ = await _approve_new_employee(client, superadmin_headers)

    deactivate = await client.patch(
        f"/api/employees/{creds['employee_id']}/status",
        json={"status": "DISABLED"},
        headers=superadmin_headers,
    )
    assert deactivate.status_code == 200

    resp = await client.post(
        "/api/auth/employee/login",
        json={"email": creds["employee_login_email"], "password": DEFAULT_APPLICANT_PASSWORD},
    )
    assert resp.status_code == 403
    assert "inactive" in resp.json()["detail"].lower()


async def test_unknown_email_login_generic_message(client):
    resp = await client.post(
        "/api/auth/employee/login", json={"email": "nobody@nowhere.com", "password": "x"}
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid email or password"


# ---------------------------------------------------------------------------
# 2. Full end-to-end flow: approve -> login -> dashboard -> profile -> sync
# ---------------------------------------------------------------------------

async def test_full_flow_login_dashboard_profile_and_superadmin_sync(client, superadmin_headers):
    creds, app_id = await _approve_new_employee(client, superadmin_headers)
    headers = await _employee_headers(client, creds["employee_login_email"], DEFAULT_APPLICANT_PASSWORD)

    dash = await client.get("/api/employee/dashboard", headers=headers)
    assert dash.status_code == 200, dash.text
    dash_body = dash.json()
    assert dash_body["employee_id"] == creds["employee_id"]
    assert dash_body["email"] == creds["employee_login_email"]
    assert dash_body["status"] == "ACTIVE"

    profile = await client.get("/api/employee/profile", headers=headers)
    assert profile.status_code == 200, profile.text
    profile_body = profile.json()
    assert profile_body["application_id"] == app_id
    assert profile_body["current_status"] == "ACTIVE"
    assert profile_body["approved_by"]  # resolved to the SuperAdmin's name
    assert profile_body["personal_details"]["email"] == creds["employee_login_email"]

    # SuperAdmin sees the same employee via Employee Management
    listing = await client.get("/api/superadmin/employees", headers=superadmin_headers)
    assert any(e["employee_id"] == creds["employee_id"] for e in listing.json())

    detail = await client.get(f"/api/superadmin/employees/{creds['employee_id']}", headers=superadmin_headers)
    assert detail.status_code == 200
    assert detail.json()["last_login"] is not None  # updated by the login above


async def test_logout_endpoint_works_for_employee(client, superadmin_headers):
    creds, _ = await _approve_new_employee(client, superadmin_headers)
    headers = await _employee_headers(client, creds["employee_login_email"], DEFAULT_APPLICANT_PASSWORD)

    resp = await client.post("/api/auth/logout", headers=headers)
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 3. Notifications
# ---------------------------------------------------------------------------

async def test_employee_sees_approval_notification(client, superadmin_headers):
    creds, _ = await _approve_new_employee(client, superadmin_headers)
    headers = await _employee_headers(client, creds["employee_login_email"], DEFAULT_APPLICANT_PASSWORD)

    resp = await client.get("/api/employee/notifications", headers=headers)
    assert resp.status_code == 200
    types = [n["type"] for n in resp.json()]
    assert "APPLICATION_APPROVED" in types
    assert "APPLICATION_SUBMITTED" in types


async def test_employee_can_mark_notification_read_and_read_all(client, superadmin_headers):
    creds, _ = await _approve_new_employee(client, superadmin_headers)
    headers = await _employee_headers(client, creds["employee_login_email"], DEFAULT_APPLICANT_PASSWORD)

    listing = await client.get("/api/employee/notifications", headers=headers)
    notif_id = listing.json()[0]["notification_id"]

    mark_one = await client.patch(f"/api/employee/notifications/{notif_id}/read", headers=headers)
    assert mark_one.status_code == 200
    assert mark_one.json()["is_read"] is True

    mark_all = await client.patch("/api/employee/notifications/read-all", headers=headers)
    assert mark_all.status_code == 200

    after = await client.get("/api/employee/notifications", headers=headers)
    assert all(n["is_read"] for n in after.json())


async def test_deactivation_notifies_employee(client, superadmin_headers):
    creds, _ = await _approve_new_employee(client, superadmin_headers)
    headers = await _employee_headers(client, creds["employee_login_email"], DEFAULT_APPLICANT_PASSWORD)

    await client.patch(
        f"/api/employees/{creds['employee_id']}/status",
        json={"status": "DISABLED"},
        headers=superadmin_headers,
    )

    # Notification was written even though the employee can no longer log in
    # to fetch it via a fresh token; verify via SuperAdmin-visible employee
    # record instead by re-activating and checking the inbox.
    await client.patch(
        f"/api/employees/{creds['employee_id']}/status",
        json={"status": "ACTIVE"},
        headers=superadmin_headers,
    )
    headers = await _employee_headers(client, creds["employee_login_email"], DEFAULT_APPLICANT_PASSWORD)
    resp = await client.get("/api/employee/notifications", headers=headers)
    types = [n["type"] for n in resp.json()]
    assert "ACCOUNT_DEACTIVATED" in types
    assert "ACCOUNT_ACTIVATED" in types


# ---------------------------------------------------------------------------
# 4. Security boundaries
# ---------------------------------------------------------------------------

async def test_protected_employee_apis_reject_unauthenticated(client):
    for path in ("/api/employee/dashboard", "/api/employee/profile", "/api/employee/notifications"):
        resp = await client.get(path)
        assert resp.status_code == 401, path


async def test_employee_cannot_access_superadmin_apis(client, superadmin_headers):
    creds, _ = await _approve_new_employee(client, superadmin_headers)
    headers = await _employee_headers(client, creds["employee_login_email"], DEFAULT_APPLICANT_PASSWORD)

    resp = await client.get("/api/superadmin/employees", headers=headers)
    assert resp.status_code == 403

    resp2 = await client.get("/api/employee-applications", headers=headers)
    assert resp2.status_code == 403

    resp3 = await client.post(f"/api/employee-applications/does-not-matter/approve", headers=headers)
    assert resp3.status_code == 403


async def test_superadmin_cannot_use_employee_login(client):
    resp = await client.post(
        "/api/auth/employee/login",
        json={"email": "superadmin@strivenest.com", "password": "SuperAdmin@123"},
    )
    assert resp.status_code == 401  # SUPERADMIN role has no EMPLOYEE-role users record


async def test_employee_cannot_see_another_employees_profile_data(client, superadmin_headers):
    creds_a, _ = await _approve_new_employee(client, superadmin_headers)
    creds_b, _ = await _approve_new_employee(
        client, superadmin_headers, email="second.employee@example.com", mobile="9000000001"
    )

    headers_a = await _employee_headers(client, creds_a["employee_login_email"], DEFAULT_APPLICANT_PASSWORD)
    profile_a = await client.get("/api/employee/profile", headers=headers_a)
    assert profile_a.json()["professional_details"]["employee_id"] == creds_a["employee_id"]
    assert profile_a.json()["professional_details"]["employee_id"] != creds_b["employee_id"]


async def test_expired_or_garbage_token_rejected(client):
    resp = await client.get(
        "/api/employee/dashboard", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert resp.status_code == 401


async def test_jwt_contains_employee_id(client, superadmin_headers):
    import jose.jwt as jose_jwt
    from config import settings

    creds, _ = await _approve_new_employee(client, superadmin_headers)
    resp = await client.post(
        "/api/auth/employee/login",
        json={"email": creds["employee_login_email"], "password": DEFAULT_APPLICANT_PASSWORD},
    )
    token = resp.json()["access_token"]
    payload = jose_jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    assert payload["employee_id"] == creds["employee_id"]
    assert payload["role"] == "EMPLOYEE"
    assert "exp" in payload
