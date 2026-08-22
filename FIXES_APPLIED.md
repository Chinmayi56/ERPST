# Fixes Applied — StriveNest CORS / Login Investigation

## Audit result

A full audit of the frontend↔backend communication path (Vite config,
`.env` files, `axios.js`, `auth.js`, FastAPI `server.py`, `config.py`,
CORS middleware, and every route referenced by the SuperAdmin/Employee
login flows) found the CORS wiring itself **already correct and
consistent**:

- SuperAdmin (3000), SubAdmin (3001), Employee (3002) all point at the
  same `VITE_API_URL=http://localhost:8001/api`.
- `superadmin/src/api/axios.js` / `employee/src/api/axios.js` are the
  single Axios clients used by their respective `auth.js` files — no
  hardcoded or stale URLs anywhere in the repo.
- Backend `CORS_ORIGINS` in `backend/.env` already listed ports 3000,
  3001, 3002, parsed correctly into a real Python list by `config.py`.
- `CORSMiddleware` is registered on the only `FastAPI()` instance in the
  repo (`backend/server.py`), with explicit origins (not `*`).
- Frontend request paths (`/auth/superadmin/login`,
  `/auth/superadmin/send-otp`) match the backend routes in
  `backend/routes/auth.py` (`prefix="/api/auth"`) exactly.
- No `withCredentials` / `credentials: "include"` is used anywhere, so
  `allow_credentials=True` isn't even required, but doesn't conflict with
  anything since explicit origins are used (not `*`).

**No code bug was found that would, by itself, produce a real CORS
block.** Given that, the most likely real-world cause of the exact
symptom reported ("CORS error", 0.0 KB transferred) is that the browser
never got any HTTP response at all — which Chrome also reports as a
"CORS error" — because either (a) the backend process wasn't actually
running/reachable, most commonly because MongoDB wasn't running and the
backend hung on startup, or (b) the frontend dev server silently moved to
a different port than the one allow-listed in CORS_ORIGINS.

## Changes made to close both gaps

1. **`backend/database/mongodb.py`** — `connect_to_mongo()` now pings
   MongoDB with a 5s `serverSelectionTimeoutMS` and fails fast with a
   clear `[STARTUP ERROR]` message if MongoDB isn't reachable, instead of
   hanging indefinitely inside `ensure_indexes()`. Previously, if MongoDB
   wasn't running, the FastAPI app would never finish starting, so _every_
   request — including the browser's CORS preflight — got no response,
   which is exactly what shows up in DevTools as an unexplained "CORS
   error" with 0 bytes transferred.

2. **`superadmin/vite.config.js`, `subadmin/vite.config.js`,
   `employee/vite.config.js`** — added `strictPort: true`. Without this,
   if the configured port (3000/3001/3002) is already in use, Vite
   silently starts on a different port (e.g. 3003). That new origin is
   not in the backend's `CORS_ORIGINS` allow-list, which produces a real
   CORS block. `strictPort: true` makes Vite fail loudly instead, so a
   port conflict is obvious immediately rather than surfacing as a
   confusing CORS error in the browser.

3. **`backend/config.py`, `backend/.env`, `backend/.env.example`** — the
   default/allow-listed CORS origins now also include the `127.0.0.1`
   equivalents of ports 3000/3001/3002, in case the app is opened via
   `http://127.0.0.1:3000` instead of `http://localhost:3000` (browsers
   treat these as different origins).

No authentication logic, role/status validation, JWT handling, or
endpoint paths were changed — only the startup reliability and CORS
origin coverage described above.

## Important — please verify in your own environment

This environment has no network access and cannot install
`fastapi`/`uvicorn`/`motor` via pip, cannot run `npm install`, and has no
browser/DevTools available, so **the fix could not be exercised end-to-end
in a live browser here**. Please run the steps in `RUN_COMMANDS.txt` and
confirm:

