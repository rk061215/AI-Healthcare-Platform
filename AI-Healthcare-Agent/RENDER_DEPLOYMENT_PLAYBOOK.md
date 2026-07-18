# Render Deployment Playbook — AI Healthcare Platform v1.0.0

## 1. Deployment Checklist

### Repository
| Item | Value |
|------|-------|
| Provider | GitHub |
| URL | `https://github.com/rk061215/AI-Healthcare-Platform` |
| Branch | `main` |
| Latest commit | `76d367e` |
| Blueprint file | `render.yaml` (repo root) |

### Services

| Service | Type | Plan | Dockerfile Path | Context |
|---------|------|------|-----------------|---------|
| `healthcare-backend` | web (Docker) | Free (Oregon) | `AI-Healthcare-Agent/backend/Dockerfile` | `AI-Healthcare-Agent/backend` |
| `healthcare-frontend` | web (Docker) | Free (Oregon) | `AI-Healthcare-Agent/frontend/Dockerfile` | `AI-Healthcare-Agent/frontend` |

### Startup Commands

| Service | Command | Port |
|---------|---------|------|
| Backend | `./startup.sh` → `alembic upgrade head` → `uvicorn app.main:app --host 0.0.0.0 --port 8000` | 8000 (EXPOSE) |
| Frontend | `node server.js` (Next.js standalone) | 3000 (EXPOSE) |

### Health Check Endpoints

| Service | Path | Response |
|---------|------|----------|
| Backend | `GET /health` | `{"status": "healthy", "version": "1.0.0", "vector_store": "..."}` |
| Frontend | `GET /` | Next.js root page (200 OK) |

### Persistent Disk

| Property | Value |
|----------|-------|
| Name | `data` |
| Mount path | `/app/data` |
| Size | 1 GB |
| Backend dirs on disk | `/app/data/uploads` → `UPLOAD_DIR`, `/app/data/documents` → `DOCUMENT_STORAGE_DIR` |

---

## 2. Environment Variables

### Backend (`healthcare-backend`)

| Key | Type | Value / Source |
|-----|------|----------------|
| `ENVIRONMENT` | plain | `production` |
| `DEBUG` | plain | `false` |
| `LOG_LEVEL` | plain | `INFO` |
| `DATABASE_URL` | **secret** | Neon PostgreSQL connection string |
| `JWT_SECRET_KEY` | **secret** | Random 32+ char string |
| `BACKEND_CORS_ORIGINS` | plain | `https://healthcare-frontend.onrender.com` |
| `GEMINI_API_KEY` | **secret** | Google AI Studio API key |
| `AI_PROVIDER` | plain | `gemini` |
| `REDIS_URL` | plain | `""` (empty — uses in-memory rate limiter) |
| `SENTRY_DSN` | plain | `""` (empty — Sentry disabled) |
| `RATE_LIMIT_PER_MINUTE` | plain | `120` |
| `RATE_LIMIT_LOGIN_PER_MINUTE` | plain | `10` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | plain | `""` (empty — telemetry disabled) |
| `UPLOAD_DIR` | plain | `/app/data/uploads` |
| `DOCUMENT_STORAGE_DIR` | plain | `/app/data/documents` |
| `CHROMA_PERSIST_DIR` | plain | `/app/data/chromadb` (documents intent; code reads `VectorStoreConfig.persist_directory` default `./chromadb_data`) |

### Frontend (`healthcare-frontend`)

| Key | Type | Value |
|-----|------|-------|
| `NODE_ENV` | plain | `production` |
| `NEXT_PUBLIC_API_URL` | plain | `https://healthcare-backend.onrender.com/api/v1` |
| `NEXT_PUBLIC_WS_URL` | plain | `wss://healthcare-backend.onrender.com/ws` |
| `NEXT_PUBLIC_APP_URL` | plain | `https://healthcare-frontend.onrender.com` |
| `NEXT_PUBLIC_ENABLE_CHAT` | plain | `true` |
| `NEXT_PUBLIC_ENABLE_EMERGENCY` | plain | `true` |
| `NEXT_PUBLIC_ENABLE_REMINDERS` | plain | `true` |

---

## 3. Required Secrets

