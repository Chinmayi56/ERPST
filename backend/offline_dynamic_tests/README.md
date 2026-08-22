# Offline dynamic tests (no MongoDB / no pip install required)

This folder is **not part of the app** — it's the harness used to actually
execute the real, unmodified `services/*.py` business logic end-to-end in an
environment with no network access (so `pip install fastapi/motor/...` isn't
possible) and no MongoDB running.

It works by:
- `stubs/` — tiny stand-in modules for `fastapi`, `passlib`, `python-jose`,
  `motor`, and `pymongo` that implement just enough surface area (exceptions,
  status codes, a JWT-shaped encode/decode, a hash/verify pair) for the real
  service modules to import and run unmodified. These are test doubles only
  — nowhere near cryptographically equivalent to bcrypt/real JWT — never use
  them outside this harness.
- `fakedb.py` — a small in-memory async fake of the Motor collection methods
  the services actually call (`find_one`, `find_one_and_update`, `insert_one`,
  `find().sort().limit()`, `count_documents`, `update_one`, `update_many`).
- `run_tests.py` — imports `services/application_service.py`,
  `employee_auth_service.py`, `registration_service.py`, and
  `superadmin_service.py` straight from the real `backend/` source (no
  copies, no mocks of the logic itself) and drives them through the full
  registration → approve/reject → login-gating → registration-link →
  dashboard-stats → notification workflow, asserting on the results.

Run it with only the Python standard library, no installs:

```
python3 offline_dynamic_tests/run_tests.py
```

This is a supplement to, not a replacement for, the real test suite in
`tests/` (which uses `pytest` + `mongomock-motor` against real Pydantic
models and the actual FastAPI routes, and should be run with
`pip install -r requirements.txt && pytest` once you have network access).
