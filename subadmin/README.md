# SubAdmin Portal (scaffold)

A real, independently runnable Vite + React app (same stack as `superadmin/`
and `employee/`), scaffolded so SubAdmin screens can be built here later
without touching `backend/`, `superadmin/`, or `employee/`.

**No SubAdmin role or routes exist on the backend yet** (only `SUPERADMIN`
and `EMPLOYEE` — see `backend/utils/dependencies.py`), so this app currently
shows a placeholder page instead of a login form that would always fail.
It connects to the **same** FastAPI backend and MongoDB database as the
other two portals — no new backend or database is needed when SubAdmin
routes are added.

## Run it

```bash
cd subadmin
npm install
cp .env.example .env
npm run dev   # http://localhost:3001
```

## Build

```bash
npm run build
```
