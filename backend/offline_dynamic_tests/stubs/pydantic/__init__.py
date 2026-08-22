"""Minimal pydantic stand-in: just enough for module-level `class X(BaseModel)`
declarations with Field(...) defaults to import cleanly. Not a validator --
no service-layer logic in this harness depends on real pydantic validation
(routes/*.py request/response models are exercised by the real pytest suite
in tests/, which uses the real pydantic; this harness only needs the module
to import without error).
"""


class BaseModel:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def Field(default=None, *a, **k):
    return default


class EmailStr(str):
    pass
