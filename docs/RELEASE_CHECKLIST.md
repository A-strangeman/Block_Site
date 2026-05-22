# Release Checklist

Before merging to `main`:

- Ensure all tests pass and CI (including audits) is green.
- Confirm `backend/.env` and secrets are set in staging.
- Verify migrations are included (run `alembic revision --autogenerate` if needed).

Staging deployment:

- Build backend image and push to registry.
- Apply migrations to staging DB.
- Deploy to staging (k8s/Render/ECS) and wait for pods to be ready.
- Validate `/ready`, `/health`, and `/metrics` endpoints.
- Verify Sentry errors (no new regressions) and Prometheus metrics.

Production release:

- Repeat staging steps and monitor traffic, logs, and errors.