| # | Name | Required? | Default | Example Format | Purpose |
|---|------|-----------|---------|----------------|---------|
| 1 | `DATABASE_URL` | **Yes** | `postgresql://neondb_owner:...@ep-holy-tree.au74ocm0.us-east-1.aws.neon.tech/neondb?sslmode=require` | `postgresql://user:pass@host:5432/db?sslmode=require` | PostgreSQL connection for all data persistence, Alembic migrations |
| 2 | `JWT_SECRET_KEY` | **Yes** | `change-me-to-a-random-secret-key` | `a9f8d7e6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9` | Signs and verifies all JWT access/refresh tokens; if default, startup emits `UserWarning` |
| 3 | `GEMINI_API_KEY` | **Yes** | `""` (empty) | `AIzaSyD-...` | Authenticates all Gemini AI calls: chat, embeddings, OCR analysis, LangGraph graph execution |

### Notes
- Secrets are set via Render Dashboard → Blueprint → "Environment" tab after importing the repo
- Render stores secrets encrypted; they are `sync: false` in the blueprint (not committed)
- If a secret is missing, the affected subsystem will log a warning and degrade gracefully

---

## 4. Error Classification

When deployment fails, find the error type below for probable cause and fix.

| # | Error Category | Probable Cause | Fix |
|---|---------------|----------------|-----|
| 1 | **Blueprint** | Render rejects `render.yaml` — schema validation error | Fix YAML indentation, rename `disks:` → `disk:`, ensure `disk:` is a single object (not list). Validate with `python -c "import yaml; yaml.safe_load(open('render.yaml'))"` |
| 2 | **Build** | Docker build fails (network timeout, pip install error) | Restart deploy. Pin exact package versions in `requirements.txt`. Ensure `python:3.12.9-slim` tag exists |
| 3 | **Docker** | EXPOSE port mismatch, WORKDIR wrong, COPY path missing | `WORKDIR /app` must exist; `COPY . .` copies from context dir. Verify `dockerContext` in blueprint points to dir containing `startup.sh`, `requirements.txt`, `app/` |
| 4 | **Dependency** | Python package not found or version conflict | Check full build log for `pip` errors. Requirements.txt installed twice (line 19 + line 42 in Dockerfile) — ensure wheels build correctly |
| 5 | **Python** | ImportError at runtime (module not found) | Check `PYTHONPATH=/app` is set. Verify `app.main` exists. Run locally to catch import cycles |
| 6 | **Alembic** | Migration fails on startup (`startup.sh` line 7) | `alembic upgrade head` requires DATABASE_URL env var. Check Neon reachability. Migration `0001_initial_schema.py` had duplicate `index=True` on FK columns — fixed in commit. |
| 7 | **PostgreSQL** | Cannot connect to Neon — timeout, SSL error, auth failure | Verify DATABASE_URL format: `postgresql://user:pass@host:port/db?sslmode=require`. Check Neon IP allowlist (Render egress IPs change). Check if Neon free-tier paused due to inactivity |
| 8 | **Gemini** | AI call fails — 403, 429, quota exceeded | GEMINI_API_KEY may be wrong, expired, or quota exhausted (free tier: 60 requests/min). Key was verified working but quota hit during test |
| 9 | **OCR** | Tesseract not found or missing language pack | Dockerfile installs `tesseract-ocr` + `tesseract-ocr-eng`. Check `startup.sh` output for tesseract version. If missing, rebuild with `apt-get` fix |
| 10 | **Filesystem** | Cannot write to `/app/data/uploads` or `/app/data/documents` | Render disk mounted at `/app/data` with `USER app`. Ensure `mkdir -p` is in Dockerfile with `chown app:app`. On first deploy, directories are created by the `settings.upload_path` / `settings.document_storage_path` properties |
| 11 | **Health Check** | Render reports `unhealthy` — /health returns non-200 | Backend root `/health` returns fast (no DB). If it 502s, uvicorn hasn't started yet (cold start). Allow 60s for first deploy. Check logs for startup errors |
| 12 | **Runtime** | 500 errors on API calls after deploy succeeds | Check backend logs. Common causes: stale `.pyc` files, missing env var, Gemini API quota exceeded, ChromaDB rebuild failure |
| 13 | **Import** | LangGraph imports fail due to circular dependency | Seen with `MedicalQAGraph` importing from `langgraph.graphs`. Check `app.langgraph` modules. Logs will show stack trace |
| 14 | **Uvicorn** | Server fails to bind to port | Port 8000 hardcoded in `startup.sh`. Ensure EXPOSE 8000 in Dockerfile matches. Render routes based on EXPOSE directive |