- [ ] `http://localhost:8001/docs` opens
- [ ] `http://localhost:8001/api/health` → `"database":"connected"`
- [ ] SuperAdmin email login (`superadmin@strivenest.com` /
      `SuperAdmin@123`) returns `200`, not a CORS error
- [ ] SuperAdmin mobile OTP (`9876543210` / `123456`) returns `200`
- [ ] Employee login (`nithin@strivenest.com` / `Nithin@12`)
      returns `200`
- [ ] `npm run build` succeeds in `superadmin/` and `employee/`

If you still see a CORS error after following `RUN_COMMANDS.txt`, please
paste the **exact** console error text and the response Status column
from the Network tab — that will tell us definitively whether it's a true
CORS block or a connection failure being mislabeled as one.

---

# Employee Registration → Approval → Login Workflow

## Audit result

This workflow was already almost entirely implemented and wired end-to-end
before this change:

- **Registration** (`POST /api/employee-applications`, public) already
  creates a `PENDING` application with a securely hashed password
  (`utils/security.hash_password`, bcrypt) and rejects duplicate
  email/mobile — `services/application_service.py::create_application`.
- **Approval** (`POST /api/superadmin/applications/{id}/approve`, called by
  `superadmin/src/pages/EmployeeApplications.jsx` via the real backend, not
  a fake frontend status flip) already, atomically:
  - flips the application to `APPROVED` (optimistic-concurrency guarded
    against double-approve — a second click gets a safe 409, not a
    duplicate employee),
  - creates the `users` record with `status: ACTIVE`, `role: EMPLOYEE`, and
    the **same password hash the applicant set at registration** (never a
    generated one),
  - creates the linked `employees` record (`status: ACTIVE`,
    `source_application_id` → the application, `user_id` → the new user),
  - notifies the new employee and broadcasts to SuperAdmin.
- **Employee login** (`POST /api/auth/employee/login`) already enforces the
  full chain (password → user ACTIVE → employee ACTIVE → application
  APPROVED → JWT) and already returns the exact spec-required messages for
  pending/rejected/wrong-password instead of a generic error —
  `services/employee_auth_service.py`.
- **SuperAdmin visibility** of new applications was already real: the
  Dashboard's "Pending Applications" counter and "Recent Applications"
  panel are computed live from MongoDB (`services/superadmin_service.py`),
  not hardcoded.

## What was actually missing, and what I added

1. **No way for a not-yet-approved applicant to check their own status.**
   An applicant has no `users` record (and thus no JWT) until approval, so
   none of the existing authenticated endpoints could serve them. Added:
   - `GET /api/auth/employee/application-status?email=...` (public,
     unauthenticated) — `routes/auth.py` +
     `services/application_service.py::get_application_status_by_email`.
     Returns `{application_id, status, message}` and never exposes the
     password hash or other applicant PII. Placed under the existing
     `/api/auth/employee/...` namespace rather than inventing a new one.

2. **No automatic "approved" detection in the Employee portal UI.** The
   post-registration screen previously showed a static "submitted" message
   with no way to find out about approval short of manually retrying login.
   Updated `employee/src/pages/Register.jsx`:
   - After a successful submission, it now polls the new status endpoint
     every 12 seconds (within the requested 10–15s window).
   - `PENDING` → spinner + "Checking application status...".
   - `APPROVED` → "🎉 Your application has been approved! You can now
     login using your registered email and password." + a **Login Now**
     button that routes to `/login`. Polling stops.
   - `REJECTED` → rejection message from the backend. Polling stops.
   - The status shown is always whatever the backend/DB last returned —
     never set locally without a matching API call.
   - Added `.alert-success` styling and `getApplicationStatus()` to
     `employee/src/api/auth.js`.

3. **Fixed a pre-existing data-exposure bug found while in this code
   path**, unrelated to CORS but directly on the SuperAdmin "sees new
   applications" flow: `services/superadmin_service.py::get_dashboard_summary`
   returned each `recent_applications` document straight from MongoDB
   without stripping `password_hash` — every other place in the codebase
   (`list_applications`, `get_application`, `create_application`,
   `approve_application`, `reject_application`) already stripped it, this
   one didn't. Fixed to match.

