"""
Centralized application configuration.
Reads values from environment variables (loaded from .env via python-dotenv).
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    MONGO_URL: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "strivenest")

    JWT_SECRET: str = os.getenv("JWT_SECRET", "change_this_secret")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

    CORS_ORIGINS: list = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:3001,http://localhost:3002,"
            "http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:3002",
        ).split(",")
        if origin.strip()
    ]

    EMPLOYEE_PORTAL_URL: str = os.getenv("EMPLOYEE_PORTAL_URL", "http://localhost:3002")

    # Deployment environment: "development" (default) or "production".
    # Controls whether DEMO_MODE (fixed/mock OTP + demo seed accounts) is
    # allowed to run at all -- see the DEMO_MODE check just below and the
    # startup guard in server.py's lifespan.
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").strip().lower()

    # Demo mode gates every fixed/mock-credential mechanism in this codebase
    # (the shared SuperAdmin/SubAdmin mobile-OTP demo flow in
    # services/auth_service.py, and the SEED_SUBADMIN_* demo account below).
    # It defaults to on for local development, but server.py refuses to
    # start if ENVIRONMENT=production and DEMO_MODE is still true -- a
    # fixed OTP / seeded demo password must never be reachable in a real
    # deployment, so misconfiguration fails loudly at startup instead of
    # silently shipping a backdoor.
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").strip().lower() in ("1", "true", "yes", "on")

    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "5"))

    SEED_SUPERADMIN_EMAIL: str = os.getenv("SEED_SUPERADMIN_EMAIL", "superadmin@strivenest.com")
    SEED_SUPERADMIN_PASSWORD: str = os.getenv("SEED_SUPERADMIN_PASSWORD", "SuperAdmin@123")
    SEED_SUPERADMIN_MOBILE: str = os.getenv("SEED_SUPERADMIN_MOBILE", "9876543210")
    SEED_SUPERADMIN_NAME: str = os.getenv("SEED_SUPERADMIN_NAME", "Super Admin")

    DEMO_OTP: str = os.getenv("DEMO_OTP", "123456")

    # Demo SubAdmin seed account (used only by seed_subadmin.py, and only
    # when DEMO_MODE is true -- see the guard at the top of that script),
    # following the exact same seeding pattern as SEED_SUPERADMIN_*.
    # Deliberately a different email/mobile/password from the SuperAdmin
    # demo account so the two roles never share credentials.
    SEED_SUBADMIN_EMAIL: str = os.getenv("SEED_SUBADMIN_EMAIL", "subadmin@strivenest.com")
    SEED_SUBADMIN_PASSWORD: str = os.getenv("SEED_SUBADMIN_PASSWORD", "Subadmin@12")
    SEED_SUBADMIN_MOBILE: str = os.getenv("SEED_SUBADMIN_MOBILE", "9876543212")
    SEED_SUBADMIN_NAME: str = os.getenv("SEED_SUBADMIN_NAME", "Sub Admin")

    # Demo Employee seed account (used only by seed_demo_employee.py). Created
    # via the real application -> SuperAdmin-approval flow so it is gated
    # exactly like any other employee account.
    SEED_EMPLOYEE_EMAIL: str = os.getenv("SEED_EMPLOYEE_EMAIL", "nithin@strivenest.com")
    SEED_EMPLOYEE_PASSWORD: str = os.getenv("SEED_EMPLOYEE_PASSWORD", "Nithin@12")
    SEED_EMPLOYEE_MOBILE: str = os.getenv("SEED_EMPLOYEE_MOBILE", "9876543211")
    SEED_EMPLOYEE_NAME: str = os.getenv("SEED_EMPLOYEE_NAME", "Demo Employee")


settings = Settings()
