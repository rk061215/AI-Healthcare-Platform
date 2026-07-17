# Deployment Audit — Final

**Date:** 2026-07-16
**Target:** v1.0.0 public release

---

## 1. Dockerfile (Backend)

| Check | Status | Notes |
|-------|--------|-------|
| Multi-stage build | ✅ | `builder` + `runtime` stages |
| Pin base image versions | ✅ | `python:3.12.9-slim` |
| Install system deps | ✅ | `libpq-dev` |
| Create non-root user | ✅ | `adduser --system --group app` |
| Set `PYTHONPATH` | ✅ | `/app` |
| Expose correct port | ✅ | `8000` |
| CMD uses uvicorn | ✅ | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| Build cache wheels | ✅ | `pip wheel --no-cache-dir --no-deps` |
| Upload dir created | ✅ | `/app/uploads`, chowned to `app:app` |
| **Missing: tesseract** | ⚠️ | Tesseract OCR binary not installed in Docker image |

**Rating:** 8/10 — Missing tesseract-ocr installation.

---

## 2. Dockerfile (Frontend)

| Check | Status | Notes |
|-------|--------|-------|
| Multi-stage build | ✅ | `dev` + `builder` + `production` |
| Pin base image | ✅ | `node:20.18-alpine` |
| Telemetry disabled | ✅ | `NEXT_TELEMETRY_DISABLED=1` |
| Standalone output used | ✅ | Copy from `.next/standalone` |
| Non-root user | ✅ | `adduser --system --group app` |
| Correct CMD | ✅ | `node server.js` |
| **Missing: next.config.js standalone** | ⚠️ | Verify `output: "standalone"` is set in next.config |

**Rating:** 9/10 — Verified standard Next.js production Dockerfile.

---

## 3. docker-compose.yml (Dev)

| Check | Status | Notes |
|-------|--------|-------|
| PostgreSQL | ✅ | `postgres:16-alpine`, healthcheck, persistent volume |
| ChromaDB | ✅ | `chromadb/chroma:0.5.23`, persistent volume, telemetry off |
| Backend | ✅ | Build from `../backend`, env file, depends on healthy postgres |
| Frontend | ✅ | Dev target, volume mounts for hot reload |
| Volumes | ✅ | `postgres_data`, `chroma_data`, `uploads_data` |
| Startup command | ✅ | `alembic upgrade head && uvicorn --reload` |

**Rating:** 10/10

---

## 4. docker-compose.production.yml

| Check | Status | Notes |
|-------|--------|-------|
| PostgreSQL | ✅ | `postgres:16-alpine`, healthcheck, start_period, resource limits |
| Backend | ✅ | Runtime target, healthcheck, resource limits, persistent volumes |
| Frontend | ✅ | Production target, healthcheck, resource limits |
| **ChromaDB missing** | ❌ | No ChromaDB service in production compose — RAG pipeline will fail |
| Nginx missing | ⚠️ | Only `docker run` instructions in nginx.conf, not in compose |
| Resource limits | ✅ | Memory: postgres 512M, backend 1G, frontend 512M |
| Network isolation | ✅ | `healthcare_network` bridge |
| Port binding | ✅ | `127.0.0.1:5432:5432` (localhost only) |
| Startup sequence | ✅ | `alembic upgrade head` in backend, depends_on postgres healthy |
| Volumes | ✅ | postgres_data, uploads_data, documents_data, backups_data |

**Rating:** 7/10 — ChromaDB missing is a blocker for the AI pipeline in production.

---

## 5. render.yaml

| Check | Status | Notes |
|-------|--------|-------|
| Backend service | ✅ | Docker build, health check on `/health`, persistent disks |
| Frontend service | ✅ | Node env, build command, health check on `/` |
| Database | ✅ | Free plan, Oregon region, IP allowlist empty |
| Environment variables | ✅ | 12 backend vars, 7 frontend vars defined |
| Secrets marked | ⚠️ | `JWT_SECRET_KEY` and `GEMINI_API_KEY` use `sync: false` (manual entry) |
| Persistent disks | ✅ | 1GB each for uploads and documents |
| **ChromaDB not defined** | ❌ | No ChromaDB service — vector search will fail on Render |
| **Missing: startup command** | ⚠️ | No pre-deploy command for `alembic upgrade head` |

**Rating:** 6/10 — Missing ChromaDB and migration step.

---

## 6. vercel.json

| Check | Status | Notes |
|-------|--------|-------|
| Framework | ✅ | `nextjs` |
| Build/install commands | ✅ | `npm run build`, `npm ci` |
| Security headers | ✅ | X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy |
| CORS headers for API | ✅ | `Access-Control-Allow-Origin: *` for `/api/:path*` |
| API proxy rewrite | ✅ | `/api/:path*` → `https://healthcare-backend.onrender.com/api/v1/:path*` |
| Clean URLs | ✅ | `cleanUrls: true` |
| **No CSP header** | ⚠️ | Content-Security-Policy not set |
| **Open CORS** | ⚠️ | `Access-Control-Allow-Origin: *` on API routes — relaxes security |

**Rating:** 8/10 — Missing CSP, open CORS on API proxy.

---

## 7. nginx.conf

