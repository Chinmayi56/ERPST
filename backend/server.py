"""
Strivenest Technologies — SuperAdmin Backend
ONE FastAPI application. ONE MongoDB database. Serves the SuperAdmin portal
in this phase; SubAdmin and Employee roles/routes can be added later without
creating another backend.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from database.mongodb import connect_to_mongo, close_mongo_connection, get_db

from routes import (
    auth,
    superadmin,
    subadmin,
    applications,
    employees,
    registration_links,
    notifications,
    health,
    employee_applications,
    uploads,
    employee_portal,
    erp,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Hard safety boundary: DEMO_MODE enables a fixed/mock mobile-OTP login
    # (used by both the SuperAdmin and SubAdmin portals) and demo seed
    # accounts with known passwords. Neither has a real SMS provider or
    # production-grade credential behind it, so this refuses to even start
    # the app if someone deploys with ENVIRONMENT=production while
    # DEMO_MODE is still true (or left at its default) -- misconfiguration
    # fails loudly at startup instead of silently shipping a backdoor.
    if settings.ENVIRONMENT == "production" and settings.DEMO_MODE:
        raise RuntimeError(
            "Refusing to start: DEMO_MODE=true while ENVIRONMENT=production. "
            "Set DEMO_MODE=false (and remove/rotate any demo seed accounts) "
            "before deploying to production."
        )
    await connect_to_mongo()
    # Guarantee the SuperAdmin account exists on every startup -- same
    # idempotent/self-healing seed_core() pattern as SubAdmin/Employee below.
    # Previously this required a manual `python seed_superadmin.py` run on
    # the deploy host; skipping that step is exactly what makes SuperAdmin
    # login fail with "Invalid email or password" in a fresh production
    # deploy (no matching `users` record exists yet). This never overwrites
    # an existing account's user_id or unrelated fields -- it only creates
    # the account if missing, or re-syncs password/role/status if they've
    # drifted from SEED_SUPERADMIN_EMAIL/PASSWORD.
    try:
        from seed_superadmin import seed_core as seed_superadmin_core
        await seed_superadmin_core(get_db())
    except Exception as exc:  # never let seeding block startup
        print(f"[startup] SuperAdmin seeding skipped due to an error: {exc}")
    # Guarantee the demo SubAdmin and demo Employee login accounts exist on
    # every startup, the same way they're meant to exist per
    # RUN_COMMANDS.txt (via `python seed_subadmin.py` /
    # `python seed_demo_employee.py`) -- those are separate manual steps
    # that are easy to skip, and skipping either is exactly what makes the
    # corresponding demo credentials shown on that portal's login page fail
    # with "Invalid email or password" (no matching `users` record exists
    # at all, so login_with_email_password's `if not user` branch is hit).
    # This calls the existing, already-idempotent/self-healing seeding
    # logic (a direct `users` insert for SubAdmin, the real
    # application -> SuperAdmin-approval flow for Employee); it changes no
    # authentication behavior and never touches SuperAdmin seeding, which
    # stays manual/unchanged.
    try:
        from seed_subadmin import seed_core as seed_subadmin_core
        await seed_subadmin_core(get_db())
    except Exception as exc:  # never let demo-account seeding block startup
        print(f"[startup] Demo SubAdmin seeding skipped due to an error: {exc}")
    try:
        from seed_demo_employee import seed_core as seed_demo_employee_core
        await seed_demo_employee_core(get_db())
    except Exception as exc:  # never let demo-account seeding block startup
        print(f"[startup] Demo Employee seeding skipped due to an error: {exc}")
    yield
    await close_mongo_connection()


app = FastAPI(
    title="Strivenest Technologies API",
    description=(
        "Single FastAPI backend for the Strivenest Technologies platform. "
        "Currently serves the SuperAdmin portal (auth, employee applications, "
        "employees, registration links, notifications, dashboard). "
        "Designed so SubAdmin and Employee roles can be added later on the "
        "same backend and database."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Never leak stack traces, database details or secrets to the client.
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(superadmin.router)
app.include_router(applications.router)
app.include_router(employees.router)
app.include_router(employees.public_router)
app.include_router(registration_links.router)
app.include_router(notifications.router)
app.include_router(employee_applications.router)
app.include_router(uploads.router)
app.include_router(employee_portal.router)
app.include_router(erp.router)

# SubAdmin routers: identical implementations to the SuperAdmin ones above
# (see each module's build_*_router factory), gated by require_subadmin
# instead, sharing the exact same MongoDB collections.
app.include_router(subadmin.router)
app.include_router(applications.subadmin_router)
app.include_router(employees.subadmin_router)
app.include_router(registration_links.subadmin_router)
app.include_router(notifications.subadmin_router)
app.include_router(erp.subadmin_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "Strivenest Technologies API",
        "docs": "/docs",
        "health": "/api/health",
    }
