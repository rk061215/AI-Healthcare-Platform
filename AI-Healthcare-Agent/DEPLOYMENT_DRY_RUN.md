# Deployment Dry Run

**Simulated deployment of v1.0.0 to production.**
**Targets:** Render (backend) + Vercel (frontend)

---

## Step 1: Pre-Deployment Verification

| # | Action | Expected | Failure Point | Risk |
|---|--------|----------|--------------|------|
| 1.1 | Verify Git tag exists | `git tag -l v1.0.0` returns tag | Tag not pushed | Low |
| 1.2 | Verify commit hash | `git rev-parse HEAD` matches remote | Diverged branches | Low |
| 1.3 | Verify LICENSE exists | `test -f LICENSE` | File missing | Low |
| 1.4 | Verify version strings | `grep -r "0.8.0" --include="*.py"` returns nothing | Missed version | ✅ Fixed |
| 1.5 | Run backend tests | `pytest -v --tb=short` | Test failures | Medium |
| 1.6 | Run frontend tests | `npm run test:run` | Test failures | Medium |
| 1.7 | Build backend Docker | `docker build -t backend-test backend/` | Build failure | Medium |
| 1.8 | Build frontend Docker | `docker build --target production frontend/` | Build failure | Medium |

---

## Step 2: Database Provisioning

| # | Action | Expected | Failure Point | Risk |
|---|--------|----------|--------------|------|
| 2.1 | Create PostgreSQL instance | Render creates `healthcare-db` | Free plan limit reached | Low |
| 2.2 | Enable UUID extension | `CREATE EXTENSION "uuid-ossp"` in init.sql | Extension not available | Low |
| 2.3 | Get connection string | Render provides `DATABASE_URL` | Manual step | Low |
| 2.4 | Set connection string in env | `DATABASE_URL` configured in Render | Typo in URL | Low |
| 2.5 | Run migrations | `alembic upgrade head` | **No pre-deploy command configured** | 🔴 **HIGH** |

**🔴 Blocker:** Render has no pre-deploy migration hook. Must run `alembic upgrade head` manually via Render Shell.

---

## Step 3: Environment Configuration

| # | Action | Expected | Failure Point | Risk |
|---|--------|----------|--------------|------|
| 3.1 | Set `JWT_SECRET_KEY` | Strong random 32-byte hex | Default insecure key used | 🔴 **HIGH** |
| 3.2 | Set `GEMINI_API_KEY` | Valid Gemini API key | Key missing or expired | 🔴 **HIGH** |
| 3.3 | Set `BACKEND_CORS_ORIGINS` | `https://healthcare-frontend.onrender.com` | Wrong domain | Medium |
| 3.4 | Set `NEXT_PUBLIC_API_URL` | `https://healthcare-backend.onrender.com/api/v1` | Wrong URL | Medium |
| 3.5 | Set `ENVIRONMENT=production` | Production mode | Left as development | Medium |
| 3.6 | Set `DEBUG=false` | No debug output | Left as true | Low |
| 3.7 | Set `LOG_LEVEL=INFO` or `WARNING` | Proper log verbosity | Left as DEBUG | Low |

**⚠️ Render free tier sleeps after 15 minutes.** API calls after idle period take 5–10s to wake. Set `RATE_LIMIT_PER_MINUTE=120` to account for sleep retries (already configured in render.yaml).

---

## Step 4: Backend Deployment (Render)

| # | Action | Expected | Failure Point | Risk |
|---|--------|----------|--------------|------|
| 4.1 | Push code to GitHub | `main` branch updated | Push rejected | Low |
| 4.2 | Render auto-deploy triggers | Build starts in Render dashboard | Webhook not configured | Low |
| 4.3 | Docker build starts | `backend/Dockerfile` used | **Missing Tesseract** | ⚠️ **Medium** |
| 4.4 | Docker build completes | Image pushed to Render registry | Build timeout (free: 15 min) | Medium |
| 4.5 | Service starts | `uvicorn app.main:app --host 0.0.0.0 --port 8000` | Startup failure | Medium |
| 4.6 | Health check passes | `/health` returns 200 | ChromaDB not running | 🔴 **HIGH** |
| 4.7 | Readiness check | `/ready` returns "ready" | Multiple services fail | Medium |

**🔴 Blocker:** ChromaDB is not deployed on Render. The `/ready` endpoint checks ChromaDB, vector store, and retriever — all will fail without ChromaDB.

---

## Step 5: Frontend Deployment (Vercel)

