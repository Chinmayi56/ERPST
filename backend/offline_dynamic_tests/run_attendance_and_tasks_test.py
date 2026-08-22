"""
Offline verification for:
  1. services/attendance_service.py -- automatic check-in on employee login
     and check-out on logout, against the real unmodified service code.
  2. routes/erp.py -- the new "tasks" module's MODULE/ID_FIELDS/STATUS_VALUES/
     DEFAULT_STATUS/SEARCH_FIELDS config is present and internally consistent
     with every other ERP module (routes/erp.py itself can't be fully driven
     here without a pydantic/UploadFile stub, which doesn't exist in this
     harness -- see stubs/ -- but its generic create/update/delete/list
     functions are shared, already-audited code paths; this checks the
     "tasks" wiring that's unique to this change).

Run with only the Python standard library, no installs:
    python3 offline_dynamic_tests/run_attendance_and_tasks_test.py
"""
import sys, os, asyncio

HERE = os.path.dirname(os.path.abspath(__file__))
STUBS = os.path.join(HERE, "stubs")
BACKEND = os.path.dirname(HERE)
sys.path.insert(0, STUBS)
sys.path.insert(0, BACKEND)

os.environ["MONGO_URL"] = "mongodb://localhost:27017"
os.environ["JWT_SECRET"] = "test-secret"

from fakedb import FakeDB
import database.mongodb as mongodb_module

fake_db = FakeDB()
mongodb_module.mongodb.db = fake_db

from services import attendance_service

results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    mark = "PASS" if cond else "FAIL"
    print(f"[{mark}] {name}" + (f" -- {detail}" if detail and not cond else ""))


async def main():
    employee = {"employee_id": "EMP000123", "full_name": "Asha Rao"}

    # --- Attendance auto-recording ---------------------------------------
    record = await attendance_service.record_login(employee)
    check("First login of the day creates an attendance record", record is not None)
    check("Record has today's employee_id", record.get("employee_id") == "EMP000123")
    check("Record has a check_in time", bool(record.get("check_in")))
    check("Record has no check_out yet", record.get("check_out") is None)
    check("Status is PRESENT or LATE", record.get("status") in ("PRESENT", "LATE"))

    count_after_first_login = await fake_db.attendance.count_documents({"employee_id": "EMP000123"})
    check("Exactly one attendance record after first login", count_after_first_login == 1, str(count_after_first_login))

    # A second login the same day must NOT create a duplicate record or
    # overwrite the original check-in time.
    original_check_in = record["check_in"]
    record2 = await attendance_service.record_login(employee)
    count_after_second_login = await fake_db.attendance.count_documents({"employee_id": "EMP000123"})
    check("Second login same day does not duplicate the record", count_after_second_login == 1, str(count_after_second_login))
    check("Second login does not overwrite the original check-in time", record2.get("check_in") == original_check_in)

    # Logout should fill in check_out and compute hours.
    logout_record = await attendance_service.record_logout("EMP000123")
    check("Logout finds and updates today's record", logout_record is not None)
    check("Logout sets check_out", bool(logout_record.get("check_out")))
    check("Logout computes non-negative hours", (logout_record.get("hours") or 0) >= 0)

    # Logout for an employee with no record today should be a safe no-op.
    missing = await attendance_service.record_logout("EMP-NOBODY")
    check("Logout for an employee with no record today returns None safely", missing is None)

    # --- Tasks module config consistency in routes/erp.py ----------------
    import importlib.util
    erp_path = os.path.join(BACKEND, "routes", "erp.py")
    # Load routes/erp.py's module-level config dicts directly via source
    # exec in an isolated namespace, without importing FastAPI route
    # decorators (which this harness's fastapi stub doesn't fully support:
    # no UploadFile/File, no router.delete). This still executes the real,
    # unmodified file top-to-bottom up to (and including) the config dicts.
    with open(erp_path) as f:
        source = f.read()
    # Only take the part of the file up to (and including) the validate()
    # function definition -- everything before the first @router.* line --
    # so we never need the parts of the fastapi stub that don't exist.
    cutoff = source.index("@router.get(\"/options/employees\")")
    partial_source = source[:cutoff]
    ns = {"__name__": "erp_config_check"}
    exec(compile(partial_source, erp_path, "exec"), ns)

    MODULES = ns["MODULES"]
    ID_FIELDS = ns["ID_FIELDS"]
    STATUS_VALUES = ns["STATUS_VALUES"]
    DEFAULT_STATUS = ns["DEFAULT_STATUS"]
    SEARCH_FIELDS = ns["SEARCH_FIELDS"]

    check("'tasks' is registered as an ERP module", "tasks" in MODULES)
    check("'tasks' has an ID_FIELDS entry", ID_FIELDS.get("tasks") == "task_id")
    check("'tasks' has STATUS_VALUES defined", "tasks" in STATUS_VALUES and len(STATUS_VALUES["tasks"]) > 0)
    check("'tasks' has a DEFAULT_STATUS that is itself a valid status", DEFAULT_STATUS.get("tasks") in STATUS_VALUES.get("tasks", set()))
    check("'tasks' has SEARCH_FIELDS defined", "tasks" in SEARCH_FIELDS and len(SEARCH_FIELDS["tasks"]) > 0)
    check(
        "Every module has matching ID_FIELDS/STATUS_VALUES/DEFAULT_STATUS/SEARCH_FIELDS entries",
        MODULES == set(ID_FIELDS) == set(STATUS_VALUES) == set(DEFAULT_STATUS) == set(SEARCH_FIELDS),
    )

    # Validate the task-specific validation rules (title required, progress
    # bounds) using the real validate() function from the same partial exec.
    validate = ns["validate"]
    from fastapi import HTTPException

    try:
        validate("tasks", {})
        check("validate() rejects a task with no title", False)
    except HTTPException as exc:
        check("validate() rejects a task with no title", exc.status_code == 400)

    try:
        validate("tasks", {"title": "Write proposal", "progress": 150})
        check("validate() rejects progress > 100", False)
    except HTTPException as exc:
        check("validate() rejects progress > 100", exc.status_code == 400)

    try:
        validate("tasks", {"title": "Write proposal", "progress": 40})
    except HTTPException:
        check("validate() accepts a well-formed task", False)
    else:
        check("validate() accepts a well-formed task", True)

    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"\n=== {passed}/{total} checks passed ===")
    if passed != total:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
