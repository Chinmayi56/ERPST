from enum import IntEnum


class ReturnDocument(IntEnum):
    """Stub mirroring pymongo.ReturnDocument (BEFORE=False, AFTER=True)."""
    BEFORE = False
    AFTER = True
