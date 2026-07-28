# Hospital Appointment Management System — Backend

Backend for the **Appointment Management Module** of a Hospital Information
Management System (HIMS). Built with **FastAPI**, **SQLAlchemy 2.0**,
**PostgreSQL**, and **Alembic**, with JWT authentication and role-based
access control (RBAC).

Manages **Patients**, **Departments**, **Doctors**, and **Appointments**
end-to-end — booking, confirmation, check-in, consultation, completion,
cancellation, and rescheduling — with an audit trail of sensitive actions.

---

## 1. Tech Stack

| Layer          | Technology                              |
|----------------|------------------------------------------|
| Language       | Python 3.11+                             |
| Framework      | FastAPI                                  |
| Database       | PostgreSQL 13+                           |
| ORM            | SQLAlchemy 2.0 (declarative, typed)      |
| Migrations     | Alembic                                  |
| Validation     | Pydantic v2 / pydantic-settings          |
| Auth           | JWT (python-jose) + passlib (bcrypt)     |
| Docs           | OpenAPI / Swagger UI / ReDoc (built-in)  |

---

## 2. Project Structure

```
backend/
├── alembic.ini                 # Alembic configuration
├── alembic/
│   ├── env.py                  # Wires Alembic to app settings + ORM metadata
│   ├── script.py.mako          # Migration file template
│   └── versions/
│       └── 20260728_0001_initial_schema.py   # Baseline schema migration
├── app/
│   ├── main.py                  # FastAPI app, middleware, router registration
│   ├── core/                    # Config, security (JWT/hashing), exceptions,
│   │                             logging, token blacklist
│   ├── db/                      # Declarative Base, mixins, engine/session
│   ├── models/                  # SQLAlchemy ORM models (one file per entity)
│   ├── schemas/                 # Pydantic request/response schemas
│   ├── repositories/            # Data-access layer (raw queries per entity)
│   ├── services/                # Business logic / validation / orchestration
│   ├── api/v1/                  # FastAPI routers (one file per entity)
│   └── middleware/               # Request ID, rate limiting, security headers
├── tests/                       # Smoke tests (pytest)
├── requirements.txt              # Runtime dependencies
├── requirements-dev.txt          # + pytest/httpx, for running tests
├── .env.example                  # Copy to .env and fill in
└── .gitignore
```

**Layer responsibilities:**

