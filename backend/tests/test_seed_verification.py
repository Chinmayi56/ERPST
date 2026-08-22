"""
Verifies that the seed scripts (seed_superadmin.py, seed_demo_employee.py)
leave both demo accounts authenticating successfully through the REAL login
services -- never a faked or bypassed check -- and that re-running them is
idempotent and self-healing against a stale/incorrect password hash.

This exercises the actual MongoDB record (via the same `db` double the rest
of the suite uses) and the actual service-layer login functions, exactly as
described in the fix request.
"""
from datetime import datetime, timezone

import seed_superadmin
import seed_demo_employee
from config import settings
from services import auth_service, employee_auth_service
from utils.security import hash_password, verify_password


async def _noop():
    return None


def _patch_seed_connections(monkeypatch):
    """
    The `db` fixture (conftest.py) already wires an in-memory Mongo double
    into database.mongodb. The seed scripts normally open their own
    connection via connect_to_mongo(); for tests that call into them
    directly we point that at a no-op so they operate on the SAME in-memory
    database as the rest of the test, instead of a real MongoDB.
    """
    monkeypatch.setattr(seed_superadmin, "connect_to_mongo", _noop)
    monkeypatch.setattr(seed_superadmin, "close_mongo_connection", _noop)
    monkeypatch.setattr(seed_demo_employee, "connect_to_mongo", _noop)
    monkeypatch.setattr(seed_demo_employee, "close_mongo_connection", _noop)


async def test_seed_superadmin_creates_working_account(db, monkeypatch):
    _patch_seed_connections(monkeypatch)

    await seed_superadmin.seed()

    user = await db.users.find_one({"email": settings.SEED_SUPERADMIN_EMAIL})
    assert user is not None
    assert user["role"] == "SUPERADMIN"
    assert user["status"] == "ACTIVE"
    assert verify_password(settings.SEED_SUPERADMIN_PASSWORD, user["password_hash"]) is True

    # Real API login flow, not a shortcut.
    result = await auth_service.login_with_email_password(
        settings.SEED_SUPERADMIN_EMAIL, settings.SEED_SUPERADMIN_PASSWORD
    )
    assert result["access_token"]
    assert result["user"]["role"] == "SUPERADMIN"


async def test_seed_superadmin_is_idempotent(db, monkeypatch):
    _patch_seed_connections(monkeypatch)

    await seed_superadmin.seed()
    await seed_superadmin.seed()

    count = await db.users.count_documents({"email": settings.SEED_SUPERADMIN_EMAIL})
    assert count == 1


async def test_seed_superadmin_self_heals_wrong_password_hash(db, monkeypatch):
    _patch_seed_connections(monkeypatch)

    # Simulate a stale account seeded with a different password (or a
    # hand-edited hash) -- exactly the bug that caused "Invalid email or
    # password" for the documented demo credentials.
    fixed_user_id = "USR-FIXEDSA01"
    await db.users.insert_one({
        "user_id": fixed_user_id,
        "name": settings.SEED_SUPERADMIN_NAME,
        "email": settings.SEED_SUPERADMIN_EMAIL,
        "mobile": settings.SEED_SUPERADMIN_MOBILE,
        "password_hash": hash_password("SomeOldWrongPassword!1"),
        "role": "SUPERADMIN",
        "status": "ACTIVE",
        "created_date": datetime.now(timezone.utc),
    })

    await seed_superadmin.seed()

    user = await db.users.find_one({"email": settings.SEED_SUPERADMIN_EMAIL})
    assert verify_password(settings.SEED_SUPERADMIN_PASSWORD, user["password_hash"]) is True
    # Existing account synchronized in place, not replaced.
    assert user["user_id"] == fixed_user_id
    count = await db.users.count_documents({"email": settings.SEED_SUPERADMIN_EMAIL})
    assert count == 1

    # Real login now succeeds through the normal flow.
    result = await auth_service.login_with_email_password(
        settings.SEED_SUPERADMIN_EMAIL, settings.SEED_SUPERADMIN_PASSWORD
    )
    assert result["access_token"]


