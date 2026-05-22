# Deployment Runbook

This runbook covers deploying FocusGuard to production (Render, ECS, or Kubernetes).

1) Build and push backend image

- Ensure `backend/.env` is populated from `backend/.env.example` with production values.
- Build the image locally:

```bash
docker build -t registry.example.com/focusguard/backend:latest -f backend/Dockerfile .
docker push registry.example.com/focusguard/backend:latest
```

2) Database migrations

- Run Alembic migrations against your production database:

```bash
# from backend/
alembic upgrade head
```

3) Environment variables and secrets

- Use a secret store (Render Secrets, AWS Secrets Manager, GitHub Secrets) to store:
  - `DATABASE_URL`
  - `SECRET_KEY`
  - `SENDGRID_API_KEY`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`
  - `REDIS_URL`
  - `SENTRY_DSN` (optional)

4) Deploying the extension

- The extension build uses environment variable `API_BASE` at build/package time.
- For CI-based releases, set `API_BASE` to your production API URL and run `npm run build` in `extension/`.

5) Healthchecks & Probes

- The backend exposes `/health` and `/ready` endpoints. Configure your platform to use `/ready` as readiness probe and `/health` for liveness.

6) Monitoring & Logs

- Set `SENTRY_DSN` to enable Sentry crash reporting.
- Expose `/metrics` for Prometheus scraping.

7) Dependency audits

- CI will run `pip-audit` and `npm audit --audit-level=high` to block high-severity vulnerabilities.

8) Rollback

- Use your container registry tags to roll back to the previous image.