---

## 5. Step-by-Step Deployment

### Phase 1: Pre-Deploy

1. **Verify Neon PostgreSQL is running**
   ```bash
   # Test connection (from any machine with psql)
   psql "postgresql://neondb_owner:...@ep-holy-tree.au74ocm0.us-east-1.aws.neon.tech/neondb?sslmode=require" -c "SELECT 1"
   ```
   Expected: `?column?` → `1`

2. **Confirm all secrets are ready**
   - [ ] DATABASE_URL (Neon connection string)
   - [ ] JWT_SECRET_KEY (random 32+ chars)
   - [ ] GEMINI_API_KEY (from Google AI Studio)

### Phase 2: Blueprint Import

3. **Navigate to** [Render Dashboard](https://dashboard.render.com)
4. **Click** "New +" → "Blueprint"
5. **Connect** `github.com/rk061215/AI-Healthcare-Platform`
6. **Select** branch `main`
7. **Verify** Render auto-detects `render.yaml` at repo root
8. **Click** "Apply Blueprint"

### Phase 3: Configure Secrets

Render pauses to let you set secrets. For each `sync: false` variable:

| Secret | Paste This |
|--------|------------|
| `DATABASE_URL` | `postgresql://neondb_owner:npg_wyaN8m5pdIgM@ep-holy-tree-au74ocm0.c-10.us-east-1.aws.neon.tech/neondb?sslmode=require` |
| `JWT_SECRET_KEY` | A **new** random 32+ char string (NOT the default) |
| `GEMINI_API_KEY` | Your Google AI Studio API key starting with `AIza` |

### Phase 4: Monitor Build

9. **Watch** the deploy logs in Render Dashboard
10. Expected sequence:
    ```
    [BUILD] Starting Docker build for healthcare-backend
    [BUILD] Step 1/19 : FROM python:3.12.9-slim AS builder
    [BUILD] Step 2/19 : WORKDIR /build
    [BUILD] ...pip wheel... (downloads ~80 packages)
    [BUILD] Step 12/19 : WORKDIR /app
    [BUILD] Step 13/19 : RUN pip install /wheels/*
    [BUILD] Step 16/19 : COPY . .
    [BUILD] Step 19/19 : CMD ["./startup.sh"]
    [BUILD] Exporting layers
    [BUILD] Pushing image to registry
    [DEPLOY] Starting container
    [DEPLOY] === AI Healthcare Backend Startup ===
    [DEPLOY] [1/4] Running database migrations...
    [DEPLOY]   INFO  [alembic.runtime.migration] Running upgrade -> 0001
    [DEPLOY]   INFO  [alembic.runtime.migration] Running upgrade 0001 -> 0002
    [DEPLOY]   INFO  [alembic.runtime.migration] Running upgrade 0002 -> 0003
    [DEPLOY]   INFO  [alembic.runtime.migration] Running upgrade 0003 -> 0004
    [DEPLOY]   INFO  [alembic.runtime.migration] Running upgrade 0004 -> 0005
    [DEPLOY] [1/4] Migrations complete.
    [DEPLOY] [2/4] Checking Tesseract OCR...
    [DEPLOY]   tesseract: tesseract 5.x
    [DEPLOY]   languages: eng
    [DEPLOY] [3/4] Checking system dependencies...
    [DEPLOY]   poppler-utils: available
    [DEPLOY] [4/4] Starting uvicorn...
    [DEPLOY]   INFO:     Started server process [1]
    [DEPLOY]   INFO:     Waiting for application startup.
    [DEPLOY]   INFO:     Application startup complete.
    [DEPLOY]   INFO:     Uvicorn running on http://0.0.0.0:8000
    ```

### Phase 5: Verify Deployment

11. **Health check** — should return immediately after uvicorn starts:
    ```bash
    curl https://healthcare-backend.onrender.com/health
    ```
    Expected:
    ```json
    {"status": "healthy", "version": "1.0.0", "vector_store": "healthy"}
    ```

12. **Detailed health** (includes DB diagnostics):
    ```bash
    curl https://healthcare-backend.onrender.com/api/v1/monitoring/health
    ```
    Expected:
    ```json
    {"status": "ok", "version": "1.0.0", "database": "ok", ...}
    ```

13. **Ready probe** (comprehensive subsystem check):
    ```bash
    curl https://healthcare-backend.onrender.com/ready
    ```
    Expected: `{"status": "ready", ...}` or `"status": "not_ready"` with `unready_services` array

14. **Frontend**:
    ```bash
    curl https://healthcare-frontend.onrender.com/
    ```
    Expected: 200 OK, HTML response (Next.js page)

15. **API test**:
    ```bash
    curl https://healthcare-backend.onrender.com/api/v1/health
    ```
    Expected: JSON with database health details

### Phase 6: Redeploy (if needed)

16. **Manual redeploy**: Render Dashboard → Service → "Manual Deploy" → "Clear build cache & deploy"
17. **Trigger rebuild**: Push a new commit to `main` branch
18. **Rollback**: Render Dashboard → Service → "Manual Deploy" → "Deploy from parent" → select previous version

---

## 6. Common Failures & Recovery

### Failure: "Disks" schema error
```
Error: field disks not found in type file.Service
```
**Fix**: Change `disks:` (plural list) → `disk:` (singular object) in `render.yaml`.

### Failure: Health check never passes
```
Service is unhealthy — failing health checks
```
**Verify**: Wait 60s for cold start. Check logs:
1. Did `alembic upgrade head` complete?
2. Did `uvicorn` start successfully?
3. Is the health endpoint responding? `curl https://.../health`

### Failure: Database connection timeout
```
sqlalchemy.exc.OperationalError: could not connect to server
```
**Check**: Wait 10s for Neon to wake from idle. If persistent, verify DATABASE_URL in Render secrets. Test with `psql` from local machine.

### Failure: Gemini API error
```
google.api_core.exceptions.PermissionDenied: 403 API key not valid
```
**Check**: GEMINI_API_KEY secret is set correctly. Verify at [Google AI Studio](https://aistudio.google.com).

### Failure: ChromaDB initialization error
```
chromadb.errors.ChromaError: Failed to initialize PersistentClient
```
**Check**: `./chromadb_data` directory (WORKDIR=/app). If PermissionError, Dockerfile `USER app` may lack write access. Create dir in Dockerfile with `RUN mkdir -p /app/chromadb_data && chown -R app:app /app/chromadb_data`.

---

## 7. Rollback Plan

| Situation | Action |
|-----------|--------|
| Blueprint import fails | Fix `render.yaml`, commit, push. Render auto-retries on new push |
| Backend deploys but health check fails | Go to Render Dashboard → healthcare-backend → "Manual Deploy" → "Deploy from parent" → select previous successful deploy |
| Frontend deploys but shows errors | Same as above for healthcare-frontend |
| Both fail | `git revert HEAD && git push` to rollback to `8d6cc56`. Then re-deploy via Blueprint |
| Data corruption | Restore from Neon backup (point-in-time recovery). ChromaDB rebuilds from PostgreSQL per ADR-028 |

---

## 8. Verification Checklist (Post-Deploy)

- [ ] `GET /health` returns 200 + `{"status": "healthy"}`
- [ ] `GET /` returns 200 + API welcome message
- [ ] `GET /api/v1/health` returns database diagnostics (14 tables, 55 indexes)
- [ ] `GET /api/v1/monitoring/health` returns DB health = "ok"
- [ ] `GET /ready` returns `"status": "ready"` (may show "not_ready" if graph bootstrap or vector recovery is still warming up)
- [ ] `GET /docs` loads Swagger UI
- [ ] Frontend `GET /` returns Next.js HTML (200)
- [ ] Frontend loads without CORS errors (check browser console)
- [ ] Login endpoint `POST /api/v1/auth/login` responds (may fail auth but should not 500)
- [ ] Logs show no ERROR-level messages after startup
- [ ] Neon DB shows 14 tables, 5 alembic migrations applied
- [ ] Free tier: confirm service spins down after 15 min idle, wakes on first request

---

## 9. Post-Deploy Monitoring

Monitor these metrics in the first 24 hours:

1. **Health check success rate** — Render automatically checks every 5 seconds
2. **Response times** — Free tier cold starts: 30-60s. Warm: <500ms
3. **Gemini API usage** — Free tier: 60 requests/minute. Monitor via Gemini API dashboard
4. **Neon DB connections** — Free tier: 10 simultaneous connections. Pool is configured for 10
5. **Disk usage** — 1 GB shared between uploads, documents. Check if nearing capacity
6. **Memory** — Free tier: 512 MB RAM. ChromaDB + LangGraph + OCR may be memory-intensive
