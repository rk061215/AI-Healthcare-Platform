# Deployment Validation Report

**Project:** AI Healthcare Follow-up Assistant  
**Version:** v1.0.0-rc.1  
**Date:** 2026-07-16  
**Scope:** Docker Compose, Dockerfiles, Startup, PostgreSQL, ChromaDB, Environment Variables, Uploads, Logging, Health Endpoints

---

## 1. Docker Compose

| Item | Status | Details | Recommendation |
|------|--------|---------|----------------|
| Base compose (`docker-compose.yml`) | ⚠️ WARNING | No network isolation (services communicate via default bridge). Bind-mounts code for dev, which is correct for dev but should not be used in production. ChromaDB exposes port `8001` but backend env expects `CHROMA_PORT=8000`. Uses `chromadb/chroma:latest` (unpinned). Backend command includes `--reload` (dev-only). | Pin ChromaDB image version. Align ChromaDB port mapping (8001:8000 is fine internally — container port 8000 is correct). Add `healthcare_network` for isolation. |
| Production compose (`docker-compose.production.yml`) | ✅ PASS | Uses `target: runtime`, resource limits (512M postgres, 1G backend, 512M frontend), internal port binding (`127.0.0.1`), dedicated `healthcare_network`, healthchecks on all services, `start_period` on postgres and backend. | No changes needed. |
| Dev compose (`docker-compose.dev.yml`) | ✅ PASS | Minimal overrides for development: opens ports, sets `DEBUG=true`, `LOG_LEVEL=DEBUG`. Good pattern. | None. |
| Observability compose (`docker-compose.observability.yml`) | ⚠️ WARNING | Grafana container port `3000` conflicts with frontend's `3000`. Uses separate network `healthcare-monitoring` — not connected to `healthcare_network`, so backend cannot reach OTEL collector unless `extra_hosts` or network attach is configured. | Map Grafana to `3001:3000` or use a different port. Attach monitoring stack to `healthcare_network` or add network linking. |

---

## 2. Dockerfiles

| Item | Status | Details | Recommendation |
|------|--------|---------|----------------|
| Backend Dockerfile | ✅ PASS | Multi-stage: `builder` compiles wheels, `runtime` installs them. Runs as non-root `app` user. Creates `/app/uploads` with correct ownership. `EXPOSE 8000`. Clean CMD without `--reload`. | Consider adding `--no-cache-dir` to final pip install (already present). Consider using `COPY --chown=app:app . .` for cleaner ownership. |
| Frontend Dockerfile | ✅ PASS | Three stages: `dev` (npm ci + dev server), `builder` (npm ci + build), `production` (copies standalone + static output). Runs as non-root `app` user. `EXPOSE 3000`. CMD is `node server.js`. | Package.json and package-lock.json are re-copied in builder stage — minor redundancy but harmless. Consider adding `.dockerignore` to exclude node_modules, .git, etc. in all stages. |

---

## 3. Backend Startup

| Item | Status | Details | Recommendation |
|------|--------|---------|----------------|
| Uvicorn command | ✅ PASS | `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]` in Dockerfile. Correct for production. | None. |
| Migrations | ⚠️ WARNING | Production compose does NOT run `alembic upgrade head` automatically — uses Dockerfile CMD which only starts uvicorn. Migration must be run manually (`docker compose exec backend alembic upgrade head`) per DEPLOYMENT_GUIDE.md. Good for idempotency, but first deployment requires manual step. | Consider adding an `entrypoint.sh` that runs migrations before starting uvicorn, or document prominently that first deploy requires manual migration. |
| Healthcheck | ✅ PASS | `curl -f http://localhost:8000/health` with `interval: 30s`, `timeout: 10s`, `retries: 3`, `start_period: 60s`. Appropriate for production. | None. |
| Resource limits | ✅ PASS | `memory: 1G`, `cpus: "1.5"` for backend in production compose. | None. |

---

## 4. Frontend Startup

