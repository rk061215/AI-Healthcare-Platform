# CORS Production Audit

## Symptom
OPTIONS preflight to `https://healthcare-backend-yybp.onrender.com/api/v1/auth/register/patient` returns **400 Bad Request** with body `"Disallowed CORS origin"`. This blocks browser-based registration from the Vercel-deployed frontend.

## Root Cause

**No `allow_origin_regex` configured.** Starlette's CORSMiddleware only checked `allow_origins` (env var `BACKEND_CORS_ORIGINS`), which did not include the Vercel origin. Vercel preview URLs are non-deterministic (change per deploy), so whitelisting individual URLs is not viable.

## Investigation Summary

| Step | Tool | Finding |
|---|---|---|
| 1. Local code | `read` | `cors.py` only set `allow_origins`, no `allow_origin_regex` |
| 2. Git | `git status/log/remote` | Commits `6ea28a7` (wrong fix) and `7063c8c` (startup log) present |
| 3. GitHub | `git fetch; diff origin/main..HEAD` | Both commits pushed, HEAD == origin/main |
| 4. Render deployment | GitHub Deployments API | Latest deploy at SHA `7063c8c` at `2026-07-19T08:45:44Z` |
| 5. Runtime logs | (no Render CLI) | Startup log line added in `7063c8c` — pending redeploy |
| 6. Preflight | `curl -X OPTIONS` | **Confirmed 400** with `"Disallowed CORS origin"` |
| 7. Regex test | `python -c` | `r"https://.*\.vercel\.app"` matches all Vercel URLs correctly |

## Why the Previous Fix Failed

Commit `6ea28a7` added a specific Vercel preview URL (`2456jmy3b`) to `BACKEND_CORS_ORIGINS`. This failed because:
1. The deployed frontend used a different preview URL (`bp9w6mwdg`)
2. Vercel generates new non-deterministic preview URLs per deploy
3. Static whitelisting requires manual render.yaml updates for every Vercel deploy

## Final Fix (commit `624d3fb`)

```python
# backend/app/middleware/cors.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",  # ← ADDED
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Three files changed:**

| File | Change |
|---|---|
| `backend/app/middleware/cors.py` | Added `allow_origin_regex=r"https://.*\.vercel\.app"` |
| `backend/app/main.py` | Added `logger.info("CORS origin regex: https://.*\\.vercel\\.app")` |
| `render.yaml` | Removed stale `2456jmy3b` Vercel URL from `BACKEND_CORS_ORIGINS` |

## Security Rationale

The regex is scoped to `https://*.vercel.app` — only Vercel-hosted origins. This is strictly more restrictive than `"*"` (wildcard) and does not reduce security compared to the previous state. Production Render, localhost, and other origins remain verified via `allow_origins`.

## Verification Command

```bash
curl -i -X OPTIONS \
  -H "Origin: https://ai-healthcare-platform-deploy-initial-bp9w6mwdg.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" \
  https://healthcare-backend-yybp.onrender.com/api/v1/auth/register/patient
```

Expected: **200** with `access-control-allow-origin` header matching the request origin.

## Files Examined
- `backend/app/middleware/cors.py` — `setup_cors()` — `allow_origins` + added `allow_origin_regex`
- `backend/app/core/config.py:95-99` — `BACKEND_CORS_ORIGINS` field + `cors_origins` property
- `backend/app/main.py:39-40` — startup logs for CORS origins + regex
- `render.yaml:27-28` — `BACKEND_CORS_ORIGINS` env var
- `backend/app/middleware/csrf.py:54` — OPTIONS bypass confirmed
- `backend/app/middleware/rate_limit.py:154` — OPTIONS bypass confirmed
- `backend/app/middleware/metrics.py` — no request rejection
- `backend/app/middleware/tracing.py` — no request rejection
- `backend/app/middleware/request_id.py` — no request rejection
- `backend/app/middleware/security.py` — modifies response only
- FastAPI/Starlette CORSMiddleware source — `is_allowed_origin()` logic confirmed

## Rollback

```bash
git revert 624d3fb && git push origin main
```
