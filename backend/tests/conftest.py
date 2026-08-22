"""
Shared pytest fixtures. Uses mongomock-motor (an in-memory async MongoDB
double) so the whole suite runs without a real MongoDB server, and an
httpx.AsyncClient wired directly to the FastAPI ASGI app.
"""
import asyncio
import sys
import os

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from mongomock_motor import AsyncMongoMockClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database.mongodb as mongodb_mod  # noqa: E402
from utils.security import hash_password, generate_id  # noqa: E402
from config import settings  # noqa: E402

# The password every test applicant registers with (submitted, hashed, and
# used as their real employee login password once a SuperAdmin approves).
DEFAULT_APPLICANT_PASSWORD = "Applicant@123"


@pytest_asyncio.fixture
async def db():
    mongodb_mod.mongodb.client = AsyncMongoMockClient()
    mongodb_mod.mongodb.db = mongodb_mod.mongodb.client["strivenest_test"]
    await mongodb_mod.ensure_indexes()
    yield mongodb_mod.mongodb.db


@pytest_asyncio.fixture
async def superadmin_user(db):
    user = {
        "user_id": generate_id("USR"),
        "name": "Super Admin",
        "email": "superadmin@strivenest.com",
        "mobile": "9876543210",
        "password_hash": hash_password("SuperAdmin@123"),
        "role": "SUPERADMIN",
        "status": "ACTIVE",
        "created_date": __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
    }
    await db.users.insert_one(user)
    return user


@pytest_asyncio.fixture
async def subadmin_user(db):
    # Uses the same official SEED_SUBADMIN_* values as seed_subadmin.py /
    # backend/.env (subadmin@strivenest.com / Subadmin@12) instead of the old,
    # never-actually-seeded subadmin@strivenest.com / SubAdmin@123 -- those
    # stale test-only credentials never matched the real demo account and
    # were a leftover inconsistency across the project.
    user = {
        "user_id": generate_id("USR"),
        "name": settings.SEED_SUBADMIN_NAME,
        "email": settings.SEED_SUBADMIN_EMAIL,
        "mobile": settings.SEED_SUBADMIN_MOBILE,
        "password_hash": hash_password(settings.SEED_SUBADMIN_PASSWORD),
        "role": "SUBADMIN",
        "status": "ACTIVE",
        "created_date": __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
    }
    await db.users.insert_one(user)
    return user


@pytest_asyncio.fixture
async def client(db):
    import server  # imported after db fixture patches mongodb_mod

    transport = ASGITransport(app=server.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def superadmin_token(client, superadmin_user):
    resp = await client.post(
        "/api/auth/superadmin/login",
        json={"email": "superadmin@strivenest.com", "password": "SuperAdmin@123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def superadmin_headers(superadmin_token):
    return {"Authorization": f"Bearer {superadmin_token}"}


@pytest_asyncio.fixture
async def subadmin_token(client, subadmin_user):
    resp = await client.post(
        "/api/auth/subadmin/login",
        json={"email": settings.SEED_SUBADMIN_EMAIL, "password": settings.SEED_SUBADMIN_PASSWORD},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def subadmin_headers(subadmin_token):
    return {"Authorization": f"Bearer {subadmin_token}"}


def sample_application_payload(**overrides):
    payload = {
        "full_name": "Rahul Kumar",
        "email": "rahul.kumar@example.com",
        "password": DEFAULT_APPLICANT_PASSWORD,
        "confirm_password": DEFAULT_APPLICANT_PASSWORD,
        "mobile": "9812345678",
        "dob": "1998-04-12",
        "gender": "Male",
        "address": "123 MG Road, Bengaluru",
        "department": "Engineering",
        "designation": "Software Engineer",
        "qualification": "B.Tech Computer Science",
        "experience": "2 years",
    }
    payload.update(overrides)
    return payload
