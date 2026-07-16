# Deployment Hardening Report

**Project:** AI Healthcare Follow-up Assistant  
**Version:** v1.0.0-rc.1  
**Date:** 2026-07-16  

---

## 1. Docker Image Version Pinning

All mutable tags (`:latest`, `:slim`, `:alpine`) have been replaced with specific patch versions to ensure reproducible builds.

| File | Image | Old Tag | New Tag |
|---|---|---|---|
| `docker/docker-compose.yml` | `chromadb/chroma` | `latest` | `0.5.23` |
| `backend/Dockerfile` (builder) | `python` | `3.12-slim` | `3.12.9-slim` |
| `backend/Dockerfile` (runtime) | `python` | `3.12-slim` | `3.12.9-slim` |
| `frontend/Dockerfile` (dev) | `node` | `20-alpine` | `20.18-alpine` |
| `frontend/Dockerfile` (builder) | `node` | `20-alpine` | `20.18-alpine` |
| `frontend/Dockerfile` (production) | `node` | `20-alpine` | `20.18-alpine` |

**Already pinned (no change needed):**
- `postgres:16-alpine` in `docker-compose.yml` and `docker-compose.production.yml`

---

## 2. Docker Compose Security Review

### `docker-compose.yml` (base)

| Check | Status | Notes |
|---|---|---|
| Image tags pinned | ✅ | ChromaDB now pinned to `0.5.23`; Postgres already `16-alpine` |
| Container names set | ✅ | Explicit `container_name` for all services |
| Restart policy | ✅ | `unless-stopped` on all services |
| Healthchecks | ⚠️ | Postgres has healthcheck; ChromaDB and backend do **not** |
| Read-only root filesystem | ❌ | Not configured; volumes mount writable |
| No privileged mode | ✅ | Not used |
| No host network mode | ✅ | Default bridge network |
| env_file used | ✅ | Secrets via `.env` files (not hardcoded) |
| Volume drivers | ✅ | Named volumes for persistence |

**Recommendations:**
- Add healthchecks for ChromaDB and backend services
- Consider `read_only: true` for non-writer containers
- Remove `version: "3.9"` (deprecated in newer Compose)

### `docker-compose.production.yml`

| Check | Status | Notes |
|---|---|---|
| Localhost-only port binding | ✅ | `127.0.0.1:...` used on all exposed ports |
| Resource limits | ✅ | CPU and memory limits defined per service |
| Healthchecks | ✅ | Present on backend and frontend |
| Network isolation | ✅ | Dedicated `healthcare_network` bridge |
| No dev volumes mounted | ✅ | Production compose does not bind-mount source code |
| Start period on healthchecks | ✅ | `start_period` set on all checks |
| No debug mode | ✅ | `DEBUG: "false"` explicitly set |

### `docker-compose.dev.yml`

Appropriate for development — exposes ports publicly, enables debug, bind-mounts source code. No changes needed.

---

## 3. render.yaml Review

| Check | Status | Notes |
|---|---|---|
| Dockerfile path correct | ✅ | `backend/Dockerfile` and `frontend/Dockerfile` |
| Health check path set | ✅ | `/health` for backend, `/` for frontend |
| Free plan | ⚠️ | Both services on `free` plan — no auto-scaling, sleeps after inactivity |
| Secrets sync | ⚠️ | `JWT_SECRET_KEY` and `GEMINI_API_KEY` marked `sync: false` (manual entry) |
| Persistent disks | ✅ | Uploads, documents disks defined (1 GB each) |
| Database reference | ✅ | `DATABASE_URL` sourced from `healthcare-db` |
| Frontend uses Node env | ✅ | Correct — Next.js standalone needs Node server, not static |

**Recommendations:**
- Upgrade from `free` to `starter` (or higher) for production to avoid service sleep
- Consider adding `autoDeploy: true` or branch filtering
- Add `healthCheckPath: /` to frontend (already done)
- Set `numInstances: 1` explicitly for baseline availability

---

## 4. vercel.json Review

| Check | Status | Notes |
|---|---|---|
| Framework set | ✅ | `nextjs` |
| Security headers | ✅ | `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy` |
| CORS headers for `/api/*` | ✅ | Open CORS for API routes |
| Clean URLs | ✅ | `cleanUrls: true` |
| No trailing slashes | ✅ | `trailingSlash: false` |
| API rewrite | ✅ | Proxies `/api/*` to Render backend |
| Region set | ✅ | `iad1` (US East) |

**Recommendations:**
- Add `Content-Security-Policy` header
- Add `Strict-Transport-Security` header for HTTPS enforcement
- Restrict `Access-Control-Allow-Origin` from wildcard (`*`) to specific domain in production
- Add a `404` rewrite fallback

---

## 5. Remaining Recommendations

### Critical
- [ ] **Replace default JWT secret** (`change-me-to-a-random-secret-key`) before production deploy — warn is already emitted in `config.py:182-187`
- [ ] **Set `JWT_SECRET_KEY`** as a Render secret (currently `sync: false`) or CI/CD pipeline variable
- [ ] **Set `GEMINI_API_KEY`** as a Render secret (currently `sync: false`)

### High Priority
- [ ] **Add rate limiting Redis URL** in production — `REDIS_URL` is currently empty, falling back to in-memory (lost on restart)
- [ ] **Enforce HTTPS** at the reverse proxy / load balancer level
- [ ] **Add `Content-Security-Policy`** header to Vercel config
- [ ] **Add `Strict-Transport-Security`** header (max-age=31536000; includeSubDomains)

### Medium Priority
- [ ] Pin frontend `node` version in `.nvmrc` or `engines` field of `package.json`
- [ ] Add `docker-compose.production.yml` healthcheck for ChromaDB
- [ ] Set `read_only: true` on application containers where possible
- [ ] Add container `restart: always` for critical services (Postgres, backend)
- [ ] Configure log rotation for Docker containers
- [ ] Set `PROMETHEUS_MULTIPROC_DIR` to a writable, ephemeral location in production

### Low Priority
- [ ] Remove deprecated `version: "3.9"` from Compose files
- [ ] Add `.dockerignore` files to reduce build context size
- [ ] Consider multi-arch builds for ARM deployment
- [ ] Add `npm audit` / `pip audit` step to CI pipeline
- [ ] Enable Docker Content Trust (`DOCKER_CONTENT_TRUST=1`) for image verification
