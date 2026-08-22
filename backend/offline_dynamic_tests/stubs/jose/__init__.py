import json, hmac, hashlib, base64, time

class JWTError(Exception):
    pass

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _unb64(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)

class _JWT:
    def encode(self, payload, key, algorithm="HS256"):
        body = dict(payload)
        for k, v in list(body.items()):
            if hasattr(v, "isoformat"):
                body[k] = v.isoformat()
        header = {"alg": algorithm, "typ": "JWT"}
        h = _b64(json.dumps(header).encode())
        p = _b64(json.dumps(body).encode())
        sig = hmac.new(key.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
        s = _b64(sig)
        return f"{h}.{p}.{s}"

    def decode(self, token, key, algorithms=None):
        try:
            h, p, s = token.split(".")
        except ValueError:
            raise JWTError("Malformed token")
        expected_sig = _b64(hmac.new(key.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(expected_sig, s):
            raise JWTError("Signature verification failed")
        payload = json.loads(_unb64(p))
        return payload

jwt = _JWT()