No authentication logic, approval logic, JWT handling, RBAC, or existing
routes were changed or removed — this was additive (one new endpoint, one
new frontend polling flow) plus the one data-exposure fix above.

## Files changed (this task)

- `backend/routes/auth.py` — new `GET /api/auth/employee/application-status`
- `backend/services/application_service.py` — new
  `get_application_status_by_email`
- `backend/services/superadmin_service.py` — strip `password_hash` from
  `recent_applications`
- `employee/src/api/auth.js` — new `getApplicationStatus`
- `employee/src/pages/Register.jsx` — polling + approved/rejected UI states
- `employee/src/styles/index.css` — `.alert-success`

## APIs used (all pre-existing except the one addition above)

- `POST /api/employee-applications` — registration
- `GET /api/auth/employee/application-status` — **new**, status polling
- `GET /api/superadmin/applications` — SuperAdmin list/pending view
- `POST /api/superadmin/applications/{id}/approve` — approval
- `POST /api/superadmin/applications/{id}/reject` — rejection
- `POST /api/auth/employee/login` — employee login post-approval

## MongoDB collections/relationships used

`employee_applications.application_id` ← `employees.source_application_id`;
`employees.user_id` → `users.user_id`. All three stay in sync on approval
(`APPROVED` / `ACTIVE` / `ACTIVE` respectively) via one function,
`application_service.approve_application`, so there's no path that updates
one without the others.

## Important — could not be run live here

Same sandbox limitation as the CORS fix: no network for `pip`/`npm`
install, no MongoDB, no browser. I traced every step of the workflow
through the actual source and verified the pieces connect correctly (route
→ service → collection → response model, and frontend call → route path
→ response shape), and all edited Python files pass `py_compile`, but I
could not execute Test A–E from the request in a live browser. Please run
them via `RUN_COMMANDS.txt` and let me know the results — particularly
whether the polling screen flips to "approved" within ~12s of clicking
Approve in the SuperAdmin dashboard.

---

# Registration Forms — Copy Link Button

## What changed

Added a "📋 Copy Link" button next to the freshly-generated URL shown in the
"Link created:" banner on the SuperAdmin Registration Forms page.

- `superadmin/src/pages/RegistrationForms.jsx`:
  - New `handleCopyGeneratedLink()` — copies the exact `newlyCreatedUrl`
    string already returned by the backend (`POST
/superadmin/registration-links`), via `navigator.clipboard.writeText`
    with the same `execCommand` fallback already used elsewhere in this
    codebase (`EmployeePortalAccess.jsx`) for older/insecure-context
    browsers. No new token or URL is generated on the frontend.
  - Button label switches to "✓ Copied!" for 2 seconds after a successful
    copy, then reverts to "📋 Copy Link".
  - On clipboard failure, shows "Unable to copy link. Please copy it
    manually." inline instead of throwing.
  - Proper `<button type="button">` with `title`/`aria-label="Copy
registration link"` — the URL text itself is not clickable.
  - `bannerCopyState` resets to idle each time a new link is generated.
- `superadmin/src/styles/index.css`:
  - `.generated-link-row` — flex row holding the URL + button, wraps on
    narrow viewports.
  - Added a rule to the existing `@media (max-width: 560px)` block so the
    URL and button stack vertically (full-width button) on small screens.

## What was intentionally left untouched

- Token/link generation, hashing, storage, expiry, `used_count`, Link ID
  format — all in `backend/services/registration_service.py`, not modified.
- The existing table (Link ID / Note / Status / Created Date / Expiry Date
  / Used Count / Actions) and its Disable button — unchanged.
- The security note text and the fact that `list_registration_links()`
  never returns `url` for existing links (already correctly enforced
  backend-side) — unchanged. The per-row Copy/Email/WhatsApp buttons in the
  table were already gated behind `link.url` (which the list endpoint never
  populates) before this change, and still are.
