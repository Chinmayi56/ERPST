"""
Password hashing helpers (bcrypt via passlib) and secure token generation.
Never store or log plain passwords.
"""
import secrets
import hashlib
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def generate_secure_token(num_bytes: int = 32) -> str:
    """Generate a cryptographically secure URL-safe token (for registration links, etc.)."""
    return secrets.token_urlsafe(num_bytes)


def hash_token(token: str) -> str:
    """Store only a hash of shareable tokens, never the raw token, in the database."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_id(prefix: str) -> str:
    """Generate a readable unique ID, e.g. APP-9F3C2A1B."""
    return f"{prefix}-{secrets.token_hex(6).upper()}"


def generate_temp_password(length: int = 12) -> str:
    """Generate a random temporary password shown once to SuperAdmin after approval.
    Never persisted in plain text — only its bcrypt hash is stored."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length)) + "!9"