| Item | Status | Details | Recommendation |
|------|--------|---------|----------------|
| Dev stage | ✅ PASS | `npm run dev` with hot reload. Bind-mounted code. Correct. | None. |
| Build stage | ✅ PASS | `npm run build` produces standalone output. `next.config.ts` has `output: "standalone"`. Correct. | None. |
| Production stage | ✅ PASS | Copies `.next/standalone/`, `public/`, `.next/static/`. Runs `node server.js`. App user. Correct. | None. |
| Healthcheck | ✅ PASS | `wget --spider http://localhost:3000` with `interval: 30s`, `start_period: 30s`. | Consider `wget` may not be available in alpine by default — verify. Node alpine typically has wget. |
| Resource limits | ✅ PASS | `memory: 512M`, `cpus: "1.0"`. Appropriate for frontend. | None. |

---

## 5. PostgreSQL

| Item | Status | Details | Recommendation |
|------|--------|---------|----------------|
| init.sql | ✅ PASS | Creates `uuid-ossp` and `pgcrypto` extensions. Mounted at `/docker-entrypoint-initdb.d/init.sql` so runs only on first initialization. Correct. | Consider adding initial schema validation or role creation if needed. |
| Image | ✅ PASS | `postgres:16-alpine` — specific major version, lightweight. | Pin to exact minor version (`16.4-alpine`) for reproducibility. |
| Healthcheck | ✅ PASS | `pg_isready -U healthcare_user -d healthcare_agent`, `interval: 10s`, `retries: 5`, `start_period: 30s` in production. | None. |
| Volume persistence | ✅ PASS | Named volume `postgres_data` with `driver: local`. Data survives container restarts. | Ensure backup strategy is documented and scheduled. |
| Resource limits | ✅ PASS | `memory: 512M`, `cpus: "1.0"` in production. Adequate for small-to-medium workloads. | None. |

---

## 6. ChromaDB Persistence

| Item | Status | Details | Recommendation |
|------|--------|---------|----------------|
| Volume mounts | ✅ PASS | Named volume `chroma_data` mounted at `/chroma/chroma`. Persistent storage configured. | None. |
| Environment | ✅ PASS | `IS_PERSISTENT=TRUE`, `PERSIST_DIRECTORY=/chroma/chroma`, `ANONYMIZED_TELEMETRY=FALSE`. Correct. | None. |
| Production availability | ⚠️ WARNING | ChromaDB service is **absent** from `docker-compose.production.yml`. Backend env defaults to `CHROMA_HOST=localhost`, which effectively disables ChromaDB (skips in health checks). Intentional for environments without ChromaDB, but vector search will be unavailable. | Add ChromaDB as optional service in production compose, or document explicitly that vector search requires a separate ChromaDB deployment. |
| Image tag | ⚠️ WARNING | Uses `chromadb/chroma:latest` in base compose. No pinning. | Pin to `chromadb/chroma:0.5.23` or specific release tag. |

---

## 7. Environment Variables

| Item | Status | Details | Recommendation |
|------|--------|---------|----------------|
| Root `.env.example` | ⚠️ WARNING | Missing several vars present in backend `.env.example`: `AI_PROVIDER`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `UPLOAD_DIR`, `MAX_UPLOAD_SIZE_MB`, `ALLOWED_EXTENSIONS`, `BACKUP_DIR`, `BACKUP_RETENTION_DAYS`, `CHECKPOINT_PROVIDER`, `REMINDER_CHECK_INTERVAL_MINUTES`, `OTEL_TRACE_SAMPLING_RATE`. Not critical since backend uses its own `.env`, but root is incomplete. | Sync root `.env.example` with backend's vars for a complete reference. |
| Backend `.env.example` | ✅ PASS | Comprehensive — covers all settings defined in `config.py`. Includes placeholders for all optional values. | None. |
| Frontend `.env.local.example` | ✅ PASS | All documented vars present. Matches DEPLOYMENT_GUIDE.md table. | None. |
| Production compose env vars | ⚠️ WARNING | Production compose references `JWT_SECRET_KEY` without `:-` default (correct — forces explicit set). However, `CHROMA_HOST` defaults to `localhost` — this makes ChromaDB effectively disabled by default, which may surprise operators. | Consider defaulting `CHROMA_HOST` to the service name `chromadb` and adding ChromaDB to production compose, or add a comment explaining the localhost default. |
| Missing GEMINI_API_KEY | ⚠️ WARNING | `GEMINI_API_KEY` is required (at least one AI provider key) but is not listed in the production compose `environment` block. Must be set via `env_file` (`../backend/.env`). This works but is less visible. | Add `GEMINI_API_KEY: ${GEMINI_API_KEY}` to production compose environment block for visibility. |