- No backend files were touched for this request.

## Could not be run live here

Same sandbox constraint as before — no `npm install`, no browser. I
verified the JSX/CSS by hand (brace/paren balance checked) and by tracing
the exact data flow (`createRegistrationLink()` → `result.url` →
`newlyCreatedUrl` → the new button), but could not click through Generate →
Copy → paste in a real browser, or run `npm run build`. Please run through
`RUN_COMMANDS.txt`, generate a link, click Copy Link, and paste the result
somewhere to confirm it's the exact full URL.

---

# Idempotent Approve/Reject Messaging (this session)

## What was checked

Traced the full SuperAdmin → Employee workflow end-to-end again against the
30-point spec: registration, application creation, PENDING state, SuperAdmin
visibility, view, approve, reject, employee login gating (pending/rejected/
approved), status polling, registration link generation/copy/disable/expiry/
used-count, dashboard stats, notifications, and password hashing. All of it
was already correctly implemented (see the workflow write-up above from the
prior session) and traced cleanly through the actual source files again here.

## What was fixed

`backend/services/application_service.py` — approving or rejecting an
application that is already in a terminal state now returns a specific,
human-readable message instead of a generic one:

- Approve on an already-APPROVED application → `409` "Application is
  already approved." (previously "Only pending applications can be
  approved").
- Approve on a REJECTED application → `400` "This application has already
  been rejected and cannot be approved."
- Reject on an already-REJECTED application → `409` "Application is already
  rejected."
- Reject on an APPROVED application → `400` "This application has already
  been approved and cannot be rejected."
- The optimistic-concurrency race path (two simultaneous approve requests)
  now also returns "Application is already approved." instead of "Application
  was already reviewed" for the approve case.

No other logic changed. The double-approve guard itself (atomic
`find_one_and_update` keyed on the previous status, plus the
`source_application_id` uniqueness check before creating a user/employee)
was already correct and still prevents duplicate user/employee/application
records under concurrent requests.

## Verification performed in this sandbox

This sandbox has no network access (`pip install` / `npm install` /
MongoDB — all blocked, confirmed by direct test: `pip install fastapi`
and `npm install` both fail with `host_not_allowed` against PyPI and the
npm registry, and no local MongoDB binary is available). It was not
possible to actually start the backend, run `npm run build`, or click
through the workflow in a live browser, so those specific checks are not
independently verified end-to-end here — the same limitation the prior
session documented.

What _was_ done in this sandbox:

- Every backend `.py` file compiles cleanly (`python -m py_compile`).
- Every frontend `.js`/`.jsx` file across `superadmin/`, `employee/`, and
  `subadmin/` parses with zero syntax errors under the TypeScript compiler
  in JSX/allowJs mode.
- Full manual trace of every route → service → MongoDB collection → response
  shape, and every frontend API call → route path → response field, for all
  30 spec items.
- The project already ships 47 backend tests
  (`backend/tests/test_employee_registration_flow.py`,
  `test_employee_portal_flow.py`, `test_seed_verification.py`) written
  against `mongomock-motor`, covering this exact workflow including
  duplicate-approve and pending/rejected login. These could not be executed
  here (no `pytest`/`fastapi`/`mongomock` available offline) but are present
  in the delivered zip — run `pytest` after `pip install -r requirements.txt`
  to execute them.

## Update: real dynamic execution of the workflow (not just static trace)

Static tracing above was upgraded to actual runtime execution. Since `pip`
and `npm` cannot reach their registries here and no MongoDB binary is
available, a small offline harness (`backend/offline_dynamic_tests/`) was
built that stubs out only the _external libraries_ (`fastapi`'s exception/
status types, `passlib`, `python-jose`, `motor`, `pymongo` — none of them
reimplement any app logic) and swaps in an in-memory async fake of the
Mongo collection methods the code calls. The **real, unmodified**
`services/application_service.py`, `employee_auth_service.py`,
`registration_service.py`, and `superadmin_service.py` were then imported
and actually run through the full workflow.

