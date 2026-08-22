"""
Tests for the SubAdmin role: authentication, server-enforced role
separation, and shared ERP/MongoDB data with SuperAdmin.
"""
import pytest

from config import settings

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# 1. SubAdmin authentication
# ---------------------------------------------------------------------------

async def test_subadmin_login_success(client, subadmin_user):
    resp = await client.post(
        "/api/auth/subadmin/login",
        json={"email": settings.SEED_SUBADMIN_EMAIL, "password": settings.SEED_SUBADMIN_PASSWORD},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["user"]["role"] == "SUBADMIN"
    assert "access_token" in body


async def test_subadmin_login_wrong_password(client, subadmin_user):
    resp = await client.post(
        "/api/auth/subadmin/login",
        json={"email": settings.SEED_SUBADMIN_EMAIL, "password": "wrong"},
    )
    assert resp.status_code == 401


async def test_superadmin_cannot_login_via_subadmin_endpoint(client, superadmin_user):
    resp = await client.post(
        "/api/auth/subadmin/login",
        json={"email": "superadmin@strivenest.com", "password": "SuperAdmin@123"},
    )
    assert resp.status_code == 403


async def test_subadmin_cannot_login_via_superadmin_endpoint(client, subadmin_user):
    resp = await client.post(
        "/api/auth/superadmin/login",
        json={"email": settings.SEED_SUBADMIN_EMAIL, "password": settings.SEED_SUBADMIN_PASSWORD},
    )
    assert resp.status_code == 403


async def test_subadmin_otp_login(client, subadmin_user):
    send = await client.post("/api/auth/subadmin/send-otp", json={"mobile": "9876543212"})
    assert send.status_code == 200, send.text

    verify = await client.post(
        "/api/auth/subadmin/verify-otp", json={"mobile": "9876543212", "otp": "123456"}
    )
    assert verify.status_code == 200, verify.text
    assert verify.json()["user"]["role"] == "SUBADMIN"


async def test_subadmin_me_returns_real_authenticated_user(client, subadmin_headers):
    resp = await client.get("/api/auth/me", headers=subadmin_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["role"] == "SUBADMIN"
    assert body["email"] == settings.SEED_SUBADMIN_EMAIL
    assert body["name"] != "Super Admin"


# ---------------------------------------------------------------------------
# 2. Server-enforced role separation
# ---------------------------------------------------------------------------

async def test_subadmin_token_rejected_on_superadmin_erp(client, subadmin_headers):
    resp = await client.get("/api/superadmin/erp/clients", headers=subadmin_headers)
    assert resp.status_code == 403


async def test_superadmin_token_rejected_on_subadmin_erp(client, superadmin_headers):
    resp = await client.get("/api/subadmin/erp/clients", headers=superadmin_headers)
    assert resp.status_code == 403


async def test_subadmin_token_rejected_on_superadmin_dashboard(client, subadmin_headers):
    resp = await client.get("/api/superadmin/dashboard", headers=subadmin_headers)
    assert resp.status_code == 403


async def test_employee_token_rejected_on_subadmin_api(client, superadmin_headers):
    # Approve a fresh application to get a real EMPLOYEE token.
    from tests.conftest import sample_application_payload, DEFAULT_APPLICANT_PASSWORD

    submit = await client.post(
        "/api/employee-applications", json=sample_application_payload(email="subtest.employee@example.com", mobile="9812399999")
    )
    app_id = submit.json()["application_id"]
    approve = await client.post(f"/api/employee-applications/{app_id}/approve", headers=superadmin_headers)
    assert approve.status_code == 200, approve.text
    email = approve.json()["employee_login_email"]

    login = await client.post(
        "/api/auth/employee/login", json={"email": email, "password": DEFAULT_APPLICANT_PASSWORD}
    )
    assert login.status_code == 200, login.text
    employee_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = await client.get("/api/subadmin/erp/clients", headers=employee_headers)
    assert resp.status_code == 403


async def test_no_token_rejected(client):
    resp = await client.get("/api/subadmin/erp/clients")
    assert resp.status_code == 401


async def test_invalid_token_rejected(client):
    resp = await client.get(
        "/api/subadmin/erp/clients", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert resp.status_code == 401


async def test_subadmin_token_allowed_on_subadmin_erp(client, subadmin_headers):
    resp = await client.get("/api/subadmin/erp/clients", headers=subadmin_headers)
    assert resp.status_code == 200


async def test_superadmin_token_allowed_on_superadmin_erp(client, superadmin_headers):
    resp = await client.get("/api/superadmin/erp/clients", headers=superadmin_headers)
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 3. Shared ERP data: SubAdmin and SuperAdmin see the same MongoDB records
# ---------------------------------------------------------------------------

async def test_client_created_by_subadmin_visible_to_superadmin(client, subadmin_headers, superadmin_headers):
    create = await client.post(
        "/api/subadmin/erp/clients",
        json={"data": {"name": "Acme Corp", "email": "acme@example.com"}},
        headers=subadmin_headers,
    )
    assert create.status_code == 200, create.text
    client_id = create.json()["client_id"]

    listing = await client.get("/api/superadmin/erp/clients", headers=superadmin_headers)
    assert listing.status_code == 200
    ids = [item["client_id"] for item in listing.json()["items"]]
    assert client_id in ids


async def test_project_created_by_superadmin_visible_to_subadmin(client, subadmin_headers, superadmin_headers):
    create = await client.post(
        "/api/superadmin/erp/projects",
        json={"data": {"name": "Website Revamp"}},
        headers=superadmin_headers,
    )
    assert create.status_code == 200, create.text
    project_id = create.json()["project_id"]

    listing = await client.get("/api/subadmin/erp/projects", headers=subadmin_headers)
    assert listing.status_code == 200
    ids = [item["project_id"] for item in listing.json()["items"]]
    assert project_id in ids


async def test_subadmin_erp_no_duplicate_collections(db, client, subadmin_headers):
    """SubAdmin ERP writes must land in the same `clients` collection --
    never a separate `subadmin_clients` collection."""
    create = await client.post(
        "/api/subadmin/erp/clients",
        json={"data": {"name": "No Duplicate Collections Inc"}},
        headers=subadmin_headers,
    )
    assert create.status_code == 200, create.text
    client_id = create.json()["client_id"]

    found = await db.clients.find_one({"client_id": client_id})
    assert found is not None

    collection_names = await db.list_collection_names()
    assert "subadmin_clients" not in collection_names


# ---------------------------------------------------------------------------
# 4. Audit logging correctness
# ---------------------------------------------------------------------------

async def test_subadmin_action_logged_with_subadmin_role(db, client, subadmin_headers):
    create = await client.post(
        "/api/subadmin/erp/services",
        json={"data": {"name": "Consulting"}},
        headers=subadmin_headers,
    )
    assert create.status_code == 200, create.text
    service_id = create.json()["service_id"]

    entry = await db.audit_logs.find_one({"target_id": service_id, "action": "CREATE_SERVICES"})
    assert entry is not None
    assert entry["role"] == "SUBADMIN"


# ---------------------------------------------------------------------------
# 5. SubAdmin dashboard and notifications
# ---------------------------------------------------------------------------

async def test_subadmin_dashboard_returns_real_counts(client, subadmin_headers):
    await client.post(
        "/api/subadmin/erp/clients",
        json={"data": {"name": "Dashboard Test Client"}},
        headers=subadmin_headers,
    )
    resp = await client.get("/api/subadmin/dashboard", headers=subadmin_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["clients_total"] >= 1


async def test_subadmin_notifications_endpoint_works(client, subadmin_headers):
    resp = await client.get("/api/subadmin/notifications", headers=subadmin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_new_application_notifies_both_superadmin_and_subadmin(
    client, superadmin_user, subadmin_user, db
):
    from tests.conftest import sample_application_payload

    submit = await client.post(
        "/api/employee-applications",
        json=sample_application_payload(email="notify.test@example.com", mobile="9812388888"),
    )
    assert submit.status_code == 200, submit.text

    superadmin_notifs = await db.notifications.count_documents(
        {"recipient_user_id": superadmin_user["user_id"], "type": "NEW_APPLICATION"}
    )
    subadmin_notifs = await db.notifications.count_documents(
        {"recipient_user_id": subadmin_user["user_id"], "type": "NEW_APPLICATION"}
    )
    assert superadmin_notifs == 1
    assert subadmin_notifs == 1


# ---------------------------------------------------------------------------
# 6. SubAdmin cannot self-elevate to SuperAdmin
# ---------------------------------------------------------------------------

async def test_no_role_mutation_endpoint_exists_for_subadmin(client, subadmin_headers):
    # There is no endpoint anywhere in this backend that lets a caller change
    # a user's role -- /api/subadmin/users is read-only. Confirm it is, and
    # confirm no such write path exists under /api/subadmin.
    resp = await client.get("/api/subadmin/users", headers=subadmin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

    # No PATCH/PUT/POST role-mutating route exists; hitting one should 404/405.
    resp2 = await client.patch(
        "/api/subadmin/users/does-not-matter", json={"role": "SUPERADMIN"}, headers=subadmin_headers
    )
    assert resp2.status_code in (404, 405)


# ---------------------------------------------------------------------------
# 3. Public demo-config endpoint (used by login pages to display the demo OTP)
# ---------------------------------------------------------------------------

async def test_demo_config_exposes_no_credentials(client):
    resp = await client.get("/api/auth/demo-config")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["demo_mode"] is True
    assert body["demo_otp"] == "123456"
    assert body["demo_subadmin_mobile"] == "9876543212"
    assert set(body.keys()) == {
        "demo_mode",
        "demo_otp",
        "demo_superadmin_mobile",
        "demo_subadmin_mobile",
    }
