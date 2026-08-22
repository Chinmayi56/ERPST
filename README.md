# Strivenest Technologies — SuperAdmin Portal

## 1. Overview

This is the **SuperAdmin portal** for the Strivenest Technologies platform:
authentication, dashboard, employee application review, employee management,
registration link generation, notifications, reports, profile and settings —
all backed by a real FastAPI + MongoDB backend. There is no mock or hardcoded
business data; every number and record shown in the UI comes from MongoDB.

This is phase one of a three-frontend platform. SubAdmin and Employee portals
are **not implemented** in this phase — see [Future Portal Architecture](#12-future-portal-architecture).

## 2. Architecture

```
SuperAdmin React (Vite) → Axios → ONE FastAPI backend → Motor → ONE MongoDB
```

- **One** FastAPI backend serves all current and future frontends.
- **One** MongoDB database (`strivenest`) holds all collections.
- **One** independent React app for SuperAdmin, in its own folder.
- Role-based access control (`role: SUPERADMIN`) is enforced **server-side**
  on every protected endpoint — not just in the frontend.

## 3. Technology Stack

**Backend:** Python, FastAPI, Motor (async MongoDB driver), MongoDB, Pydantic,
JWT (python-jose), bcrypt/passlib, Uvicorn

**Frontend:** React 18, Vite, Axios, React Router, plain CSS (no UI framework)

**Database:** MongoDB

## 4. Folder Structure

```
STRIVENEST-TECHNOLOGIES/
├── backend/
│   ├── server.py                 # FastAPI app entry point
│   ├── config.py                 # Environment-driven settings
│   ├── routes/                   # auth, superadmin, applications, employees,
│   │                              #   registration_links, notifications, health
│   ├── services/                 # business logic per domain
│   ├── models/                   # Pydantic request/response schemas
│   ├── utils/                    # security, jwt, validation, auth dependencies
│   ├── database/mongodb.py       # Motor connection + indexes
│   ├── requirements.txt
│   ├── .env.example
│   └── seed_superadmin.py
├── superadmin/
│   ├── src/
│   │   ├── api/                  # Axios wrappers per domain
│   │   ├── components/           # Loader, EmptyState, StatusBadge, ConfirmDialog...
│   │   ├── context/AuthContext.jsx
│   │   ├── layouts/              # Sidebar, Header, DashboardLayout
│   │   ├── pages/                # Login, Dashboard, Employees, Applications, ...
│   │   └── styles/index.css
│   ├── public/logo.png
│   ├── package.json
│   └── .env.example
├── subadmin/                     # future phase, placeholder only
├── employee/                     # future phase, placeholder only
├── README.md
└── .gitignore
```

## 5. MongoDB Setup

**Local MongoDB (default):**
```
mongodb://localhost:27017
```
Install MongoDB Community Server and make sure the `mongod` service is running.

**MongoDB Atlas (cloud):**
Set `MONGO_URL` in `backend/.env` to your Atlas connection string, e.g.:
```
MONGO_URL=mongodb+srv://<user>:<password>@<cluster>.mongodb.net
```

Database name: `strivenest` (set via `DB_NAME`).

Collections used: `users`, `employee_applications`, `employees`,
`registration_links`, `notifications`, `audit_logs`. All are created
automatically on first write; indexes are created automatically on backend
startup.

## 6. Python Setup

Python 3.10+ is recommended.

## 7. Backend Installation (Windows / VS Code)

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
python seed_superadmin.py
python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

macOS/Linux equivalent:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python seed_superadmin.py
python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

## 8. SuperAdmin Installation

```powershell
cd superadmin
npm install
copy .env.example .env
npm run dev
```

The app runs at `http://localhost:3000` by default (configured in `vite.config.js`).

## 9. Environment Variables

**backend/.env**
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=strivenest
JWT_SECRET=change_this_secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:3002
EMPLOYEE_PORTAL_URL=http://localhost:3002
SEED_SUPERADMIN_EMAIL=superadmin@strivenest.com
SEED_SUPERADMIN_PASSWORD=SuperAdmin@123
SEED_SUPERADMIN_MOBILE=9876543210
SEED_SUPERADMIN_NAME=Super Admin
DEMO_OTP=123456
```

**superadmin/.env**
```
VITE_API_URL=http://localhost:8001/api
```

Never commit real secrets — only `.env.example` files are checked in.

## 10. Seed Command

```bash
python seed_superadmin.py
```

Idempotent: safe to run multiple times. Creates the demo SuperAdmin account
only if it doesn't already exist. Passwords are bcrypt-hashed before storage;
the plain password is never written to MongoDB or logged. No other business
data (employees, applications, notifications, etc.) is ever seeded.

## 11. Demo Credentials

```
Email:    superadmin@strivenest.com
Password: SuperAdmin@123
Mobile:   9876543210
Demo OTP: 123456
```

OTP login is **demo only** in this phase — no real SMS provider is
integrated. The architecture (separate send-otp / verify-otp endpoints) is
ready for a real provider to be plugged in later without changing the
frontend contract.

## 12. Portal Architecture

The platform is four independent apps sharing **one** backend and **one**
MongoDB database — see section 23 for the full folder layout:

- `superadmin/` — implemented (SuperAdmin role). Runs on `:3000`.
- `employee/` — implemented (public registration form + gated `EMPLOYEE`
  role login/portal — see sections 20–22). Runs on `:3002`.
- `subadmin/` — **scaffolded, not yet implemented**. A real, independently
  runnable Vite + React app on `:3001` that currently shows a placeholder
  page, since no `SUBADMIN` role or routes exist on the backend yet. When
  built out, it will reuse the same JWT auth pattern; a new role-gate
  dependency can be added in `backend/utils/dependencies.py` alongside
  `require_superadmin` / `require_employee` without a new backend or
  database. See `subadmin/README.md`.

## 13. Run Commands (Quick Reference)

**Backend** (`http://localhost:8001`):
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**SuperAdmin** (`http://localhost:3000`):
```bash
cd superadmin
npm install
npm run dev
```

**SubAdmin** (`http://localhost:3001`):
```bash
cd subadmin
npm install
npm run dev
```

**Employee Portal** (`http://localhost:3002`):
```bash
cd employee
npm install
npm run dev
```

## 14. Swagger URL

```
http://localhost:8001/docs
```

## 15. SuperAdmin Login URL

```
http://localhost:3000/login
```

## 16. API Architecture

All endpoints are prefixed `/api`. Every SuperAdmin endpoint requires a
`Authorization: Bearer <token>` header and validates both the JWT signature
and the `SUPERADMIN` role **on the server** — the frontend route guard is a
UX convenience only, not the source of truth.

```
AUTH
  POST   /api/auth/superadmin/login
  POST   /api/auth/superadmin/send-otp
  POST   /api/auth/superadmin/verify-otp
  POST   /api/auth/logout
  GET    /api/auth/me

DASHBOARD
  GET    /api/superadmin/dashboard

APPLICATIONS
  GET    /api/superadmin/applications
  GET    /api/superadmin/applications/{application_id}
  POST   /api/superadmin/applications/{application_id}/approve
  POST   /api/superadmin/applications/{application_id}/reject

EMPLOYEES
  GET    /api/superadmin/employees
  GET    /api/superadmin/employees/{employee_id}
  PATCH  /api/superadmin/employees/{employee_id}
  POST   /api/superadmin/employees/{employee_id}/disable

REGISTRATION LINKS
  POST   /api/superadmin/registration-links
  GET    /api/superadmin/registration-links
  POST   /api/superadmin/registration-links/{link_id}/disable

NOTIFICATIONS
  GET    /api/superadmin/notifications
  PATCH  /api/superadmin/notifications/{notification_id}/read

HEALTH
  GET    /api/health
```

Approving an application also creates a new `employees` record, a
notification, and an audit log entry, all in the same operation. Rejecting
requires a reason and is also logged and notified.

## 17. Troubleshooting

- **`ModuleNotFoundError` on backend start** — make sure the virtual
  environment is activated and `pip install -r requirements.txt` completed
  without errors.
- **Backend can't connect to MongoDB** — confirm `mongod` is running locally,
  or that your Atlas `MONGO_URL` and IP allowlist are correct. `GET
  /api/health` reports `"database": "connected"` or `"disconnected"`.
- **CORS errors in the browser console** — make sure the frontend origin
  (e.g. `http://localhost:3000`) is included in `CORS_ORIGINS` in
  `backend/.env`.
- **401 Unauthorized on every request after login** — check that
  `VITE_API_URL` in `superadmin/.env` points at the running backend, and
  that the JWT hasn't expired (`JWT_EXPIRE_MINUTES`).
- **`seed_superadmin.py` says the account already exists** — this is
  expected on repeat runs; it's idempotent by design. Delete the user
  document from the `users` collection if you need to reset the demo
  account.
- **Swagger shows no routes** — confirm `server.py` started without import
  errors; check the terminal output for a traceback.
- **PowerShell blocks `Activate.ps1`** — run PowerShell as Administrator once
  and execute `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then
  retry.

## 18. Testing Notes

The backend was syntax-verified (`python -m py_compile` across all modules),
imported and served with FastAPI's TestClient against an in-memory MongoDB
double, and exercised by the automated suite in section 20.5 (17/17 passing)
in this environment. Both frontends were built with `npm run build` and
compiled without errors. This sandbox has no live MongoDB server or browser,
so the manual checklist below should still be run once on your machine
against a real `mongod` before going to production:

1. FastAPI starts without errors.
2. MongoDB connects (`GET /api/health` returns `"database": "connected"`).
3. Swagger opens at `/docs`.
4. `seed_superadmin.py` creates the account, and is a no-op on a second run.
5. Email/password login succeeds with the demo credentials.
6. Wrong password is rejected with a 401.
7. Mobile OTP: send-otp then verify-otp with `123456` succeeds.
8. Wrong OTP is rejected.
9. Protected endpoints reject requests with no/invalid JWT (401).
10. Dashboard shows zeros on an empty database, and updates as data changes.
11. Approving a pending application creates an employee, a notification, and
    an audit log entry.
12. Rejecting without a reason is blocked by both frontend and backend
    validation.
13. Registration link Copy/Email/WhatsApp actions work in the browser.
14. Logout clears the session and protected routes redirect to `/login`.

## 19. ZIP Packaging

The project excludes `node_modules/`, `venv/`, `__pycache__/`, `.git/` and
build output directories (see `.gitignore`). To package for distribution:

```bash
cd ..
zip -r strivenest-superadmin.zip STRIVENEST-TECHNOLOGIES \
  -x "*/node_modules/*" "*/venv/*" "*/__pycache__/*" "*/.git/*" "*/dist/*"
```

Extract and open the `STRIVENEST-TECHNOLOGIES/` folder directly in VS Code.

## 20. Employee Registration → Approval Feature

This phase adds the full loop: **Employee Registration → SuperAdmin
Notification → SuperAdmin Review → Approve/Reject → Employee Record**, plus a
gated Employee login.

### 20.1 New Employee portal (`employee/`)

A real Vite + React app (same stack as `superadmin/`) with:

- `/register` — the public Employee Registration Form (Personal, Contact,
  Professional info + Resume/ID proof upload). On submit, shows the
  Application ID and PENDING status.
- `/login` — Employee login, only usable after SuperAdmin approval.

Run it like the SuperAdmin app:

```bash
cd employee
npm install
cp .env.example .env
npm run dev   # http://localhost:3002
```

### 20.2 New/changed backend API

```
EMPLOYEE REGISTRATION (public)
  POST   /api/employee-applications
  GET    /api/employee-applications                (SuperAdmin)
  GET    /api/employee-applications/{id}             (SuperAdmin)
  POST   /api/employee-applications/{id}/approve     (SuperAdmin)
  POST   /api/employee-applications/{id}/reject      (SuperAdmin)

EMPLOYEE MANAGEMENT (spec-shaped alias of /api/superadmin/employees)
  GET    /api/employees
  GET    /api/employees/{id}
  PUT    /api/employees/{id}
  PATCH  /api/employees/{id}/status

EMPLOYEE AUTH
  POST   /api/auth/employee/login

UPLOADS (public, used by the registration form)
  POST   /api/uploads
```

The original `/api/superadmin/applications` and `/api/superadmin/employees`
routes are untouched and still work — both route sets share one service
layer, so nothing already shipped was broken.

### 20.3 How approval works

`POST /api/employee-applications/{id}/approve`:

1. Confirms the application is still PENDING (atomic — a concurrent
   duplicate approve/reject is rejected with 409).
2. Generates a sequential `employee_id` (e.g. `EMP000124`).
3. Creates the `employees` record, linked back via `source_application_id`.
4. Creates a gated login account in `users` (`role: EMPLOYEE`) with a random
   temporary password — **only the bcrypt hash is stored**. The plain
   temporary password is returned once in the API response
   (`temporary_password`, `employee_login_email`) for the SuperAdmin to share
   with the new hire; the SuperAdmin UI displays it once on the Application
   Detail page after approving.
5. Broadcasts an `APPLICATION_APPROVED` notification to every SuperAdmin and
   writes an audit log entry.

### 20.4 Security rule: no login before approval

Enforced **server-side**, not just hidden in the UI:

- No `users` record of role `EMPLOYEE` exists until step 4 above runs, so a
  pending/rejected applicant has no credentials to authenticate with at all.
- `POST /api/auth/employee/login` additionally re-checks that the linked
  `employees.status` is `ACTIVE` and the source application is `APPROVED`
  before issuing a JWT — defense in depth even if a record is ever edited
  directly.
- Deactivating an employee (`PATCH /api/employees/{id}/status`) immediately
  flips their linked `users.status`, blocking further logins.

### 20.5 Tests

`backend/tests/test_employee_registration_flow.py` — 17 tests, run against an
in-memory MongoDB double (`mongomock-motor`), no real MongoDB server needed:

```bash
cd backend
pip install -r requirements.txt
pytest -q
```

Covers: registration creates a PENDING application; duplicate email/mobile
rejected; invalid mobile format rejected (422); submission notifies every
SuperAdmin; non-SuperAdmin cannot list/approve; SuperAdmin can view, approve,
and reject; rejection requires and stores a reason; approval creates exactly
one employee and cannot create duplicates on retry; the original application
is preserved after rejection; the approved employee appears in Employee
Management; an applicant cannot log in before approval (401); an approved
employee can log in with the issued temporary password; and disabling an
employee blocks their login (403).

All 17 tests were run in this environment and pass. Both `employee/` and
`superadmin/` were also built with `npm run build` in this environment and
compiled without errors.

## 21. Employee Approval → Employee Login → Employee Portal → SuperAdmin Sync

This phase wires up the gated Employee login into a real, working Employee
Portal, and makes sure everything an approved employee does stays in sync
with what SuperAdmin sees.

### 21.1 New Employee Portal pages (`employee/`)

- `/login` — now redirects to `/dashboard` on success and keeps the employee
  signed in via a `AuthProvider`/JWT stored in `localStorage`
  (`strivenest_employee_token`), matching the SuperAdmin app's pattern.
- `/dashboard` — Employee ID, Name, Email, Mobile, Department, Designation,
  Joining Date, Status, Last Login — all loaded live from MongoDB, never
  hardcoded.
- `/profile` — Personal details, Professional details, Application ID,
  Submitted date, Approval date, Approved by (resolved to the SuperAdmin's
  name), current status, last login.
- `/notifications` — the employee's own notification inbox: list, mark one
  read, mark all read.
- All three are wrapped in a `ProtectedRoute` (redirects to `/login` if not
  authenticated) and a shared sidebar/header layout, mirroring the
  SuperAdmin app's `DashboardLayout`.

Run it the same way as before:

```bash
cd employee
npm install
cp .env.example .env
npm run dev   # http://localhost:3002
```

### 21.2 New/changed backend API

```
EMPLOYEE PORTAL (EMPLOYEE role only, JWT required)
  GET    /api/employee/dashboard
  GET    /api/employee/profile
  GET    /api/employee/notifications
  PATCH  /api/employee/notifications/{id}/read
  PATCH  /api/employee/notifications/read-all
```

Every route above is scoped to the caller's own `user_id` — an employee can
never fetch another employee's dashboard, profile, or notifications, and
none of them accept a SuperAdmin token (403).

The existing `POST /api/auth/employee/login` now:

- Returns a **specific message** for each rejection reason instead of a
  generic error, matching the spec exactly:
  - Pending: *"Your employee application is still pending SuperAdmin
    approval."*
  - Rejected: *"Your employee application was rejected. Please contact the
    administrator."*
  - Inactive account: *"Your employee account is currently inactive."*
  - Wrong password / unknown email: *"Invalid email or password"*
- Records `last_login` on the employee record on every successful login.
- Issues a JWT that now also carries `employee_id` (in addition to
  `user_id`, `role`, `email`, `exp`), so protected employee routes never
  need an extra lookup just to know whose token it is.

### 21.3 SuperAdmin ↔ Employee sync

No new SuperAdmin routes were needed — `GET /api/superadmin/employees` and
`GET /api/superadmin/employees/{id}` already return the full employee
record (Employee ID, Application ID via `source_application_id`, Name,
Email, Mobile, Department, Designation, Joining Date, Status, Approval
date, Approved by). This phase adds one field to that same record:
**`last_login`**, populated automatically the moment the employee logs in,
so SuperAdmin can see it without any extra plumbing.

Notifications now flow both ways:

- On **approval**, the new employee's inbox is seeded with an
  `APPLICATION_SUBMITTED` and an `APPLICATION_APPROVED` entry (their inbox
  only starts existing once their account does, so this gives them a
  complete history on first login).
- On **activate/deactivate** (`PATCH /api/employees/{id}/status` or
  `POST /api/superadmin/employees/{id}/disable`), the employee gets an
  `ACCOUNT_ACTIVATED` / `ACCOUNT_DEACTIVATED` notification, and their linked
  login account is immediately flipped so the next API call (or login
  attempt) is blocked with 403 — no need to wait for the JWT to expire.

### 21.4 Security

- `require_employee` (new, in `utils/dependencies.py`) enforces the EMPLOYEE
  role on every Employee Portal route, on top of the existing JWT
  validation and live `users.status == ACTIVE` re-check that already ran on
  every request.
- Employee routes and SuperAdmin routes are fully separate route sets
  (`/api/employee/...` vs `/api/superadmin/...`) with separate role gates —
  an employee token gets 403 on every SuperAdmin/approval/rejection
  endpoint, and a SuperAdmin token gets 403 on Employee Portal endpoints
  (it isn't role `EMPLOYEE`).
- Passwords are never stored or logged in plain text (bcrypt via `passlib`,
  unchanged from the existing implementation).

### 21.5 Tests

`backend/tests/test_employee_portal_flow.py` — 16 new tests, run against the
same in-memory MongoDB double as the rest of the suite:

```bash
cd backend
pip install -r requirements.txt
pytest -q
```

Covers the full spec end-to-end flow (registration → pending → login
rejected → approve → employee created → account active → login succeeds →
JWT issued → dashboard loads → profile loads → SuperAdmin sees the same
employee → logout works) plus every required negative case: wrong password,
rejected application, pending application, inactive/deactivated account,
garbage/invalid token, an employee reading another employee's profile, and
an employee hitting SuperAdmin-only APIs.

**33 tests total pass** (17 existing + 16 new). Both `employee/` and
`superadmin/` were rebuilt with `npm run build` in this environment after
these changes and compiled without errors — nothing existing was broken.

## 22. Employee Portal Access (SuperAdmin sharing)

The last piece of the spec loop: after an application is approved and the
employee account exists, SuperAdmin needs a way to actually hand the
employee their portal link. This phase adds that sharing UI — **no backend
change was needed**, since the Employee Portal was already a fully separate
app (`employee/`) with its own `/login` route and server-enforced gating
(see sections 20–21).

### 22.1 What was added

- **`superadmin/src/components/EmployeePortalAccess.jsx`** — a panel titled
  "Employee Portal Access" with three actions:
  - **Copy Login Link** — copies the Employee Portal's `/login` URL to the
    clipboard (`navigator.clipboard`, with an `execCommand` fallback for
    non-secure contexts).
  - **Share on WhatsApp** — opens `https://wa.me/...` pre-filled with a
    message containing the login link; pre-fills the recipient's number
    when the employee's stored mobile is a plain 10-digit number (assumes
    `+91`), otherwise opens a generic share dialog.
  - **Share via Email** — opens a `mailto:` link addressed to the employee
    with a pre-filled subject and body containing the login link.
