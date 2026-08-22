"""
Sequential, human-readable ID generation backed by an atomic MongoDB counter.
Produces IDs like EMP-2026-00124 (employee applications) using a single
findOneAndUpdate $inc — safe under concurrent requests, no duplicates.
"""
from datetime import datetime, timezone

from database.mongodb import get_db


async def next_sequence_id(prefix: str, scope: str) -> str:
    """
    Atomically increments and returns a zero-padded sequence number for the
    given (prefix, scope) pair, e.g. next_sequence_id("EMP", "2026") -> 124.
    """
    db = get_db()
    counter_key = f"{prefix}:{scope}"
    result = await db.counters.find_one_and_update(
        {"_id": counter_key},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    return result["seq"]


async def generate_application_id() -> str:
    """Generate an application ID like EMP-2026-00124."""
    year = str(datetime.now(timezone.utc).year)
    seq = await next_sequence_id("APPSEQ", year)
    return f"EMP-{year}-{seq:05d}"


async def generate_employee_id() -> str:
    """Generate an employee ID like EMP000124."""
    seq = await next_sequence_id("EMPIDSEQ", "ALL")
    return f"EMP{seq:06d}"