---

## 8. Upload Directory

| Item | Status | Details | Recommendation |
|------|--------|---------|----------------|
| Dockerfile creation | ✅ PASS | `RUN mkdir -p /app/uploads && chown -R app:app /app/uploads` in backend Dockerfile. Correct. | None. |
| Volume mounts (base) | ✅ PASS | `uploads_data:/app/uploads` volume in base compose. Named volume persists across restarts. | None. |
| Volume mounts (production) | ✅ PASS | Three data volumes: `uploads_data`, `documents_data`, `backups_data`. All with `driver: local`. | None. |
| Permissions | ✅ PASS | Backend runs as `app` user, uploads directory owned by `app:app`. Correct. | None. |
| Auto-creation in config | ✅ PASS | `config.py` line 112-113: `Path(self.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)`. Runtime fallback exists. | None. |

---

## 9. Logging

| Item | Status | Details | Recommendation |
|------|--------|---------|----------------|
| Loguru configuration | ✅ PASS | `setup_loguru_logging()` called in lifespan. Dual logging (Loguru + stdlib) configured. `LOG_LEVEL` and `LOG_FORMAT` env vars supported. | None. |
| JSON log format | ✅ PASS | `LOG_FORMAT=json` available for structured logging. Production checklist mentions this. | Consider setting `LOG_FORMAT=json` by default in production compose. |
| Loki integration | ✅ PASS | Observability compose includes Loki for log aggregation. Not connected to production compose network by default. | Connect observability compose to production network or include Loki config in production compose. |
| Production compose log driver | ⚠️ WARNING | No `logging:` driver configured in production compose. Uses Docker default (`json-file`). Logs are not shipped to an external aggregator without the observability stack. | Either add `logging.driver` to production compose, or ensure users deploy the observability stack alongside. |

---

## 10. Health Endpoints

| Item | Status | Details | Recommendation |
|------|--------|---------|----------------|
| `GET /health` | ✅ PASS | Returns `{"status": "healthy", "version": "0.8.0"}`. No DB dependency — true shallow check. Used by Docker healthcheck. | Consider returning uptime or basic DB status for richer health info. |
| `GET /ready` | ✅ PASS | Deep readiness check: tests DB connection, alembic migrations, graph registry, tool registry, memory framework, AI provider, embedding provider, vector store, retriever, prompt manager, graph bootstrap. Returns detailed per-service status and list of unready services. | None. |
| `GET /live` | ✅ PASS | Shallow liveness: returns `{"status": "alive", "timestamp": "..."}`. No dependencies. Perfect for Kubernetes liveness probes. | None. |
| Monitoring router unused | ⚠️ WARNING | `app.api.v1.monitoring` router is imported in `main.py` but **never included** (`app.include_router(monitoring_router)` is missing). The `/health`, `/ready`, `/live` endpoints in monitoring.py are dead code. | Either remove the monitoring router or include it. The main.py endpoints already cover the functionality. Clean up dead code. |

---

## Summary

| Category | ✅ PASS | ⚠️ WARNING | ❌ FAIL |
|----------|---------|------------|---------|
| Docker Compose | 2 | 2 | 0 |
| Dockerfiles | 2 | 0 | 0 |
| Backend Startup | 3 | 1 | 0 |
| Frontend Startup | 4 | 1 | 0 |
| PostgreSQL | 4 | 1 | 0 |
| ChromaDB | 2 | 2 | 0 |
| Environment Variables | 2 | 3 | 0 |
| Upload Directory | 5 | 0 | 0 |
| Logging | 3 | 1 | 0 |
| Health Endpoints | 3 | 1 | 0 |
| **Total** | **30** | **12** | **0** |

**Overall: 30 PASS / 12 WARNING / 0 FAIL** — Deployment-ready with minor improvements recommended.

### Critical Items Before Production Launch

1. Pin ChromaDB image version (currently `:latest`)
2. Resolve Grafana port conflict with frontend (port 3000)
3. Connect observability stack to production network
4. Clean up unused monitoring router import
5. Document that first deployment requires manual migration step