- **`superadmin/src/utils/employeePortal.js`** — builds the login link from
  `VITE_EMPLOYEE_PORTAL_URL` and the WhatsApp/email share content. Nothing
  is hardcoded to `localhost`.
- The panel is rendered on the **Employee Detail** page
  (`/employees/:employeeId#portal-access`), reachable from:
  - The **Employees** list — each row now has a "Portal Access" action
    alongside "View" / "Disable".
  - The **Application Detail** page's approval success banner — after
    approving, SuperAdmin gets a direct "Open Employee Portal Access →"
    link for the employee just created.
- `superadmin/.env.example` gained `VITE_EMPLOYEE_PORTAL_URL` (defaults to
  `http://localhost:3002`, matching the `employee/` app's dev port).

### 22.2 Why the Employee Login stays out of the SuperAdmin app

The panel only ever links to the Employee Portal's own `/login` page — it
never renders a login form inside `superadmin/`. The employee still has to
open the link themselves and sign in with their own email/password; the
link carries no token and grants no access by itself. This matches the
spec's requirement that the Employee Login remains a separate portal.

### 22.3 Testing

This is a frontend-only, additive change — no route, model, or service in
`backend/` was touched, so the existing 33 backend tests are unaffected by
it and continue to be the source of truth for the login-gating rules
(pending/rejected/inactive blocking, own-data-only access, etc. — see
sections 20.5 and 21.5). If you're running this in your own environment:

```bash
cd backend
pip install -r requirements.txt
pytest -q                 # should still show 33 passed

cd ../superadmin
npm install
cp .env.example .env      # set VITE_EMPLOYEE_PORTAL_URL if not on :3002
npm run build              # verify the new panel compiles cleanly

cd ../employee
npm install
cp .env.example .env
npm run build
```

Manual check for the new UI:

1. Log in to SuperAdmin, approve a pending application.
2. From the success banner, click "Open Employee Portal Access →" (or go
   to Employees → a given employee → "Portal Access").
3. Click **Copy Login Link**, paste it somewhere — it should be
   `<VITE_EMPLOYEE_PORTAL_URL>/login`, e.g. `http://localhost:3002/login`.
4. Click **Share on WhatsApp** — a WhatsApp Web/app share dialog should
   open with the message pre-filled.
5. Click **Share via Email** — your default mail client should open with
   the employee's address, a subject, and the login link in the body.
6. Open the copied link in a new tab — it should load the separate
   Employee Portal login page (not anything inside the SuperAdmin app).

## 23. Folder Structure & SubAdmin Scaffold

The project was reorganized into a clean, exact top-level layout:

```
STRIVENEST-TECHNOLOGIES/
│
├── backend/       # FastAPI + MongoDB, port 8001
├── superadmin/    # React + Vite, port 3000
├── subadmin/      # React + Vite, port 3001 (scaffold — see below)
├── employee/      # React + Vite, port 3002
└── README.md
```

No files are shared or mixed between folders — each frontend has its own
`package.json`, `vite.config.js`, `.env.example`, `src/`, and `public/`, and
is independently runnable with `npm install && npm run dev`. `backend/`
contains all Python/FastAPI source, `requirements.txt`,
`seed_superadmin.py`, `.env.example`, and `tests/`.

### 23.1 What changed

- **`subadmin/`** was a documentation-only placeholder (just a `README.md`).
  It's now a real, independently runnable Vite + React app: `package.json`,
  `vite.config.js` (port `3001`), `.env.example`
  (`VITE_API_URL=http://localhost:8001/api`), `index.html`, and a minimal
  `src/` (entry point, router, a placeholder page, an axios client already
  pointed at the shared backend). It intentionally does **not** ship a login
  form — the backend has no `SUBADMIN` role or routes yet (only
  `SUPERADMIN` and `EMPLOYEE`, see `backend/utils/dependencies.py`), so a
  login screen would only ever fail. The placeholder says exactly that and
  is ready for real screens to be built in without touching any other app.
- **`backend/`, `superadmin/`, `employee/`** — untouched. Their folder
  contents already matched this exact structure; no files were moved.
- `.env.example` contents across all four pieces were checked line-by-line
  against the required values (ports 3000/3001/3002/8001,
  `VITE_API_URL=http://localhost:8001/api` in every frontend, backend
  `CORS_ORIGINS` covering all three frontend origins) — all already correct.

### 23.2 Verification performed in this environment

This sandbox has no network access, so `pip install` / `npm install`
against the real registries can't run here. What was verified instead:

- Every backend `.py` file (unchanged): byte-compiled cleanly
  (`python -m py_compile`).
- Every `.js`/`.jsx` file in `superadmin/`, `subadmin/`, and `employee/`
  (including the new `subadmin/` files): syntax/bundle-checked cleanly with
  `esbuild`.
- Confirmed `superadmin/`, `employee/` were byte-identical to your last
  verified upload — only `subadmin/` and this README changed.
- Confirmed each frontend's dev port (`vite.config.js` + `package.json`
  `"dev"` script) matches 3000 / 3001 / 3002 respectively, and each
  `.env.example` points at `http://localhost:8001/api`.

**Run these on your machine to fully confirm:**

```bash
cd backend && pip install -r requirements.txt && pytest -q
# expect: 33 passed

cd ../superadmin && npm install && npm run build
cd ../subadmin && npm install && npm run build
cd ../employee && npm install && npm run build
# expect: all three build cleanly
```

If SuperAdmin authentication, Employee Registration/Applications/Approval,
Employee Portal, Employee Login, Employee Portal Access, or data sync
between SuperAdmin and the Employee Portal behave differently after this
reorganization, it would be a packaging mistake rather than a logic change
— none of that code was edited — so paste the exact error and I'll fix it.