Result: **37/37 checks passed**, including:

- registration creates a PENDING application; password hash never leaks
  through `get_application`/`create_application`
- approve synchronizes Application=APPROVED, User=ACTIVE role=EMPLOYEE,
  Employee=ACTIVE in the same DB
- double-approve is rejected (409, "Application is already approved.") and
  leaves exactly one user/employee record — no duplicates
- double-reject and approve-after-reject / reject-after-approve are all
  correctly rejected with the new friendly messages
- login with the exact registration password succeeds and returns a
  JWT-shaped token; wrong password is rejected
- a PENDING applicant's login attempt is blocked with a pending-specific
  message (not a generic invalid-credentials message); same for REJECTED
- the status-polling lookup reports PENDING then APPROVED (with a
  "you can now log in" message) after the SuperAdmin decision
- registration links: URL contains the token once, the list endpoint never
  re-exposes it, used_count increments in the DB on use, a disabled link
  is rejected, an expired link is rejected
- a duplicate email registration is rejected
- dashboard stats (`get_dashboard_summary`) match the DB exactly after the
  above operations
- the SuperAdmin receives one real notification per new application,
  each referencing the correct application id

An earlier version of this harness reported 2 unexpected failures around
notifications — that turned out to be a bug in the _test_, not the app: the
harness hadn't seeded a SuperAdmin user for `broadcast_to_role` to deliver
to. Once that was fixed the notification checks passed too, which is a good
sign the app code itself is correct rather than the test being too lenient.

This still isn't a substitute for running the real `pytest` suite (which
exercises the actual Pydantic models and FastAPI routes/dependency
injection, not just the service layer) or a real browser click-through —
please do both when you have network/MongoDB access, and treat items 17–19
in the PASS/FAIL report below as still needing that live confirmation.

---

# This session: demo Employee login fix + Employee Portal expansion

## 1. Demo Employee login — root cause and fix

**Root cause:** `nithin@strivenest.com` only ever exists in MongoDB
if someone manually runs `python seed_demo_employee.py` _after_
`seed_superadmin.py`, per `RUN_COMMANDS.txt`. That account is created
through the real application→approval flow, not a startup hook — so if
that one manual step was skipped (easy to miss when SuperAdmin login
already works, since `seed_superadmin.py` is a separate command), no
`users`/`employees`/`employee_applications` record exists for that email
at all. Tracing `employee_auth_service.login_employee`: when no `users`
record and no `employee_applications` record exist for the email, it falls
through every specific branch (pending/rejected) straight to the generic
`raise HTTPException(401, "Invalid email or password")` — exactly the
symptom reported. This was reproduced and confirmed with a dynamic test
(`offline_dynamic_tests/run_demo_login_fix_test.py`) that seeds only a
SuperAdmin (matching "SuperAdmin login already works") and shows the demo
Employee login failing with that exact message before the fix.

**Fix (smallest possible, no auth-architecture change):**

- `backend/seed_demo_employee.py` — split the existing seeding logic out of
  `seed()` into a new `seed_core(db)` that assumes an already-connected db
  (no behavior change, same idempotent/self-healing logic as before).
  `seed()` (the CLI entrypoint used by `python seed_demo_employee.py`) is
  unchanged in behavior, just now delegates to `seed_core`.
- `backend/server.py` — the startup `lifespan` now calls
  `seed_demo_employee.seed_core(get_db())` once, right after
  `connect_to_mongo()`, wrapped in try/except so a seeding failure can
  never block the API from starting. This guarantees the demo Employee
  account exists on every boot, the same way it was always _supposed_ to
  after following `RUN_COMMANDS.txt` — it doesn't change what the account
  is, how it's created, or how login works. SuperAdmin seeding was
  deliberately left untouched (still manual, still `seed_superadmin.py`)
  since SuperAdmin login was already reported working and out of scope.