| Check | Status | Notes |
|-------|--------|-------|
| Security headers | ✅ | X-CTO, X-Frame-Options, XSS-Protection, Referrer-Policy, Permissions-Policy, HSTS |
| Rate limiting | ✅ | `limit_req_zone` for API (30r/s) and login (5r/m) |
| Upstreams | ✅ | Backend (`healthcare-backend:8000`) and Frontend (`healthcare-frontend:3000`) |
| WebSocket proxy | ✅ | `/ws/` with 3600s timeouts |
| Health endpoint proxy | ✅ | `/health`, `/ready`, `/live` |
| API docs proxy | ✅ | `/docs`, `/openapi.json` |
| Static file caching | ✅ | 30d cache, `public, immutable` |
| Hidden file protection | ✅ | `deny all` for dotfiles |
| Max body size | ✅ | `20M` |
| **SSL commented out** | ⚠️ | TLS config is placeholder — requires manual cert setup |
| **HTTP→HTTPS redirect commented** | ⚠️ | No automatic redirect to HTTPS |

**Rating:** 8/10 — SSL/HTTPS not auto-configured.

---

## 8. Health Endpoints

| Endpoint | Status | Notes |
|----------|--------|-------|
| `/health` | ✅ | Returns `{"status": "healthy", "version": "1.0.0"}` |
| `/ready` | ✅ | Checks: DB, migrations, graph registry, tool registry, memory, AI provider, embeddings, vector store, retriever, prompt manager, bootstrap |
| `/live` | ✅ | Simple liveness check |
| **Duplicate routes** | ⚠️ | `monitoring.py` registers same `/health`, `/ready`, `/live` paths — may cause FastAPI conflicts |
| `/metrics` | ✅ | Prometheus metrics snapshot |

**Rating:** 8/10 — Duplicate route registration is a bug to fix.

---

## 9. Environment Variables

| Check | Status | Notes |
|-------|--------|-------|
| `.env.example` comprehensive | ✅ | 135 lines, all categories covered |
| All vars in config.py | ✅ | Settings class mirrors .env.example |
| Secrets | ⚠️ | `JWT_SECRET_KEY` default is `"change-me-to-a-random-secret-key"` — config.py warns on default |
| Production defaults | ⚠️ | `CORS_ORIGINS` defaults to `http://localhost:3000` — must override for production |
| ChromaDB port mismatch | ⚠️ | `.env.example` uses port `8001`, `render.yaml` uses port `8000` |

**Rating:** 8/10 — Port mismatch and insecure defaults noted.

---

## 10. Upload Folders

| Check | Status | Notes |
|-------|--------|-------|
| Upload dir created in Dockerfile | ✅ | `/app/uploads` |
| Persistent volume in compose | ✅ | `uploads_data:/app/uploads` |
| Render persistent disk | ✅ | 1GB mount at `/app/uploads` |
| Documents volume | ✅ | `documents_data:/app/documents` |
| **Path in .env** | ⚠️ | Default `UPLOAD_DIR=./uploads` — relative path may not match Docker mount |

**Rating:** 9/10

---

## 11. Logging

| Check | Status | Notes |
|-------|--------|-------|
| Structured logging via Loguru | ✅ | `setup_logging()` in lifespan |
| Request ID middleware | ✅ | `RequestIDMiddleware` |
| JSON log format option | ✅ | `LOG_FORMAT=json` available |
| **No log rotation** | ⚠️ | No log rotation configured for Docker |

**Rating:** 8/10

---

## 12. Migrations

| Check | Status | Notes |
|-------|--------|-------|
| Alembic configured | ✅ | env.py, 4 migration files |
| Startup migration | ✅ | `alembic upgrade head` in both dev and production compose |
| Readiness check | ✅ | `/ready` verifies `alembic_version` table |
| UUID extension | ✅ | `init.sql` creates `uuid-ossp` and `pgcrypto` |
| **Missing: production Docker CMD** | ⚠️ | Backend Dockerfile CMD doesn't include `alembic upgrade head` — relies on compose override |

**Rating:** 8/10

---

## 13. Security

| Check | Status | Notes |
|-------|--------|-------|
| CORS | ✅ | Configured via `BACKEND_CORS_ORIGINS` env var |
| CSRF | ✅ | `CSRFTokenMiddleware` with tuple-matching origin validation |
| JWT | ✅ | Access + refresh tokens, configurable expiry |
| Rate limiting | ✅ | In-memory and PostgreSQL-backed providers |
| Security headers | ✅ | Via `SecurityHeadersMiddleware` |
| Upload validation | ✅ | Extension whitelist, max size check |
| **Prompt injection** | ⚠️ | No explicit guardrail middleware — relies on RAG guardrails |

**Rating:** 8/10

---

## 14. Deployment Scoring

| Category | Score |
|----------|-------|
| Dockerfile (Backend + Frontend) | 8/10 |
| docker-compose (Dev + Production) | 8/10 |
| Render Configuration | 6/10 |
| Vercel Configuration | 8/10 |
| Nginx Configuration | 8/10 |
| Health Endpoints | 8/10 |
| Environment Variables | 8/10 |
| Upload Folders | 9/10 |
| Logging & Observability | 8/10 |
| Migrations | 8/10 |
| Security | 8/10 |
| **Overall** | **7.9/10** |

## Critical Blocker

**ChromaDB is missing from `docker-compose.production.yml` and `render.yaml`.** Without it, the RAG pipeline (document retrieval, vector search) will fail. This must be resolved before production deployment.

## Recommendations Before Deploy

1. Add ChromaDB service to `docker-compose.production.yml`
2. Add ChromaDB service or external provider to `render.yaml`
3. Add `alembic upgrade head` pre-deploy command to Render
4. Fix duplicate route registration in `monitoring.py`
5. Install `tesseract-ocr` in backend Docker image
6. Configure SSL/HTTPS in Nginx
7. Add Content-Security-Policy to Vercel headers
8. Fix ChromaDB port mismatch (8001 in .env vs 8000 in render.yaml)
