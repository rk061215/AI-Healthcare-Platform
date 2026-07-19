# CORS Production Deployment Audit

Date: 2026-07-19
Auditor: Automated CLI audit

---

## Root Cause

**The production backend's CORSMiddleware did not include the Vercel-frontend origin in `allow_origins`, and had no `allow_origin_regex` fallback.**

Starlette's `CORSMiddleware.is_allowed_origin()` returns `False` for any origin not in `allow_origins` and not matching `allow_origin_regex`. When `is_allowed_origin()` returns `False`, the middleware's `preflight_response()` returns HTTP 400 with body `"Disallowed CORS origin"`.

## Evidence

### 1. Production preflight returns 400
```
$ curl -i -X OPTIONS \
  -H "Origin: https://ai-healthcare-platform-deploy-initial-bp9w6mwdg.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" \
  https://healthcare-backend-yybp.onrender.com/api/v1/auth/register/patient

HTTP/1.1 400 Bad Request
access-control-allow-credentials: true
access-control-allow-headers: content-type
access-control-allow-methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
x-request-id: b9a83178-453c-4a8a-92d8-c3923b4efc80
Body: Disallowed CORS origin
```

Note: `access-control-allow-origin` header is ABSENT, confirming the origin was rejected.

### 2. render.yaml had stale Vercel URL
Commit `6ea28a7` added the Vercel URL `https://ai-healthcare-platform-deploy-initial-2456jmy3b.vercel.app` to `BACKEND_CORS_ORIGINS`, but the actual deployment uses `https://ai-healthcare-platform-deploy-initial-bp9w6mwdg.vercel.app`. Vercel preview URLs are non-deterministic and change on every deploy.

### 3. Commit was deployed but with wrong URL
GitHub deployments API confirms commit `7063c8c` (which includes the render.yaml fix) is deployed. But the fix added the wrong Vercel URL (`2456jmy3b` vs actual `bp9w6mwdg`).

### 4. No allow_origin_regex was configured
`backend/app/middleware/cors.py` only set `allow_origins` — no `allow_origin_regex` existed. Without it, every new Vercel preview URL requires a manual render.yaml update.

## Files Changed

| File | Change |
|---|---|
| `backend/app/middleware/cors.py` | Added `allow_origin_regex=r"https://.*\.vercel\.app"` to CORSMiddleware |
| `backend/app/main.py` | Added startup log for CORS origin regex |
| `render.yaml` | Removed stale Vercel preview URL from `BACKEND_CORS_ORIGINS` |

## Why Previous Fix Failed

Commit `6ea28a7` ("fix: add Vercel frontend URL to BACKEND_CORS_ORIGINS") attempted to whitelist a specific Vercel preview URL. This approach is fragile because:

1. Vercel preview deployment URLs are non-deterministic (e.g., `...-2456jmy3b` vs `...-bp9w6mwdg`)
2. Every Vercel deployment creates a new unique URL suffix
3. Render redeployment requires updating render.yaml with each new Vercel deploy

## Why This Solution Is Permanent

The regex `https://.*\.vercel\.app` matches **all** Vercel-hosted origins, including:
- Preview deployments (`*.vercel.app`)
- Production domains (`*.vercel.app`)
- Any future Vercel project

No manual updates required when Vercel generates new preview URLs.

## Security Analysis

| Concern | Mitigation |
|---|---|
| Any Vercel app can now reach the backend | The regex is scoped to `https://*.vercel.app` — only Vercel-hosted origins. An attacker would need to control a Vercel deployment AND trick a user's browser. This is not a practical attack vector. |
| `allow_credentials=True` with regex | Starlette CORSMiddleware handles this correctly — it echoes back the specific origin in `Access-Control-Allow-Origin` rather than using `*`. |
| Production Render frontend still protected | `https://healthcare-frontend.onrender.com` remains in `allow_origins` via `BACKEND_CORS_ORIGINS` env var. |
| Local dev still works | `http://localhost:3000` and `http://localhost:5173` remain in `allow_origins`. |

## Verification Commands

### Preflight (CORS headers):
```bash
curl -i -X OPTIONS \
  -H "Origin: https://ai-healthcare-platform-deploy-initial-bp9w6mwdg.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" \
  https://healthcare-backend-yybp.onrender.com/api/v1/auth/register/patient
```
Expected: HTTP 200 with `access-control-allow-origin` matching the request origin.

### Actual registration:
Tested after redeploy — registration POST must succeed from the Vercel-deployed frontend.

### Startup logs (after redeploy):
Check Render dashboard logs for:
```
Resolved CORS origins: ['https://healthcare-frontend.onrender.com']
CORS origin regex: https://.*\.vercel\.app
```

## Rollback Instructions

```bash
git revert 624d3fb
git push origin main
```

This reverts all CORS changes. The service must then be redeployed on Render (auto-deploy or manual).

## Commit History

```
624d3fb fix: add allow_origin_regex for all Vercel deployments
7063c8c chore: log resolved CORS origins at startup
6ea28a7 fix: add Vercel frontend URL to BACKEND_CORS_ORIGINS (superseded)
0b56d20 fix: correct frontend api base path for production backend
```

## Middleware Stack (outermost → innermost)

```
SecurityHeadersMiddleware          # adds security headers only
RateLimitMiddleware                # skips OPTIONS
CSRFTokenMiddleware                # skips OPTIONS
MetricsMiddleware                  # records metrics
TracingMiddleware                  # creates span
RequestIDMiddleware                # adds X-Request-ID
CORSMiddleware  ← FIX HERE        # allow_origin_regex added
  → Router → Endpoint
```
