"""
Tests for: employee registration -> superadmin notification -> review ->
approve/reject -> employee record.
"""
import pytest

from tests.conftest import sample_application_payload, DEFAULT_APPLICANT_PASSWORD

pytestmark = pytest.mark.asyncio


async def test_registration_creates_pending_application(client):
    resp = await client.post("/api/employee-applications", json=sample_application_payload())
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "PENDING"
    assert body["application_id"].startswith("EMP-")
    assert body["email"] == "rahul.kumar@example.com"


async def test_duplicate_email_rejected(client):
    payload = sample_application_payload()
    resp1 = await client.post("/api/employee-applications", json=payload)
    assert resp1.status_code == 200

    dup = sample_application_payload(mobile="9999999999")  # same email, different mobile
    resp2 = await client.post("/api/employee-applications", json=dup)
    assert resp2.status_code == 409


async def test_duplicate_mobile_rejected(client):
    payload = sample_application_payload()
    resp1 = await client.post("/api/employee-applications", json=payload)
    assert resp1.status_code == 200

    dup = sample_application_payload(email="someoneelse@example.com")  # same mobile
    resp2 = await client.post("/api/employee-applications", json=dup)
    assert resp2.status_code == 409


async def test_invalid_mobile_format_rejected(client):
    bad = sample_application_payload(mobile="12345")
    resp = await client.post("/api/employee-applications", json=bad)
    assert resp.status_code == 422


async def test_mismatched_passwords_rejected(client):
    bad = sample_application_payload(confirm_password="SomethingElse@123")
    resp = await client.post("/api/employee-applications", json=bad)
    assert resp.status_code == 422


async def test_short_password_rejected(client):
    bad = sample_application_payload(password="short1", confirm_password="short1")
    resp = await client.post("/api/employee-applications", json=bad)
    assert resp.status_code == 422


async def test_submission_notifies_superadmin(client, superadmin_headers, superadmin_user):
    await client.post("/api/employee-applications", json=sample_application_payload())

    resp = await client.get("/api/superadmin/notifications", headers=superadmin_headers)
    assert resp.status_code == 200
    notifications = resp.json()
    assert any(n["type"] == "NEW_APPLICATION" and not n["is_read"] for n in notifications)


async def test_non_superadmin_cannot_list_applications(client):
    resp = await client.get("/api/employee-applications")
    assert resp.status_code == 401


async def test_superadmin_can_view_applications(client, superadmin_headers):
    await client.post("/api/employee-applications", json=sample_application_payload())
    resp = await client.get("/api/employee-applications", headers=superadmin_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_non_superadmin_cannot_approve(client):
    submit = await client.post("/api/employee-applications", json=sample_application_payload())
    app_id = submit.json()["application_id"]

    resp = await client.post(f"/api/employee-applications/{app_id}/approve")
    assert resp.status_code == 401


async def test_superadmin_can_approve_and_creates_exactly_one_employee(client, superadmin_headers, db):
    submit = await client.post("/api/employee-applications", json=sample_application_payload())
    app_id = submit.json()["application_id"]

    resp = await client.post(f"/api/employee-applications/{app_id}/approve", headers=superadmin_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "APPROVED"
    assert body["employee_id"].startswith("EMP")
    assert "password_hash" not in body  # never exposed via the API

    employees = await db.employees.find({"source_application_id": app_id}).to_list(length=10)
    assert len(employees) == 1
    assert employees[0]["status"] == "ACTIVE"

    users = await db.users.find({"email": "rahul.kumar@example.com", "role": "EMPLOYEE"}).to_list(length=10)
    assert len(users) == 1


async def test_approval_cannot_create_duplicates(client, superadmin_headers):
    submit = await client.post("/api/employee-applications", json=sample_application_payload())
    app_id = submit.json()["application_id"]

    resp1 = await client.post(f"/api/employee-applications/{app_id}/approve", headers=superadmin_headers)
    assert resp1.status_code == 200

    resp2 = await client.post(f"/api/employee-applications/{app_id}/approve", headers=superadmin_headers)
    assert resp2.status_code == 400  # no longer PENDING


async def test_approved_employee_appears_in_employee_management(client, superadmin_headers):
    submit = await client.post("/api/employee-applications", json=sample_application_payload())
    app_id = submit.json()["application_id"]
    await client.post(f"/api/employee-applications/{app_id}/approve", headers=superadmin_headers)

    resp = await client.get("/api/superadmin/employees", headers=superadmin_headers)
    assert resp.status_code == 200
    employees = resp.json()
    assert any(e["source_application_id"] == app_id for e in employees)


async def test_superadmin_can_reject_with_reason(client, superadmin_headers):
    submit = await client.post("/api/employee-applications", json=sample_application_payload())
    app_id = submit.json()["application_id"]

    resp = await client.post(
        f"/api/employee-applications/{app_id}/reject",
        json={"reason": "Insufficient experience for this role"},
        headers=superadmin_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "REJECTED"
    assert body["rejection_reason"] == "Insufficient experience for this role"


async def test_reject_without_reason_fails_validation(client, superadmin_headers):
    submit = await client.post("/api/employee-applications", json=sample_application_payload())
    app_id = submit.json()["application_id"]

    resp = await client.post(
        f"/api/employee-applications/{app_id}/reject", json={"reason": ""}, headers=superadmin_headers
    )
    assert resp.status_code == 422


async def test_rejected_application_creates_no_employee(client, superadmin_headers, db):
    submit = await client.post("/api/employee-applications", json=sample_application_payload())
    app_id = submit.json()["application_id"]
    await client.post(
        f"/api/employee-applications/{app_id}/reject",
        json={"reason": "Not a fit right now"},
        headers=superadmin_headers,
    )

    employees = await db.employees.find({"source_application_id": app_id}).to_list(length=10)
    assert len(employees) == 0

    # Original application remains stored, not deleted.
    detail = await client.get(f"/api/employee-applications/{app_id}", headers=superadmin_headers)
    assert detail.status_code == 200
    assert detail.json()["status"] == "REJECTED"


async def test_employee_cannot_login_before_approval(client, db):
    submit = await client.post("/api/employee-applications", json=sample_application_payload())
    email = submit.json()["email"]

    resp = await client.post(
        "/api/auth/employee/login", json={"email": email, "password": "anything"}
    )
    assert resp.status_code == 401


async def test_employee_can_login_after_approval_with_registered_password(client, superadmin_headers):
    submit = await client.post("/api/employee-applications", json=sample_application_payload())
    app_id = submit.json()["application_id"]

    approve = await client.post(f"/api/employee-applications/{app_id}/approve", headers=superadmin_headers)
    creds = approve.json()

    resp = await client.post(
        "/api/auth/employee/login",
        json={"email": creds["employee_login_email"], "password": DEFAULT_APPLICANT_PASSWORD},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["user"]["role"] == "EMPLOYEE"


async def test_disabling_employee_blocks_login(client, superadmin_headers):
    submit = await client.post("/api/employee-applications", json=sample_application_payload())
    app_id = submit.json()["application_id"]
    approve = await client.post(f"/api/employee-applications/{app_id}/approve", headers=superadmin_headers)
    creds = approve.json()

    resp = await client.patch(
        f"/api/employees/{creds['employee_id']}/status",
        json={"status": "DISABLED"},
        headers=superadmin_headers,
    )
    assert resp.status_code == 200

    login = await client.post(
        "/api/auth/employee/login",
        json={"email": creds["employee_login_email"], "password": DEFAULT_APPLICANT_PASSWORD},
    )
    assert login.status_code == 403
