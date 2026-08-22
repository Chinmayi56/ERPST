class HTTPAuthorizationCredentials:
    def __init__(self, scheme="Bearer", credentials=""):
        self.scheme = scheme
        self.credentials = credentials

class HTTPBearer:
    def __init__(self, auto_error=True):
        self.auto_error = auto_error