- No change to `employee_auth_service.py`, `application_service.py`,
  JWT handling, or password hashing — none of that was broken.

Verified with `offline_dynamic_tests/run_demo_login_fix_test.py`: 10/10
checks, including reproducing the bug before the fix, confirming the fix,
confirming idempotency across repeated (simulated) restarts with no
duplicate records, and confirming self-healing repairs a corrupted
password hash on the next startup.

## 2 & 3. Employee Portal expansion + Dashboard upgrade

Added, employee-frontend only, no backend routes added:

- `src/pages/MyTasks.jsx`, `MyProjects.jsx`, `MyClients.jsx`,
  `Attendance.jsx`, `LeaveManagement.jsx`, `Documents.jsx`, `Payslips.jsx`
- `src/data/demoPortalData.js` — single shared source of demo data for the
  above (and for the Dashboard summary cards), so numbers stay consistent
  between the Dashboard and each module's own page. Clearly commented as
  placeholder data pending real backend endpoints; each page footer says
  "Preview data — ... once the backend API is available."
- `App.jsx` — added routes for the 7 new pages (same `Protected` +
  `DashboardLayout` wrapper pattern as existing routes).
- `layouts/Sidebar.jsx` — added the 7 new nav items in the requested order.
- `components/StatusBadge.jsx` — additively extended the status→color map
  with new keys used by the new modules (`IN_PROGRESS`, `DONE`,
  `COMPLETED`, `PRESENT`, `ABSENT`, `LATE`, `LEAVE`, `PAID`). Every existing
  key/behavior is unchanged.
- `pages/Dashboard.jsx` — rewritten to add: My Projects / My Clients /
  My Tasks / Attendance summary stat cards, Recent Tasks / Recent Projects
  panels (from the new demo data), a Recent Notifications panel (from the
  **real** `/api/employee/notifications` endpoint, same one the
  Notifications page already uses), and a Quick Actions panel linking to
  the new pages. The existing "Your Details" section (real backend data
  from `/api/employee/dashboard`) is preserved, just moved below the new
  panels.
- No new CSS was needed — `.stat-grid`/`.stat-card`/`.dashboard-panels`/
  `.panel`/`.simple-list` classes already existed in
  `employee/src/styles/index.css` (mirroring the SuperAdmin dashboard) but
  were unused by the Employee portal until now.

`superadmin/` and `subadmin/` are untouched (verified with a direct
recursive diff against the previously delivered zip: zero differences).
`backend/routes/*.py`, `services/application_service.py`,
`services/employee_auth_service.py`, `services/registration_service.py`
etc. are untouched — the only backend files touched are
`seed_demo_employee.py` and `server.py`, both described above.

---

# This session: full backend + ERP audit (no code regressions found)

## What was done

