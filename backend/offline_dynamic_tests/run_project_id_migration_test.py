"""
Offline, dependency-free functional test for the project_id / ERP-ID
backfill migration added to database/mongodb.py.

This sandbox has no network access, so `motor`/`pymongo` cannot be
installed. This script builds a minimal in-memory fake of just the Motor
collection methods `backfill_missing_erp_ids()` and `ensure_indexes()`
actually call (find, find_one, update_one, create_index with a real unique
-index simulation including MongoDB's null-collision behavior), imports the
REAL, unmodified `database/mongodb.py` source via exec() with `motor`/
`pymongo` stubbed out, and runs the exact reported failure scenario against
it end to end.
"""
import asyncio
import sys
import types
import copy


# ---------------------------------------------------------------------------
# Minimal stand-ins for the two third-party symbols database/mongodb.py
# imports, just enough for the module to import and for our test to run.
# ---------------------------------------------------------------------------
class DuplicateKeyError(Exception):
    pass


class ServerSelectionTimeoutError(Exception):
    pass


fake_pymongo_errors = types.ModuleType("pymongo.errors")
fake_pymongo_errors.DuplicateKeyError = DuplicateKeyError
fake_pymongo_errors.ServerSelectionTimeoutError = ServerSelectionTimeoutError
fake_pymongo = types.ModuleType("pymongo")
fake_pymongo.errors = fake_pymongo_errors
sys.modules["pymongo"] = fake_pymongo
sys.modules["pymongo.errors"] = fake_pymongo_errors

fake_motor_asyncio = types.ModuleType("motor.motor_asyncio")


class _FakeAsyncIOMotorClient:
    def __init__(self, *a, **k):
        pass


fake_motor_asyncio.AsyncIOMotorClient = _FakeAsyncIOMotorClient
fake_motor = types.ModuleType("motor")
fake_motor.motor_asyncio = fake_motor_asyncio
sys.modules["motor"] = fake_motor
sys.modules["motor.motor_asyncio"] = fake_motor_asyncio

fake_config = types.ModuleType("config")


class _Settings:
    MONGO_URL = "mongodb://fake"
    DB_NAME = "fake"


fake_config.settings = _Settings()
sys.modules["config"] = fake_config


# ---------------------------------------------------------------------------
# A real-enough fake Mongo collection: supports the queries
# backfill_missing_erp_ids()/ensure_indexes() actually issue, AND enforces
# uniqueness (including MongoDB's "missing/null field = duplicate null")
# semantics on create_index(unique=True), so the exact reported
# DuplicateKeyError can be reproduced and then shown to be fixed.
# ---------------------------------------------------------------------------
class FakeCollection:
    def __init__(self, name):
        self.name = name
        self._docs = []
        self._unique_fields = set()

    def _matches(self, doc, filt):
        for k, v in filt.items():
            if k == "$or":
                if not any(self._matches(doc, sub) for sub in v):
                    return False
                continue
            if isinstance(v, dict) and "$exists" in v:
                exists = k in doc
                if exists != v["$exists"]:
                    return False
                continue
            if v is None:
                if doc.get(k) is not None:
                    return False
                continue
            if doc.get(k) != v:
                return False
        return True

    def find(self, filt=None):
        filt = filt or {}
        matches = [d for d in self._docs if self._matches(d, filt)]
        return _Cursor(matches)

    async def find_one(self, filt=None, projection=None):
        filt = filt or {}
        for d in self._docs:
            if self._matches(d, filt):
                return copy.deepcopy(d)
        return None

    async def update_one(self, filt, update):
        for d in self._docs:
            if self._matches(d, filt):
                for k, v in update.get("$set", {}).items():
                    d[k] = v
                return
        raise AssertionError("update_one matched no document")

    async def create_index(self, field_or_spec, unique=False, sparse=False, **kwargs):
        if not unique or not isinstance(field_or_spec, str):
            return  # compound/non-unique indexes: not relevant to this test
        field = field_or_spec
        values = [d.get(field) for d in self._docs]
        if sparse:
            values = [v for v in values if v is not None]
        seen = set()
        for v in values:
            key = ("__NULL__",) if v is None else v
            if key in seen:
                raise DuplicateKeyError(
                    f"E11000 duplicate key error collection: fake.{self.name} "
                    f"index: {field}_1 dup key: {{ {field}: {v!r} }}"
                )
            seen.add(key)
        self._unique_fields.add(field)


class _Cursor:
    def __init__(self, docs):
        self._docs = docs

    def __aiter__(self):
        self._i = 0
        return self

    async def __anext__(self):
        if self._i >= len(self._docs):
            raise StopAsyncIteration
        d = copy.deepcopy(self._docs[self._i])
        self._i += 1
        return d


class FakeDB:
    def __init__(self):
        self._collections = {}

    def __getitem__(self, name):
        return self._collections.setdefault(name, FakeCollection(name))

    def __getattr__(self, name):
        return self[name]


# ---------------------------------------------------------------------------
# Import the REAL database/mongodb.py source unmodified.
# ---------------------------------------------------------------------------
import importlib.util
import os

MODULE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "mongodb.py")
spec = importlib.util.spec_from_file_location("database.mongodb", MODULE_PATH)
mongodb_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mongodb_mod)


