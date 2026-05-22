FocusGuard — Production Guide

Overview

This document describes how to run the FocusGuard backend and extension locally, how to deploy to Render, and lists the API contract, database schema, and security best practices required for production readiness.

1) Quick start (local, Docker Compose)

Prerequisites:
- Docker & Docker Compose
- Node 18+ / npm for extension build

Commands:

```bash
# From repository root
docker compose up -d --build
# Wait for Postgres and backend to be healthy
# Optionally: build extension
cd extension
npm install
npm run build
# Load the extension/ folder in Chrome (unpacked) and point to extension/ (ensure dist/ exists)
```

Backend dev (without Docker):

```bash
# create a Python venv, install deps
python -m venv .venv
. .venv/Scripts/activate   # Windows PowerShell: . .venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
# Ensure you have a running Postgres and DATABASE_URL env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2) Render deployment
- The repository includes `render.yaml` at root that configures a `focusguard-backend` service pointing to `backend/` (Docker build). Set the following environment variables in the Render service: `DATABASE_URL`, `JWT_SECRET`, `SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL`, optional Twilio envs.

3) Docker (production-ready)
- `backend/Dockerfile` produces a minimal image based on Python 3.12-slim. Use an external managed Postgres (RDS, Render DB).
- Use a proper secrets manager to store `JWT_SECRET` and SendGrid/Twilio credentials.

4) API Contract Verification (endpoints present in code)

The requested endpoints and their implemented paths/methods:

- POST /register -> `backend/app/api/routes/auth.py` (returns access_token)
- POST /login -> `backend/app/api/routes/auth.py` (returns access_token)
- POST /add-blocked-site -> `backend/app/api/routes/blocking.py`
- POST /remove-blocked-site -> `backend/app/api/routes/blocking.py`
- POST /log-attempt -> `backend/app/api/routes/blocking.py`
- POST /send-approval -> `backend/app/api/routes/accountability.py`
- POST /approve-access -> `backend/app/api/routes/accountability.py`
- GET /weekly-report -> `backend/app/api/routes/reporting.py`
- GET /approve (friend link) -> `backend/app/api/routes/accountability.py` (added as convenience)

Notes:
- All protected endpoints use header `Authorization: Bearer <token>` and FastAPI dependency `get_current_user`.
- Input validation is enforced via Pydantic models in `backend/app/schemas/`.

5) Database schema
- Canonical SQL: `backend/sql/schema.sql`. Tables: `users`, `blocked_sites`, `friends`, `block_attempts`, `approval_requests`.

6) Extension integration
- The extension stores JWT in `chrome.storage.local` under `focusguard_auth` and reads `focusguard_blocked_sites` and `focusguard_friend`.
- It uses `background.ts` to detect tab updates/activation and redirects to `blocked.html` when a domain matches a blocked site.
- The popup now supports registration and login that call `/register` and `/login` and store the returned token.

7) Notifications
- Implemented using SendGrid (email) and Twilio (SMS) in `backend/app/services/notifications.py`. The service checks for configured credentials; when missing the calls are no-ops (safe in dev).

8) Approval flow
- `POST /send-approval` creates an approval token and notifies the latest configured friend for the user.
- Friend can approve via `GET /approve?token=...` (simple HTML response) or `POST /approve-access` for programmatic OTP-style approval.
- When approved, the backend marks the ApprovalRequest as `approved` and returns `unlock_minutes: 5` for programmatic approval.
- The extension honors `unlockUntil` stored in local storage and sets a local alarm for expiry.

9) Security & Production hardening
- Secrets: keep `JWT_SECRET` and provider keys in secrets manager or platform env (do not commit `.env`).
- Passwords hashed with bcrypt via `passlib` (see `backend/app/core/security.py`).
- JWT tokens signed with `python-jose`. Short expiry recommended (configurable via `ACCESS_TOKEN_EXPIRY_MINUTES`).
- Rate limiting: `InMemoryRateLimitMiddleware` provided for basic protection; replace with Redis-backed rate limiter in production (e.g., FastAPI + slowapi or external WAF).
- Notifications should be handed to an async job queue (e.g., Redis + RQ/Celery) to avoid blocking request threads and for retries.
- CORS: lock `CORS_ORIGINS` to explicit frontend origins. The default includes `chrome-extension://*` for extension usage — in production prefer listing the extension ID as origin.
- Approvals: tokens are time-bound and single-use; consider storing a one-time flag to prevent replay and move approval delivery to secure channels (email with clickable deep link + OTP SMS where necessary).
- Database: enable connection pooling, SSL, and restrict inbound access to DB server.
- Logging & Monitoring: centralize logs (Sentry, Datadog), enable structured logging and health checks.

10) Observability & analytics
- `GET /weekly-report` provides a simple aggregated report (attempts, most attempted site, focus score). Extend with background aggregation for scale.

11) Next recommended improvements
- Add Alembic migrations for schema evolution (alembic config + migrations directory).
- Add integration tests that spin up test Postgres and run the FastAPI test client.
- Use a queue for notifications and approval email templates.
- Use HTTPS and HSTS; ensure backend is behind a proper load balancer if scaling.


Contact

If you want, I can:
- Add `alembic` migrations for the current schema.
- Add a basic GitHub Actions workflow to build and test the backend and extension.
- Create a small demo script to register a user and add a blocked site via `curl`.