A sandboxed environment here has no network access (pip/npm registries
blocked, confirmed by direct test) and no local MongoDB, so the backend
could not be started live to reproduce "fails when running `python -m
uvicorn server:app ...`" directly. In place of that, every backend file was
audited exhaustively and mechanically, not just read:

- `python -m py_compile` on every backend `.py` file (excluding
  `tests/`/`offline_dynamic_tests/`) — 0 syntax errors.
- A Python `ast.parse` pass over the same files — 0 syntax errors,
  confirming the `py_compile` result independently.
- Manually traced every `routes/*.py` → `services/*.py` → MongoDB
  collection → response model, and cross-checked every router's
  `prefix` against every other router's for path collisions — all 12
  router prefixes are distinct; no duplicate/conflicting routes.
- Verified `server.py`'s router imports and `app.include_router(...)`
  calls against the actual files in `routes/` — all present, no
  missing/renamed imports.
- Verified `database/mongodb.py`'s startup sequence, index creation, and
  the CORS/`.env` wiring described in the "CORS / Login Investigation"
  section above are all still intact and correct.
- Checked the exact PyMongo/Motor version pins in `requirements.txt`
  against Motor's documented compatibility range (Motor 3.5.1 requires
  `4.5 <= PyMongo < 4.9`) — `pymongo==4.8.0` is inside that range, so
  that pairing is fine, not a bug.
- Checked every frontend (`superadmin/`, `employee/`, `subadmin/`) for
  broken relative imports (0 found across 152 import statements) and
  parsed every `.js`/`.jsx` file with the TypeScript compiler in
  JSX/allowJs mode (0 syntax errors across all three apps).
- Confirmed the SuperAdmin ERP modules requested (Clients, Projects,
  Leave, Attendance, Services, Bookings, Documents) already exist,
  fully wired end-to-end: `backend/routes/erp.py` (generic, real
  MongoDB-backed CRUD/search/status/pagination for all 7 modules) ↔
  `superadmin/src/api/erp.js` ↔ `superadmin/src/pages/ERPManagement.jsx`
  ↔ `App.jsx` routes (`/clients`, `/projects`, `/leave-requests`,
  `/attendance`, `/services`, `/services-bookings`, `/documents`) — all
  backed by real MongoDB queries, no mock/hardcoded data. The Dashboard
  (`services/superadmin_service.py::get_dashboard_summary`) already
  aggregates real counts from `clients`, `projects`, `leaves`,
  `attendance`, `services`, `bookings`, and `documents`, plus recent
  applications/notifications/activity — not a placeholder.

## What was actually fixed

`backend/requirements.txt` — `bcrypt` pin lowered from `4.2.0` to
`4.0.1`. `passlib==1.7.4`'s bcrypt backend reads
`bcrypt.__about__.__version__` at every hash/verify call; bcrypt >=4.1
removed that attribute, so every login and every application submission
throws a `(trapped) error reading bcrypt version` `AttributeError` to
the console (this is a widely-reported passlib/bcrypt interop issue —
it does not break hashing/verification itself, but it is exactly the
kind of console noise that gets mistaken for "the backend is failing").
`4.0.1` is the last bcrypt release before that attribute was removed,
so it works cleanly with `passlib==1.7.4` with no warning at all. No
hashing/verification code in `utils/security.py` changed.

## What was intentionally NOT changed

No route, service, model, auth/JWT/RBAC logic, or frontend component was
modified. The employee registration → SuperAdmin approval → employee
login pipeline, all SuperAdmin ERP CRUD modules, and the dashboard are
unchanged — they were already real and already wired to MongoDB.

## Still needs live verification (could not be run in this sandbox)

- `pip install -r requirements.txt` then `python -m uvicorn server:app
--host 0.0.0.0 --port 8001 --reload` with a running local MongoDB —
  confirm `http://localhost:8001/docs` loads and
  `http://localhost:8001/api/health` reports `"database":"connected"`.
- `npm install && npm run build` in `superadmin/`, `employee/`, and
  `subadmin/` — confirm production builds succeed (only syntax-level
  parsing was verified here, not the full Vite/Rollup build pipeline,
  since `npm install` requires network access this sandbox does not
  have).
- End-to-end click-through of SuperAdmin login → each ERP module
  (Clients/Projects/Leave/Attendance/Services/Bookings/Documents) →
  create/edit/delete/filter/paginate → Dashboard reflecting the change.

---

# This session: fixed `project_id: null` DuplicateKeyError on startup

## Root cause

`database/mongodb.py`'s `ensure_indexes()` creates a **unique** index on
`projects.project_id` (and the equivalent business-ID field on every other
ERP module collection). MongoDB treats any document that is _missing_ the
indexed field, or has it explicitly set to `null`, as having the value
`null` for indexing purposes. If two or more `projects` documents in the
database had no `project_id` (e.g. rows present before this field existed,
or inserted by hand/import), the unique index creation fails immediately
because Mongo sees multiple "duplicate" nulls — exactly the reported:

```
pymongo.errors.DuplicateKeyError: E11000 duplicate key error collection:
strivenest.projects index: project_id_1 dup key: { project_id: null }
```

New projects created through the API were never affected —
`routes/erp.py`'s `create_record()` already always assigns a `project_id`
via `data.setdefault(...)` after stripping out any `None`/`""` value the
client sends — so this was purely a pre-existing-data problem, not a code
path that generates nulls going forward.

## Fix

`backend/database/mongodb.py`:

1. Added `backfill_missing_erp_ids()` — for each ERP module collection
   (`clients`, `projects`, `leaves`, `attendance`, `services`, `bookings`,
   `documents`), finds every document whose unique-indexed ID field is
   missing or `null` and assigns it a fresh, collision-checked ID in the
   exact same `"<PREFIX>-<8 hex chars>"` format `routes/erp.py` already
   generates for new records. No document is deleted, and no field other
   than the missing ID is touched — all existing project/client/etc. data
   is preserved exactly as-is.
2. `connect_to_mongo()` now calls `backfill_missing_erp_ids()` **before**
   `ensure_indexes()`, so every document has a real ID by the time the
   unique index is created.
3. `ensure_indexes()`'s ERP-module loop now also catches `DuplicateKeyError`
   around each unique `create_index()` call as a defense-in-depth retry
   (re-runs the backfill once and tries again) rather than letting a
   startup crash silently, in case a document appears mid-migration.

**Idempotent and safe to run on every startup**: the backfill's query is
`{field: null} OR {field: {$exists: false}}`, so once every document has a
real ID it matches zero documents on every subsequent run — it never
regenerates or overwrites an ID that already exists, and `create_index()`
is itself a no-op if the index already exists with the same spec. No
duplicate indexes are created.

No route, service, model, or frontend code changed. No project/client/
leave/attendance/service/booking/document data was deleted.

## Verification performed in this sandbox

Same sandbox constraint as prior sessions: no network access, so
`pymongo`/`motor` cannot be installed and the app cannot be started against
a real MongoDB here. Instead, `offline_dynamic_tests/run_project_id_migration_test.py`
was added: it stubs out only `motor`/`pymongo`'s import surface, builds an
in-memory fake Mongo collection that faithfully reproduces MongoDB's
duplicate-null unique-index behavior, imports the real unmodified
`database/mongodb.py`, and:

- reproduces the exact reported `DuplicateKeyError` against dirty data
  (documents missing `project_id`, including one explicit `null`) —
  confirmed it fails the same way before the fix,
- runs `backfill_missing_erp_ids()` and confirms every project ends up with
  a unique, correctly-formatted ID, no project is deleted, and unrelated
  fields (`name`, `status`) are untouched,
- confirms the previously-failing unique index now creates successfully,
- confirms re-running the migration is a true no-op (idempotency),
- runs the **full** `ensure_indexes()` startup sequence against dirty data
  across every ERP module (not just projects) and confirms it completes
  without raising,
- confirms a newly created project (via the same logic
  `routes/erp.py::create_record()` uses) can never end up with
  `project_id: null`, even if the client explicitly sends one.

Result: **13/13 checks passed**. The pre-existing offline test suites
(`run_tests.py` — 37/37, `run_demo_login_fix_test.py` — 10/10) were also
re-run to confirm zero regressions from this change (60/60 total). One
supporting fix was needed for the pre-existing offline test harness itself:
`offline_dynamic_tests/stubs/pymongo/errors.py` was missing a
`DuplicateKeyError` stub, which the real `pymongo.errors` module has always
provided — added it so the harness's stub matches the real module.

## Still needs live verification (could not be run in this sandbox)

`python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload` against
a real MongoDB containing the actual dirty `projects` data — confirm the
startup log shows `[startup] Backfilled N existing 'projects' document(s)...`
followed by `Application startup complete`, that `http://localhost:8001/docs`
opens, and that restarting the server a second time produces no further
backfill log lines (proving idempotency on real data).