- **api/v1/** — HTTP boundary only: parses requests, calls a service, returns
  a response model. No business logic lives here.
- **services/** — Business rules (overlap checks, status transitions,
  duplicate prevention, RBAC-aware scoping) and transaction orchestration.
- **repositories/** — SQLAlchemy queries only, no business rules. Keeps
  services testable and persistence concerns in one place.
- **models/** — ORM table definitions, enums, relationships.
- **schemas/** — Pydantic I/O contracts, decoupled from ORM models.
- **core/** — Cross-cutting concerns: settings, JWT/password hashing,
  the custom exception hierarchy, logging, and the token revocation store.
- **middleware/** — Request ID propagation, fixed-window rate limiting on
  auth endpoints, security response headers.

---

## 3. Prerequisites

- Python 3.11+
- PostgreSQL 13+ running and reachable
- A database created for this project, e.g.:

  ```sql
  CREATE DATABASE hims_appointment_db;
  ```

---

## 4. Setup

```bash
# 1. Clone and enter the project
git clone <your-repo-url>
cd <repo>/backend

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env: set POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_SERVER /
# POSTGRES_DB (or DATABASE_URL directly) and a real SECRET_KEY.

# 5. Apply database migrations
alembic upgrade head

# 6. Run the API
uvicorn app.main:app --reload
```

The API is now available at `http://localhost:8000`.

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI schema: `http://localhost:8000/openapi.json`
- Health check: `http://localhost:8000/health`

---

## 5. Environment Variables

See `.env.example` for the full, authoritative list (database connection
pieces, JWT secret/algorithm/expiry, CORS origins, pagination defaults,
default appointment duration, logging). Every setting is loaded through
`app/core/config.py`; nothing is hardcoded elsewhere in the codebase.

**Before deploying anywhere beyond local development, always change
`SECRET_KEY`** to a long, random value (e.g. `openssl rand -hex 32`) —
the default in `.env.example` is a placeholder only.

---

## 6. Database Migrations (Alembic)

Migrations are wired directly into the app's own settings and ORM models
(`alembic/env.py` imports `app.core.config.settings` for the connection
string and `app.models` for the schema), so there is one source of truth.

```bash
# Apply all migrations (creates every table, enum, FK, and index)
alembic upgrade head

# Roll back the most recent migration
alembic downgrade -1

# Roll back everything
alembic downgrade base

# After changing/adding a model, generate the next migration
alembic revision --autogenerate -m "describe your change"

# Inspect current DB revision / history
alembic current
alembic history --verbose
```

The initial migration (`20260728_0001_initial_schema.py`) creates, in
dependency order: `departments` → `users` → `doctors` (then wires the
deferred `users.doctor_id → doctors.id` foreign key) → `patients` →
`appointments` → `audit_logs`, along with every unique/lookup index used
by the repositories — including composite indexes on
`(doctor_id, appointment_date, status)` and
`(patient_id, appointment_date, status)` that back the double-booking
checks in `AppointmentRepository`.

---

## 7. Authentication & RBAC

JWT access + refresh tokens (`app/core/security.py`), with logout-time
revocation via an in-memory `jti` blacklist (`app/core/token_blacklist.py`
— documented there as a single-process implementation; swap for Redis in a
multi-worker/multi-replica production deployment).

**Roles** (`app.models.user.UserRole`): `SUPER_ADMIN`, `HOSPITAL_ADMIN`,
`RECEPTIONIST`, `DOCTOR`. Endpoints enforce role checks via the
`RoleChecker` dependency in `app/api/deps.py`; a `DOCTOR` account is
additionally scoped to their own appointments via `require_own_doctor_profile`.

Creating your first account:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "Hospital Admin",
        "password": "ChangeMe123",
        "role": "SUPER_ADMIN"
      }'
```

> `/auth/register` accepts a `role` field directly for development
> convenience. In a real deployment, gate account creation (or restrict
> which roles a caller may self-assign) behind an already-authenticated
> admin — this is a policy decision to make before production rollout,
> not a code change.

---

## 8. API Testing Instructions

### Option A — Swagger UI (fastest)

1. Run the server, open `http://localhost:8000/docs`.
2. `POST /api/v1/auth/register`, then `POST /api/v1/auth/login` to get an
   `access_token`.
3. Click **Authorize** (top right), enter `Bearer <access_token>`.
4. Exercise any endpoint interactively, including request/response
   validation shown inline.

### Option B — curl walkthrough (full booking flow)

```bash
BASE=http://localhost:8000/api/v1

# 1. Login (after registering, see section 7)
TOKEN=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"ChangeMe123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

AUTH="Authorization: Bearer $TOKEN"

# 2. Create a department
curl -s -X POST $BASE/departments -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"name":"Cardiology","description":"Heart & vascular care"}'

# 3. Create a doctor (use the department id returned above)
curl -s -X POST $BASE/doctors -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"employee_id":"EMP001","full_name":"Dr. Jane Doe","department_id":"<dept-uuid>","specialization":"Cardiologist","mobile_number":"9999999999","email":"jane.doe@example.com","consultation_fee":500}'

# 4. Create a patient
curl -s -X POST $BASE/patients -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"first_name":"John","last_name":"Smith","gender":"MALE","date_of_birth":"1990-01-01","mobile_number":"8888888888","email":"john.smith@example.com"}'

# 5. Book an appointment (use the ids returned above)
curl -s -X POST $BASE/appointments -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"patient_id":"<patient-uuid>","doctor_id":"<doctor-uuid>","department_id":"<dept-uuid>","appointment_date":"2026-08-01","appointment_time":"10:00:00","appointment_type":"OPD","priority":"NORMAL","reason_for_visit":"Routine checkup"}'

# 6. List / search appointments
curl -s "$BASE/appointments?page=1&page_size=20&status=SCHEDULED" -H "$AUTH"
```

Repeat step 5 with the same doctor/date/time to confirm the API rejects
double-booking with a `409 Conflict`.

### Option C — Automated smoke test (pytest)

```bash
pip install -r requirements-dev.txt
pytest -v
```

`tests/test_health.py` verifies the app boots, all routers import cleanly,
and Swagger/OpenAPI are served — useful as a fast CI sanity check before a
database is even available. It intentionally does **not** hit any DB-backed
endpoint; use Options A/B above (or extend `tests/` with your own
Postgres-backed fixtures) for full CRUD/auth-flow coverage.

---

## 9. Error Format

All handled errors return a consistent JSON shape (see
`app/core/exception_handlers.py`):

```json
{
  "error_code": "NOT_FOUND",
  "message": "Doctor not found (id=...)",
  "details": {}
}
```

with the HTTP status code matching the exception raised (`404`, `409`,
`422`, `401`, `403`, `429`, etc. — see `app/core/exceptions.py` for the
full hierarchy).

---

## 10. Deployment Instructions

These are general-purpose steps; adapt hosting specifics to your provider.

1. **Provision PostgreSQL** (managed service recommended: RDS, Cloud SQL,
   Azure Database for PostgreSQL, etc.). Note the connection details.
2. **Set environment variables** on the host/container — at minimum:
   `DATABASE_URL` (or the individual `POSTGRES_*` vars), a strong
   `SECRET_KEY`, `ENVIRONMENT=production`, `DEBUG=false`, and
   `BACKEND_CORS_ORIGINS` set to your real frontend origin(s) (not `["*"]`
   — see the CORS note in `app/main.py` regarding credentialed requests).
3. **Install dependencies**: `pip install -r requirements.txt`.
4. **Run migrations before starting the app**: `alembic upgrade head`.
   Run this as an explicit release/deploy step, not inside app startup, so
   a failed migration blocks the deploy instead of half-starting the app.
5. **Run the app with a production ASGI setup**, e.g.:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```
   or behind Gunicorn with the Uvicorn worker class:
   ```bash
   gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000
   ```
6. **Put a reverse proxy in front** (nginx / cloud load balancer) for TLS
   termination; forward `X-Forwarded-For` so `app/api/v1/auth.py`'s
   `_client_ip` resolves real client IPs for audit logging/rate limiting.
7. **Multi-worker/multi-replica caveat**: both the JWT revocation store
   (`app/core/token_blacklist.py`) and the auth rate limiter
   (`app/middleware/rate_limit_middleware.py`) are documented, intentional
   in-memory implementations. Each process/replica has its own copy. For
   real multi-instance production traffic, back both with Redis (the
   call-site contracts — `revoke()`/`is_revoked()`, the fixed-window
   counter — are designed to swap in a shared store without touching
   calling code).
8. **Logging**: `LOG_JSON=true` in production for structured logs your log
   aggregator (CloudWatch, Stackdriver, ELK, etc.) can parse.

### Containerizing (optional)

A minimal `Dockerfile` (not included by default — add if your deployment
target needs it):

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Run migrations as a separate step/job (`alembic upgrade head`) before
starting the container in production, e.g. as a Kubernetes init container
or a pre-deploy CI step.

---

## 11. Business Rules Enforced

- A doctor cannot have overlapping active appointments (checked in
  `AppointmentService` against `AppointmentRepository.get_active_for_doctor_on_date`).
- A patient cannot hold two active appointments at the same time.
- Appointment dates cannot be booked in the past.
- Appointment duration defaults to `DEFAULT_APPOINTMENT_DURATION_MINUTES`
  (configurable via `.env`), overridable per appointment.
- Inactive doctors cannot receive new appointments.
- Cancelling/no-showing an appointment releases the slot (see
  `RELEASED_STATUSES` in `app/models/appointment.py`) so it becomes bookable
  again.
- Follow-up appointments reference the originating appointment via
  `parent_appointment_id`.
- Status transitions follow the explicit state machine in
  `ALLOWED_STATUS_TRANSITIONS` (`app/models/appointment.py`) — e.g. a
  `COMPLETED` appointment can never move to any other status.

---

## 12. License

Internal / educational project — add a license here if you intend to
publish this repository publicly.
