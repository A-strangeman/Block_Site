## Summary
- Brief description of the change and why it is needed.

## Checklist (required before merge)
- [ ] CI passes (tests, lint, typecheck)
- [ ] No high-severity vulnerabilities (pip-audit / npm audit)
- [ ] DB migrations reviewed and included if required
- [ ] Secrets configured for staging/production
- [ ] Healthchecks verified (/health and /ready)
- [ ] Metrics exposed and Sentry configured (if enabled)
- [ ] Release notes updated (docs/RELEASE_CHECKLIST.md)

## Deployment runbook (short checklist)
- Build and push backend image
- Run alembic migrations
- Deploy to staging and validate healthchecks and metrics
- Promote to production after validation