async def test_seed_superadmin_login_via_real_api(db, client, monkeypatch):
    _patch_seed_connections(monkeypatch)
    await seed_superadmin.seed()

    resp = await client.post(
        "/api/auth/superadmin/login",
        json={"email": settings.SEED_SUPERADMIN_EMAIL, "password": settings.SEED_SUPERADMIN_PASSWORD},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["role"] == "SUPERADMIN"


async def test_seed_demo_employee_creates_working_account(db, monkeypatch):
    _patch_seed_connections(monkeypatch)

    await seed_superadmin.seed()
    await seed_demo_employee.seed()

    user = await db.users.find_one({"email": settings.SEED_EMPLOYEE_EMAIL, "role": "EMPLOYEE"})
    assert user is not None
    assert user["status"] == "ACTIVE"
    assert verify_password(settings.SEED_EMPLOYEE_PASSWORD, user["password_hash"]) is True

    employee = await db.employees.find_one({"email": settings.SEED_EMPLOYEE_EMAIL})
    assert employee is not None
    assert employee["status"] == "ACTIVE"

    result = await employee_auth_service.login_employee(
        settings.SEED_EMPLOYEE_EMAIL, settings.SEED_EMPLOYEE_PASSWORD
    )
    assert result["access_token"]
    assert result["user"]["role"] == "EMPLOYEE"


async def test_seed_demo_employee_is_idempotent(db, monkeypatch):
    _patch_seed_connections(monkeypatch)

    await seed_superadmin.seed()
    await seed_demo_employee.seed()
    await seed_demo_employee.seed()

    count = await db.employees.count_documents({"email": settings.SEED_EMPLOYEE_EMAIL})
    assert count == 1
    user_count = await db.users.count_documents({"email": settings.SEED_EMPLOYEE_EMAIL})
    assert user_count == 1


async def test_seed_demo_employee_self_heals_wrong_password_hash(db, monkeypatch):
    _patch_seed_connections(monkeypatch)

    await seed_superadmin.seed()
    await seed_demo_employee.seed()

    # Corrupt the employee's password hash to simulate drift from an earlier run.
    await db.users.update_one(
        {"email": settings.SEED_EMPLOYEE_EMAIL, "role": "EMPLOYEE"},
        {"$set": {"password_hash": hash_password("SomeOldWrongPassword!1")}},
    )

    await seed_demo_employee.seed()

    user = await db.users.find_one({"email": settings.SEED_EMPLOYEE_EMAIL, "role": "EMPLOYEE"})
    assert verify_password(settings.SEED_EMPLOYEE_PASSWORD, user["password_hash"]) is True

    result = await employee_auth_service.login_employee(
        settings.SEED_EMPLOYEE_EMAIL, settings.SEED_EMPLOYEE_PASSWORD
    )
    assert result["access_token"]


async def test_seed_demo_employee_login_via_real_api(db, client, monkeypatch):
    _patch_seed_connections(monkeypatch)
    await seed_superadmin.seed()
    await seed_demo_employee.seed()

    resp = await client.post(
        "/api/auth/employee/login",
        json={"email": settings.SEED_EMPLOYEE_EMAIL, "password": settings.SEED_EMPLOYEE_PASSWORD},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["access_token"]
    assert body["user"]["role"] == "EMPLOYEE"


async def test_demo_employee_cannot_use_superadmin_login(db, client, monkeypatch):
    """An EMPLOYEE-role account must be rejected by the SuperAdmin login
    endpoint even with the correct password -- role check must not be
    bypassable by hitting the wrong endpoint."""
    _patch_seed_connections(monkeypatch)
    await seed_superadmin.seed()
    await seed_demo_employee.seed()

    resp = await client.post(
        "/api/auth/superadmin/login",
        json={"email": settings.SEED_EMPLOYEE_EMAIL, "password": settings.SEED_EMPLOYEE_PASSWORD},
    )
    assert resp.status_code == 403, resp.text


async def test_demo_superadmin_login_wrong_password_rejected(db, client, monkeypatch):
    _patch_seed_connections(monkeypatch)
    await seed_superadmin.seed()

    resp = await client.post(
        "/api/auth/superadmin/login",
        json={"email": settings.SEED_SUPERADMIN_EMAIL, "password": "WrongPassword!1"},
    )
    assert resp.status_code == 401, resp.text


async def test_demo_superadmin_login_disabled_account_rejected(db, client, monkeypatch):
    _patch_seed_connections(monkeypatch)
    await seed_superadmin.seed()

    await db.users.update_one(
        {"email": settings.SEED_SUPERADMIN_EMAIL},
        {"$set": {"status": "DISABLED"}},
    )

    resp = await client.post(
        "/api/auth/superadmin/login",
        json={"email": settings.SEED_SUPERADMIN_EMAIL, "password": settings.SEED_SUPERADMIN_PASSWORD},
    )
    assert resp.status_code == 403, resp.text


async def test_demo_superadmin_login_email_case_and_whitespace_insensitive(db, client, monkeypatch):
    """Real-world browser autofill / manual typing can add surrounding
    whitespace or different casing -- login must still succeed."""
    _patch_seed_connections(monkeypatch)
    await seed_superadmin.seed()

    resp = await client.post(
        "/api/auth/superadmin/login",
        json={"email": "  SuperAdmin@Strivenest.com  ", "password": settings.SEED_SUPERADMIN_PASSWORD},
    )
    assert resp.status_code == 200, resp.text
