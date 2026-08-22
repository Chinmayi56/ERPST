"""
FastAPI dependencies for authentication and role-based authorization.
Every protected SuperAdmin endpoint depends on `require_superadmin`, which
validates the JWT on the server (frontend-only protection is not trusted).
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from utils.jwt import decode_access_token
from database.mongodb import get_db

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    db = get_db()
    user = await db.users.find_one({"user_id": payload.get("user_id")})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if user.get("status") != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active",
        )

    return user


async def require_superadmin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Role gate: only SUPERADMIN may call SuperAdmin APIs.
    SUBADMIN / EMPLOYEE roles can be added later without touching this backend's
    architecture — just add new role-gate dependencies alongside this one.
    """
    if current_user.get("role") != "SUPERADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SuperAdmin access required",
        )
    return current_user


async def require_employee(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Role gate: only EMPLOYEE users may call Employee Portal APIs.
    `get_current_user` already re-verifies the user's `status` is ACTIVE on
    every request (not just at login), so a SuperAdmin deactivating an
    employee mid-session immediately blocks their next API call with 403 —
    no need to wait for the JWT to expire.
    """
    if current_user.get("role") != "EMPLOYEE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employee access required",
        )
    return current_user


async def require_subadmin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Role gate: only SUBADMIN users may call SubAdmin APIs.
    Mirrors `require_superadmin` exactly (JWT validated, user loaded and
    re-checked ACTIVE by `get_current_user`, then the role itself is
    checked here) so SUBADMIN gets the same server-enforced protection as
    SUPERADMIN -- a SUPERADMIN or EMPLOYEE token is rejected with 403, never
    trusted from the frontend.
    """
    if current_user.get("role") != "SUBADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SubAdmin access required",
        )
    return current_user
