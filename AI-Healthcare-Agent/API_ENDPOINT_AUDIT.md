# API Endpoint Audit

## Root Cause

The `NEXT_PUBLIC_API_URL` environment variable on Vercel was set to:
```
https://healthcare-backend-yybp.onrender.com
```
without the `/api/v1` path prefix. The frontend's `api-client.ts` used this value directly as the axios `baseURL`, producing requests like:

```
POST https://healthcare-backend-yybp.onrender.com/auth/register/patient
```

The correct endpoint (per the backend Swagger/OpenAPI spec) is:
```
POST https://healthcare-backend-yybp.onrender.com/api/v1/auth/register/patient
```

## Files Inspected

| File | Status |
|------|--------|
| `frontend/src/services/api-client.ts` | **Modified** |
| `frontend/next.config.ts` | **Modified** |
| `frontend/src/services/auth.ts` | No changes needed (uses relative paths correctly) |
| `frontend/src/services/chat.ts` | No changes needed |
| `frontend/src/services/reports.ts` | No changes needed |
| `frontend/src/services/patients.ts` | No changes needed |
| `frontend/src/services/medicines.ts` | No changes needed |
| `frontend/src/services/doctor.ts` | No changes needed |
| `frontend/src/services/demo.ts` | No changes needed |
| `frontend/.env.local.example` | Reference only |
| `frontend/src/__tests__/services/auth.test.ts` | No changes needed (mocks axios) |

## Files Modified

### 1. `frontend/src/services/api-client.ts`

Added `normalizeBaseUrl()` function that ensures the baseURL always includes `/api/v1`:

```ts
function normalizeBaseUrl(url: string): string {
  const trimmed = url.replace(/\/+$/, "");
  if (trimmed.endsWith("/api/v1")) return trimmed;
  return `${trimmed}/api/v1`;
}
```

This handles all cases:
- `https://healthcare-backend-yybp.onrender.com` → `https://healthcare-backend-yybp.onrender.com/api/v1`
- `https://healthcare-backend-yybp.onrender.com/api/v1` → unchanged
- `http://localhost:8000/api/v1` → unchanged
- `http://localhost:8000` → `http://localhost:8000/api/v1`

### 2. `frontend/next.config.ts`

Applied the same normalization to the rewrite destination to keep it in sync with axios.

## Endpoint Mapping

All services use `apiClient` from `api-client.ts`, which now correctly resolves to `/api/v1/...`:

| Service | Relative Path | Resolves To |
|---------|--------------|-------------|
| `auth.login` | `POST /auth/login` | `/api/v1/auth/login` |
| `auth.registerPatient` | `POST /auth/register/patient` | `/api/v1/auth/register/patient` |
| `auth.registerDoctor` | `POST /auth/register/doctor` | `/api/v1/auth/register/doctor` |
| `auth.logout` | `POST /auth/logout` | `/api/v1/auth/logout` |
| `auth.refreshToken` | `POST /auth/refresh` | `/api/v1/auth/refresh` |
| `auth.getMe` | `GET /auth/me` | `/api/v1/auth/me` |
| `chat.sendMessage` | `POST /chat/message` | `/api/v1/chat/message` |
| `chat.getHistory` | `GET /chat/history` | `/api/v1/chat/history` |
| `chat.clearHistory` | `DELETE /chat/history` | `/api/v1/chat/history` |
| `reportService.upload` | `POST /reports/upload` | `/api/v1/reports/upload` |
| `reportService.list` | `GET /reports` | `/api/v1/reports` |
| `reportService.get` | `GET /reports/:id` | `/api/v1/reports/:id` |
| `reportService.delete` | `DELETE /reports/:id` | `/api/v1/reports/:id` |
| `patientService.getProfile` | `GET /patients/me` | `/api/v1/patients/me` |
| `patientService.updateProfile` | `PATCH /patients/me` | `/api/v1/patients/me` |
| `patientService.getMyDoctors` | `GET /patients/me/doctors` | `/api/v1/patients/me/doctors` |
| `medicineService.list` | `GET /medicines` | `/api/v1/medicines` |
| `medicineService.listActive` | `GET /medicines/active` | `/api/v1/medicines/active` |
| `medicineService.get` | `GET /medicines/:id` | `/api/v1/medicines/:id` |
| `medicineService.update` | `PATCH /medicines/:id` | `/api/v1/medicines/:id` |
| `doctorService.getProfile` | `GET /doctors/me` | `/api/v1/doctors/me` |
| `doctorService.getPatients` | `GET /doctors/me/patients` | `/api/v1/doctors/me/patients` |
| `doctorService.assignPatient` | `POST /doctors/me/patients/:id/assign` | `/api/v1/doctors/me/patients/:id/assign` |
| `demoService.upload` | `POST /demo/upload` | `/api/v1/demo/upload` |
| `demoService.ask` | `POST /demo/ask` | `/api/v1/demo/ask` |
| `demoService.getScenarios` | `GET /demo/scenarios` | `/api/v1/demo/scenarios` |
| `demoService.reset` | `POST /demo/reset` | `/api/v1/demo/reset` |

No duplicate prefixes (`/api/v1/api/v1`) exist anywhere.

## Verification

- [x] Build compiles successfully (`npm run build`)
- [x] No raw `fetch()` calls bypass axios
- [x] No hardcoded `onrender.com` URLs in service files
- [x] No duplicate `/api/v1` prefixes
- [x] All 8 service files use the centralized `apiClient`
- [x] BaseURL normalization handles both with and without `/api/v1`
- [x] `next.config.ts` rewrite destination stays in sync with `api-client.ts`