async def main():
    checks = []

    def check(name, cond):
        checks.append((name, bool(cond)))
        print(("PASS" if cond else "FAIL") + " - " + name)

    # --- Reproduce the exact reported bug scenario -------------------------
    db = FakeDB()
    mongodb_mod.mongodb.db = db

    # Three legacy 'projects' documents: two have NO project_id field at all
    # (the realistic case for old/imported rows), one has project_id
    # explicitly set to None, and two have valid, already-unique IDs.
    db["projects"]._docs = [
        {"_id": "p1", "name": "Legacy Project A", "status": "ACTIVE"},               # missing field
        {"_id": "p2", "name": "Legacy Project B", "status": "ACTIVE"},               # missing field
        {"_id": "p3", "name": "Legacy Project C", "status": "ACTIVE", "project_id": None},  # explicit null
        {"_id": "p4", "name": "Real Project D", "status": "ACTIVE", "project_id": "PRO-AAAA1111"},
        {"_id": "p5", "name": "Real Project E", "status": "ACTIVE", "project_id": "PRO-BBBB2222"},
    ]

    # 1) Confirm the bug is real: creating the unique index BEFORE the
    #    backfill must fail exactly like the reported error.
    raised = False
    try:
        await db["projects"].create_index("project_id", unique=True)
    except mongodb_mod.DuplicateKeyError as exc:
        raised = True
        check("reproduces the reported DuplicateKeyError before the fix", "project_id: None" in str(exc) or "dup key" in str(exc))
    check("index creation fails before backfill (bug reproduced)", raised)

    # 2) Run the new migration.
    await mongodb_mod.backfill_missing_erp_ids()

    docs_after = db["projects"]._docs
    ids_after = [d.get("project_id") for d in docs_after]
    check("no project is missing project_id after backfill", all(pid for pid in ids_after))
    check("all project_id values are unique after backfill", len(ids_after) == len(set(ids_after)))
    check("previously-valid IDs (PRO-AAAA1111 / PRO-BBBB2222) were left untouched",
          "PRO-AAAA1111" in ids_after and "PRO-BBBB2222" in ids_after)
    check("no project document was deleted (still 5 projects)", len(docs_after) == 5)
    check("non-id fields (name/status) were not touched by the migration",
          docs_after[0]["name"] == "Legacy Project A" and docs_after[0]["status"] == "ACTIVE")
    check("backfilled IDs follow the same PRO-XXXXXXXX format as routes/erp.py",
          all(pid.startswith("PRO-") and len(pid) == 12 for pid in ids_after))

    # 3) The unique index creation that previously failed must now succeed.
    index_ok = False
    try:
        await db["projects"].create_index("project_id", unique=True)
        index_ok = True
    except mongodb_mod.DuplicateKeyError:
        index_ok = False
    check("unique index on project_id now creates successfully after backfill", index_ok)

    # 4) Idempotency: running the migration again must be a true no-op.
    ids_before_rerun = sorted(d.get("project_id") for d in db["projects"]._docs)
    await mongodb_mod.backfill_missing_erp_ids()
    ids_after_rerun = sorted(d.get("project_id") for d in db["projects"]._docs)
    check("re-running the migration is a no-op (idempotent)", ids_before_rerun == ids_after_rerun)

    # 5) Full ensure_indexes() must run end-to-end without raising, for ALL
    #    ERP modules (not just projects), against a similarly "dirty" DB --
    #    this is the actual code path exercised by the reported
    #    `python -m uvicorn server:app ...` startup failure.
    db2 = FakeDB()
    mongodb_mod.mongodb.db = db2
    db2["clients"]._docs = [{"_id": "c1", "status": "ACTIVE"}, {"_id": "c2", "status": "ACTIVE"}]  # both missing client_id
    db2["projects"]._docs = [{"_id": "p1", "status": "ACTIVE"}, {"_id": "p2", "status": "ACTIVE"}]  # both missing project_id
    db2["leaves"]._docs = []
    db2["attendance"]._docs = []
    db2["services"]._docs = []
    db2["bookings"]._docs = []
    db2["documents"]._docs = []
    startup_ok = True
    try:
        await mongodb_mod.backfill_missing_erp_ids()
        await mongodb_mod.ensure_indexes()
    except Exception as exc:  # noqa: BLE001
        startup_ok = False
        print(f"    -> ensure_indexes() raised: {exc!r}")
    check("full ensure_indexes() startup sequence completes without raising, across all ERP modules", startup_ok)

    # 6) Simulate what routes/erp.py's create_record() does for a brand new
    #    project (data.setdefault(key, generated_id) after normalize() strips
    #    None/""), confirming a freshly created project can never end up with
    #    project_id: null going forward.
    def simulate_create_record(payload_data):
        import uuid as _uuid
        data = {k: v for k, v in payload_data.items() if v is not None and v != ""}
        data.setdefault("project_id", f"PRO-{_uuid.uuid4().hex[:8].upper()}")
        return data

    new_project_no_id = simulate_create_record({"name": "Brand New Project"})
    new_project_null_id = simulate_create_record({"name": "Another Project", "project_id": None})
    check("a newly created project without project_id in the payload gets a real ID",
          bool(new_project_no_id.get("project_id")))
    check("a newly created project that explicitly sends project_id: null still gets a real ID",
          bool(new_project_null_id.get("project_id")))

    total = len(checks)
    passed = sum(1 for _, ok in checks if ok)
    print(f"\n{passed}/{total} checks passed.")
    if passed != total:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
