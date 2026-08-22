"""
Automatic attendance recording, driven only by real employee login/logout
events -- no manual entry, no mock/demo data. Exactly one `attendance`
document exists per employee per calendar day (the same collection and
document shape the SuperAdmin Attendance module already reads/writes via
`routes/erp.py`, so records created here show up there immediately, are
searchable/filterable, and remain after refresh since they're persisted in
MongoDB like everything else).

- check-in is recorded on the employee's *first* successful login of the
  day; later logins the same day never overwrite it.
- check-out is recorded on logout (or on the next day's first login, in
  case the employee never explicitly logged out) and `hours` is computed
  from the recorded check-in/check-out times.
- status is derived automatically: PRESENT by default, LATE if the first
  login lands after the configured cutoff.
"""
from datetime import datetime, timezone, time
from typing import Optional
import uuid

from database.mongodb import get_db

LATE_CUTOFF = time(9, 30)  # after 9:30 AM local-server time counts as LATE


def _today_str(now: datetime) -> str:
    return now.date().isoformat()


def _time_str(now: datetime) -> str:
    return now.strftime("%H:%M")


async def record_login(employee: dict) -> dict:
    """Upsert today's attendance record for this employee's check-in."""
    db = get_db()
    now = datetime.now(timezone.utc)
    today = _today_str(now)
    employee_id = employee["employee_id"]

    existing = await db.attendance.find_one({"employee_id": employee_id, "date": today})
    if existing:
        # Already checked in today -- don't overwrite the first check-in,
        # just bump updated_at so we know the employee is active.
        await db.attendance.update_one(
            {"_id": existing["_id"]}, {"$set": {"updated_at": now.isoformat()}}
        )
        existing.pop("_id", None)
        return existing

    status = "LATE" if now.time() > LATE_CUTOFF else "PRESENT"
    record = {
        "attendance_id": f"ATT-{uuid.uuid4().hex[:8].upper()}",
        "employee_id": employee_id,
        "employee_name": employee.get("full_name"),
        "date": today,
        "check_in": _time_str(now),
        "check_out": None,
        "hours": None,
        "status": status,
        "notes": "Auto-recorded from login",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "created_by": "SYSTEM_LOGIN",
    }
    await db.attendance.insert_one(record)
    record.pop("_id", None)
    return record


async def record_logout(employee_id: str) -> Optional[dict]:
    """Record check-out time (and computed hours) on today's attendance record, if any."""
    db = get_db()
    now = datetime.now(timezone.utc)
    today = _today_str(now)

    existing = await db.attendance.find_one({"employee_id": employee_id, "date": today})
    if not existing:
        return None

    update = {"check_out": _time_str(now), "updated_at": now.isoformat()}

    check_in = existing.get("check_in")
    if check_in:
        try:
            in_dt = datetime.strptime(check_in, "%H:%M")
            out_dt = datetime.strptime(update["check_out"], "%H:%M")
            hours = (out_dt - in_dt).total_seconds() / 3600
            if hours < 0:
                hours += 24
            update["hours"] = round(hours, 2)
        except ValueError:
            pass

    # return_document=True is equivalent to pymongo.ReturnDocument.AFTER
    # (ReturnDocument is an IntEnum where AFTER == True) -- passing the bool
    # directly avoids importing pymongo here just for this one enum.
    result = await db.attendance.find_one_and_update(
        {"_id": existing["_id"]}, {"$set": update}, return_document=True
    )
    if result:
        result.pop("_id", None)
    return result
