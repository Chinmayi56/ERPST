import hashlib

class CryptContext:
    """Minimal stand-in for passlib's bcrypt CryptContext, for offline
    functional testing only -- NOT cryptographically equivalent to bcrypt.
    Only used in this sandbox's test harness; never shipped in the deliverable."""
    def __init__(self, schemes=None, deprecated="auto"):
        pass

    def hash(self, plain_password: str) -> str:
        salted = ("teststub$" + plain_password).encode("utf-8")
        return "teststub$" + hashlib.sha256(salted).hexdigest()

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return self.hash(plain_password) == hashed_password
