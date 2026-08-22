class HTTPException(Exception):
    def __init__(self, status_code=None, detail=None):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)

class _Status:
    HTTP_200_OK = 200
    HTTP_400_BAD_REQUEST = 400
    HTTP_401_UNAUTHORIZED = 401
    HTTP_403_FORBIDDEN = 403
    HTTP_404_NOT_FOUND = 404
    HTTP_409_CONFLICT = 409
    HTTP_500_INTERNAL_SERVER_ERROR = 500

status = _Status()

def Depends(*a, **k):
    return None

def Query(*a, **k):
    return None

def File(*a, **k):
    return None

class UploadFile:
    """Minimal stand-in; real UploadFile is a Starlette type not needed by
    any service-layer logic this harness exercises."""
    pass

class APIRouter:
    def __init__(self, *a, **k):
        pass
    def get(self, *a, **k):
        def deco(fn): return fn
        return deco
    def post(self, *a, **k):
        def deco(fn): return fn
        return deco
    def patch(self, *a, **k):
        def deco(fn): return fn
        return deco
    def put(self, *a, **k):
        def deco(fn): return fn
        return deco
    def delete(self, *a, **k):
        def deco(fn): return fn
        return deco
