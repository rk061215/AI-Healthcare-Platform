# CORS Audit

## Symptom
OPTIONS preflight requests to `https://healthcare-backend-yybp.onrender.com/api/v1/auth/register/patient` return **400 Bad Request** instead of 200 with CORS headers. This blocks browser-based frontend registration.

## Root Cause

**Missing CORS origin**: `render.yaml` line 28 sets `BACKEND_CORS_ORIGINS` to only `https://healthcare-frontend.onrender.com` (the old Render frontend). The actual frontend is deployed on Vercel at:
```
https://ai-healthcare-platform-deploy-initial-2456jmy3b.vercel.app
```

Starlette's `CORSMiddleware` returns **400** for preflight OPTIONS requests when the `Origin` header is not in `allow_origins` (see Starlette `CORSMiddleware._preflight_response()` — returns `PlainTextResponse("", status_code=400)` for disallowed origins).

## Investigation Details

### Middleware Stack (outermost → innermost)
```
SecurityHeadersMiddleware  → adds security headers to response
RateLimitMiddleware        → skips OPTIONS (not in {POST,PUT,PATCH,DELETE})
CSRFTokenMiddleware        → skips OPTIONS (bypasses Origin/Referer validation)
MetricsMiddleware          → records metrics, does not reject
TracingMiddleware          → creates trace span, does not reject
RequestIDMiddleware        → adds request ID, does not reject
CORSMiddleware             → handles preflight; returns 400 if Origin not in allow_origins
```

### What was ruled out
- **CSRF middleware**: correctly bypasses OPTIONS (`if request.method in {"GET", "HEAD", "OPTIONS"}: return await call_next(request)`)
- **Rate limiter**: correctly bypasses OPTIONS (only acts on POST/PUT/PATCH/DELETE)
- **Request validation**: no middleware or endpoint dependency parses the request body for OPTIONS
- **Router prefix mismatch**: OPTIONS hits `/api/v1/auth/register/patient` which matches the registered route

## Fix

`render.yaml` — add Vercel frontend URL to `BACKEND_CORS_ORIGINS`:

```diff
- https://healthcare-frontend.onrender.com
+ https://healthcare-frontend.onrender.com,https://ai-healthcare-platform-deploy-initial-2456jmy3b.vercel.app
```

After redeployment, the backend will accept preflights from the Vercel origin.

## Verification

```bash
curl -s -o /dev/null -w "%{http_code}" -X OPTIONS \
  -H "Origin: https://ai-healthcare-platform-deploy-initial-2456jmy3b.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  https://healthcare-backend-yybp.onrender.com/api/v1/auth/register/patient
```

Expected: **200**
Before fix: **400**

## Files Examined
- `backend/app/middleware/cors.py` — `setup_cors()` uses `settings.cors_origins`
- `backend/app/core/config.py:98-99` — `cors_origins` property splits `BACKEND_CORS_ORIGINS` env var
- `backend/app/middleware/csrf.py:54` — OPTIONS bypass confirmed
- `backend/app/middleware/rate_limit.py:154` — OPTIONS bypass confirmed
- `backend/app/middleware/metrics.py` — no request rejection
- `backend/app/middleware/tracing.py` — no request rejection
- `backend/app/middleware/request_id.py` — no request rejection
- `backend/app/middleware/security.py` — modifies response only
- `backend/app/main.py:112-126` — middleware ordering
- `render.yaml:28` — **the fix location**