| # | Action | Expected | Failure Point | Risk |
|---|--------|----------|--------------|------|
| 5.1 | Vercel import from GitHub | Repo connected | Permission denied | Low |
| 5.2 | Build command runs | `npm run build` | Build errors | Low |
| 5.3 | Output directory | `.next` | Standalone config missing | ⚠️ Medium |
| 5.4 | Vercel sets `NEXT_PUBLIC_*` vars | Env vars injected at build time | Wrong domain | Medium |
| 5.5 | Deploy completes | Vercel provides URL | Free plan limit | Low |
| 5.6 | Home page loads | `GET /` returns 200 | Next.js render error | Low |
| 5.7 | API proxy works | `GET /api/health` proxies to Render | Vercel → Render connection | Medium |
| 5.8 | Login page loads | Auth UI renders | CORS / cookie issues | Medium |

---

## Step 6: Post-Deployment Verification

| # | Action | Expected | Failure Point | Risk |
|---|--------|----------|--------------|------|
| 6.1 | `curl https://healthcare-backend.onrender.com/health` | `{"status":"healthy","version":"1.0.0"}` | Service not running | 🔴 |
| 6.2 | `curl https://healthcare-backend.onrender.com/ready` | `{"status":"ready"}` | ChromaDB/Vector service | 🔴 |
| 6.3 | `curl https://healthcare-backend.onrender.com/live` | `{"status":"alive"}` | Process dead | 🔴 |
| 6.4 | Visit `https://healthcare-frontend.vercel.app` | Page loads | Vercel error | Medium |
| 6.5 | Try demo login | Demo mode works | Auth flow broken | Medium |
| 6.6 | Upload a document | OCR processes | Tesseract missing | Medium |
| 6.7 | Send a chat message | AI responds | Gemini key / ChromaDB | Medium |

---

## Step 7: Failure Points Summary

### 🔴 Critical (Must Fix Before Deploy)

| # | Issue | Impact |
|---|-------|--------|
| FP-1 | **ChromaDB not deployed** | RAG pipeline, vector search, context builder all fail |
| FP-2 | **No pre-deploy migration** | `alembic upgrade head` must be run manually on Render |
| FP-3 | **Missing Tesseract in Docker** | OCR processing will fail on Docker/Render |
| FP-4 | **Secrets not set** | `JWT_SECRET_KEY` and `GEMINI_API_KEY` must be manually configured |

### ⚠️ High (Must Fix Soon)

| # | Issue | Impact |
|---|-------|--------|
| FP-5 | **Duplicate route registration** | `monitoring.py` registers same `/health`, `/ready`, `/live` — may cause undefined behavior |
| FP-6 | **Render free tier sleep** | 15-min inactivity sleep — wake time 5–10s |
| FP-7 | **CORS origin hardcoded in render.yaml** | `BACKEND_CORS_ORIGINS: https://healthcare-frontend.onrender.com` — future custom domains need update |
| FP-8 | **Vercel API proxy uses Render URL** | Hardcoded `destination: https://healthcare-backend.onrender.com...` — must update if URL changes |

### 🟡 Medium

| # | Issue | Impact |
|---|-------|--------|
| FP-9 | **No SSL in Nginx config** | TLS config is commented placeholder |
| FP-10 | **ChromaDB port mismatch** | `.env.example`: 8001, `render.yaml`: 8000 |
| FP-11 | **No Content-Security-Policy** | Missing in Vercel and Nginx headers |
| FP-12 | **CSPF default JWT secret** | Warning issued but default could slip into production |
| FP-13 | **No async migration support** | Alembic uses sync SQLAlchemy only |

### 🟢 Low

| # | Issue | Impact |
|---|-------|--------|
| FP-14 | **No log rotation** | Logs grow unbounded in Docker |
| FP-15 | **No pool pre-ping** | Stale DB connections possible |
| FP-16 | **No connection timeout** | Backend could hang on DB failure |
| FP-17 | **Vercel CORS headers are open** | `Access-Control-Allow-Origin: *` on API proxy |

---

## Step 8: Successful Deployment Flow (Ideal)

```
pre-checks ✅ → DB provisioned ✅ → env vars set ✅ → 
  Render build (⚠️ tesseract missing) → Render deploy → 
  manual migration (🔴 blocker: no CI step) → 
  manual ChromaDB setup (🔴 blocker) → 
  Vercel deploy → post-deploy checks → live!
```

**Estimated time to resolve blockers:** 2–4 hours

---

## Step 9: Rollback Plan

If deployment fails, rollback is straightforward:

```bash
# Render — redeploy previous version
render deploy healthcare-backend --commit <previous-hash>

# Vercel — promote previous deployment
vercel rollback healthcare-frontend

# Database — downgrade migrations if needed
alembic downgrade -1
```
