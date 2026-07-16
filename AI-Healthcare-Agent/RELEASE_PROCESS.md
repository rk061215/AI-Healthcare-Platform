# Release Process

This document defines the release workflow, versioning scheme, and deployment procedures for the AI Healthcare Follow-up Assistant.

## Table of Contents

- [Semantic Versioning](#semantic-versioning)
- [Release Checklist](#release-checklist)
- [Migration Checklist](#migration-checklist)
- [Rollback Procedure](#rollback-procedure)
- [Deployment Procedure](#deployment-procedure)

---

## Semantic Versioning

This project follows [Semantic Versioning 2.0.0](https://semver.org/).

### Version Format

```
MAJOR.MINOR.PATCH
```

| Component | Bump When                                                                 | Example  |
|-----------|---------------------------------------------------------------------------|----------|
| MAJOR     | Incompatible API changes, breaking database migrations, removed features  | `1.0.0` → `2.0.0` |
| MINOR     | New features, new endpoints, new agent workflows, backward-compatible     | `1.0.0` → `1.1.0` |
| PATCH     | Bug fixes, security patches, performance improvements, backward-compatible| `1.0.0` → `1.0.1` |

### Pre-release Tags

Use for staging and testing before production:

```
0.3.0-alpha.1
0.3.0-beta.2
0.3.0-rc.1
```

| Tag     | Meaning                                      |
|---------|----------------------------------------------|
| `alpha` | Feature incomplete, internal testing         |
| `beta`  | Feature complete, external testing           |
| `rc`    | Release candidate, final validation          |

### Version Location

Update the version in the following places (in the same commit or the release commit):

| File                    | Field                    |
|-------------------------|--------------------------|
| `backend/app/main.py`   | `version` parameter in `FastAPI()` and `/health` endpoint |
| `backend/pyproject.toml`| `version` field         |
| `frontend/package.json` | `version` field         |
| `CHANGELOG.md`          | New version header      |
| `CURRENT_STATUS.md`     | `Current Version` field |

---

## Release Checklist

### Pre-Release (T-7 days)

- [ ] Review open issues and PRs tagged for this release.
- [ ] Resolve all `blocker` review comments on targeted PRs.
- [ ] Identify breaking changes and plan migration steps.

### Pre-Release (T-48 hours)

- [ ] Create a release branch: `release/v{MAJOR}.{MINOR}.{PATCH}`.
- [ ] Run the full test suite and confirm all tests pass:

  ```bash
  cd backend
  pytest -v --cov=app --cov-report=term --cov-report=html
  cd ../frontend
  npm run test:run
  ```

- [ ] Run linting and type checking:

  ```bash
  cd backend
  black . --check
  isort . --check-only
  flake8 app/
  mypy app/

  cd ../frontend
  npm run lint
  npm run type-check
  ```

- [ ] Audit dependencies for vulnerabilities:

  ```bash
  pip-audit
  cd frontend && npm audit
  ```

- [ ] Verify all environment variables are documented in `.env.example` files.
- [ ] Update `CHANGELOG.md`:
  - Move changes from `[Unreleased]` to the new version header.
  - Group entries as `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.
  - Include migration steps if applicable.

### Release Day

- [ ] Bump version numbers in all locations (see [Version Location](#version-location)).
- [ ] Commit version bumps: `chore(release): bump to v{MAJOR}.{MINOR}.{PATCH}`.
- [ ] Tag the commit:

  ```bash
  git tag -a v{MAJOR}.{MINOR}.{PATCH} -m "Release v{MAJOR}.{MINOR}.{PATCH}"
  git push origin v{MAJOR}.{MINOR}.{PATCH}
  ```

- [ ] Merge the release branch into `main`.
- [ ] Deploy to staging environment (see [Deployment Procedure](#deployment-procedure)).
- [ ] Run smoke tests on staging:

  ```bash
  # Health check
  curl -f http://staging.example.com/health

  # Auth flow
  curl -f -X POST http://staging.example.com/api/v1/auth/register/patient \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"TestPass123!","confirm_password":"TestPass123!","full_name":"Test","terms_accepted":true}'
  ```

- [ ] Deploy to production (same procedure).
- [ ] Verify production health check.
- [ ] Tag the release on GitHub with release notes from CHANGELOG.md.
- [ ] Notify stakeholders (Slack, email, etc.).

### Post-Release

- [ ] Create a new `[Unreleased]` section in CHANGELOG.md.
- [ ] Update TASKS.md with completed tasks.
- [ ] Update CURRENT_STATUS.md version and progress.
- [ ] Close the release milestone in the issue tracker.
- [ ] Hold a post-mortem if the release had issues.

---

## Migration Checklist

### When a Migration is Required

Database migrations are needed when:
- A new table is added.
- A column is added, removed, or modified.
- An index is added or removed.
- A constraint is changed.
- Seed data needs to be updated.

### Migration Steps

1. **Generate the migration**:

   ```bash
   cd backend
   alembic revision --autogenerate -m "description_of_change"
   ```

2. **Review the generated migration** in `alembic/versions/`. Verify:
   - `upgrade()` creates/drops the correct tables/columns/indexes.
   - `downgrade()` exactly reverses the upgrade.
   - No data loss occurs for existing rows (provide defaults for new non-nullable columns).
   - Batch operations for large tables (if applicable).

3. **Test the migration**:

   ```bash
   # Reset the test database
   # (Current test setup uses SQLite; verify manually on PostgreSQL)
   alembic downgrade -1
   alembic upgrade head
   ```

4. **Test the rollback**:

   ```bash
   alembic downgrade -1
   alembic upgrade head  # re-apply
   ```

5. **Commit both** the migration file and any model/schema changes in the same PR.

### Migration PR Checklist

- [ ] Migration file is reviewed by a second developer.
- [ ] `downgrade()` is tested and works.
- [ ] Models are updated to match the new schema.
- [ ] Schemas are updated to match the new columns.
- [ ] Seed data scripts are updated (if applicable).
- [ ] Migration has been run against a copy of production data (if possible).
- [ ] Rollback procedure is documented in the PR description.

### Zero-Downtime Migrations

Guidelines for avoiding production downtime:

| Change Type              | Strategy                                                      |
|--------------------------|--------------------------------------------------------------|
| Add column (nullable)    | Safe — run migration; deploy code that may read the column   |
| Add column (non-nullable)| Two-phase: add as nullable, backfill data, add NOT NULL      |
| Remove column            | Safe — deploy code that no longer reads the column, then migrate |
| Rename column            | Two-phase: add new column, dual-write, backfill, remove old  |
| Add table                | Safe — deploy code, then migrate                             |
| Add index                | Safe — can run concurrently (CREATE INDEX CONCURRENTLY)      |
| Remove index             | Safe — run migration after deploying code that no longer needs it |

---

## Rollback Procedure

### Application Rollback

If a deployment causes issues:

```bash
# Option 1: Revert to previous version
git revert HEAD
git push origin main

# Option 2: Checkout and deploy previous tag
git checkout v{previous_version}
# Build and deploy
```

### Database Rollback

```bash
# Roll back the last migration
cd backend
alembic downgrade -1

# Roll back to a specific version
alembic downgrade {previous_revision_id}

# Roll back all the way
alembic downgrade base
```

### Combined Rollback

In most cases, you need to roll back both the code and the database:

```
1. Roll back database: alembic downgrade {previous_revision}
2. Deploy previous code version
3. Verify health check
4. Notify stakeholders
```

### Rollback Scenarios

| Scenario                          | Action                                                                 |
|-----------------------------------|------------------------------------------------------------------------|
| Broken API response               | Revert code only. No DB rollback needed.                               |
| Wrong column type                 | Roll back migration + revert code.                                     |
| Data corruption                   | Restore from backup (WAL archival). Apply fix forward.                 |
| Performance regression            | Revert code. Run `DROP INDEX` if a new index caused the problem.       |
| Security vulnerability            | Revert code immediately. Fix forward in a hotfix.                      |

### Backup Verification

- Automated database backups must run at least daily.
- Test restoration from backup at least once per quarter.
- Document the backup restore procedure in the operations runbook.

---

## Deployment Procedure

### Prerequisites

- PostgreSQL 16 running and accessible.
- `DATABASE_URL` environment variable set.
- `JWT_SECRET_KEY` set to a strong random value.
- `OPENAI_API_KEY` set (for AI features).
- `BACKEND_CORS_ORIGINS` configured with production domains.
- `REDIS_URL` set if using Redis-backed rate limiting (optional).

### Environment Configuration

Create a `.env` file on the server:

```bash
# Required
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://user:password@host:5432/healthcare_agent
JWT_SECRET_KEY=<generate-a-strong-64-char-random-key>
OPENAI_API_KEY=sk-...
BACKEND_CORS_ORIGINS=https://app.example.com

# Optional (for Redis-backed rate limiting)
REDIS_URL=redis://redis:6379/0

# Optional (for OCR)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

### Deployment Steps

```bash
# 1. Pull latest code
git pull origin main

# 2. Install dependencies
cd backend
pip install -r requirements.txt

cd ../frontend
npm ci --production

# 3. Run database migrations
cd ../backend
alembic upgrade head

# 4. Build frontend
cd ../frontend
npm run build

# 5. Run database health check
python -c "from app.database.session import get_sync_engine; e = get_sync_engine(); e.connect(); print('DB OK')"

# 6. Start backend (via process manager)
# Using Supervisor, systemd, or Docker:
gunicorn app.main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -

# 7. Start frontend (via process manager)
cd ../frontend
npm run start -- -p 3000

# 8. Verify deployment
curl -f http://localhost:8000/health
curl -f http://localhost:3000
```

### Docker Deployment

```bash
# Build images
docker compose -f docker/docker-compose.yml build

# Run migrations (one-time)
docker compose run --rm backend alembic upgrade head

# Start services
docker compose -f docker/docker-compose.yml up -d

# Verify
docker compose ps
docker compose logs --tail=50
```

### Canary Deployment

For high-risk releases:

1. Deploy to 10% of instances.
2. Monitor error rates and latency for 30 minutes.
3. If stable, deploy to remaining 90%.
4. If issues detected, roll back the canary instances.

### Monitoring After Deployment

- Error rate (target: < 0.1% of requests).
- P95 response time (target: < 500ms for API, < 2s for AI agents).
- Database connection pool utilization (target: < 70%).
- Rate limit hit rate (alert if > 1% of requests are being throttled).
- Application logs for unexpected errors or warnings.

---

*Last updated: 2026-07-11*
