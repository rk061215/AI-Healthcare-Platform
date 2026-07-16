# Security Validation Report

**Project:** AI Healthcare Follow-up Assistant  
**Version:** v1.0.0-rc.1  
**Date:** 2026-07-16  
**Status:** 8 PASS / 2 WARNING / 0 FAIL

---

## 1. JWT Authentication

**Status:** ✅ PASS

### Implementation
- **Files:** `backend/app/core/security.py`, `backend/app/services/auth_service.py`, `backend/app/core/config.py:40-44`
- **Algorithm:** HS256 via `python-jose` (`jwt.encode`/`jwt.decode`)
- **Access tokens:** Short-lived (default 15 min), contain `sub`, `role`, `exp`, `iat`, `type: "access"`
- **Refresh tokens:** Long-lived (7 days default, 30 with remember-me), include `jti` (UUID v4) for revocation tracking
- **Rotation:** Refresh tokens are revoked on use — every `/refresh` issues a new pair and invalidates the old
- **Storage:** Refresh tokens stored as SHA-256 hash in database; plaintext never persisted
- **Password hashing:** bcrypt via `passlib` (`backend/app/core/security.py:11-19`)
- **Token type enforcement:** `verify_token()` checks `type` claim matches expected value (`access`/`refresh`)

### Protects Against
- Token forgery, replay attacks (short expiry + rotation), stolen refresh tokens (hashed + revocable), credential leakage (bcrypt)

### Gaps
- Access and refresh tokens share the same `JWT_SECRET_KEY` — a compromise of the secret compromises both token types
- No token blacklist/deny-list for access tokens (revoked access tokens remain valid until expiry)
- Default secret `"change-me-to-a-random-secret-key"` is used when unconfigured; a runtime warning is emitted in `config.py:182-187`

### Recommendation
- Consider separate signing keys for access vs refresh tokens
- Implement an access token denylist (Redis or DB) for immediate revocation capability

---

## 2. Role Authorization

**Status:** ✅ PASS

### Implementation
- **Files:** `backend/app/api/deps.py:11-70`
- **Dependency functions:** `get_current_user` (authenticated), `get_current_patient`, `get_current_doctor`, `require_role(allowed_roles)`
- **Role in JWT:** Role is embedded at token creation (`backend/app/core/security.py:37`) and extracted from the decoded payload
- **Routing:** Each endpoint declares its required role via `Depends()` at the router level
  - `documents.py` uses `get_current_patient` for uploads, `get_current_user` for downloads
  - `auth.py` endpoints are public (registration, login) or protected via `get_current_user`
  - `chat.py` uses `get_current_patient`
- **Admin role:** Not yet implemented — only `patient` and `doctor` roles exist

### Protects Against
- Unauthorized access to patient-specific endpoints, privilege escalation, horizontal movement between roles

### Gaps
- No admin role implementation
- All role checks are done in the dependency layer — a missing `Depends()` call on a new endpoint would leave it unprotected

### Recommendation
- Add integration tests that verify every protected endpoint enforces correct role checks
- Implement admin role when needed for system administration

---

## 3. CSRF Protection

**Status:** ⚠️ WARNING

### Implementation
- **Files:** `backend/app/middleware/csrf.py`, `backend/app/core/config.py:92`
- **Mechanism:** Origin / Referer header validation (NOT the traditional double-submit cookie pattern described in the task)
- **Scope:** Validates `POST`, `PUT`, `PATCH`, `DELETE` requests (skips `GET`, `HEAD`, `OPTIONS`)
- **Enabled via:** `ENABLE_CSRF_PROTECTION` config flag (`backend/app/main.py:72-73`)
- **Exempt endpoints:** Paths starting with `/demo`
- **Allowed origins:** Parsed from `BACKEND_CORS_ORIGINS` config

### Protects Against
- Cross-Site Request Forgery (defense-in-depth — primary protection is Bearer token auth which browsers don't auto-attach cross-origin)

### Gaps
- **Substring matching** in `_origin_is_allowed` (`csrf.py:82-84`): `if allowed in url` means `http://localhost:3000` matches `http://localhost:3000.evil.com`
- **Bypassed in development** (`csrf.py:65-66`): `ENVIRONMENT == "development"` disables ALL checks
- **Missing origin returns 200** (`csrf.py:77`): Requests without Origin or Referer headers are allowed through
- Not the double-submit pattern — relies on header presence which can be suppressed by some browser configurations

### Recommendation
- Replace substring matching with exact hostname comparison (parse with `urlparse` and compare `hostname`)
- Do not allow requests with missing Origin/Referer on state-changing endpoints in production
- Consider a true double-submit cookie pattern or CSRF token header for defense-in-depth

---

## 4. Rate Limiting

**Status:** ⚠️ WARNING

### Implementation
- **Files:** `backend/app/middleware/rate_limit.py`, `backend/app/core/config.py:131-137`
- **Algorithm:** Sliding window per IP per route (in-memory)
- **Limits:**
  - Global: 60 requests/minute (`RATE_LIMIT_PER_MINUTE`)
  - Login: 5 requests/minute (`RATE_LIMIT_LOGIN_PER_MINUTE`)
- **Scope:** `POST`, `PUT`, `PATCH`, `DELETE` only
- **IP extraction:** `X-Forwarded-For` → `X-Real-IP` → `request.client.host` → `"unknown"`
- **Enabled via:** `RATE_LIMIT_ENABLED` config flag (`backend/app/main.py:75-76`)

### Protects Against
- Brute-force login attacks, API abuse, DoS via excessive requests

### Gaps
- **In-memory only:** State is lost on server restart; no persistence across workers
- **No Redis implementation:** `REDIS_URL` config exists (`config.py:139`) but `InMemoryRateLimiter` has no Redis fallback
- **Per-IP granularity only:** No user-based, endpoint-specific, or tiered rate limiting
- **GET requests not limited:** Only mutation methods are rate-limited
- **No burst handling:** The sliding window is strict — a sudden burst of 60 requests in one second is allowed as long as the window tracks correctly

### Recommendation
- Implement the Redis-backed rate limiter (config already exists) for production deployments
- Add per-user rate limiting (using `sub` claim from JWT)
- Consider rate-limiting GET endpoints for document downloads and chat history

---

## 5. Input Validation

**Status:** ✅ PASS

### Implementation
- **Files:** `backend/app/schemas/auth.py`, `backend/app/schemas/chat.py`, `backend/app/schemas/document.py`, and all schema modules
- **Framework:** Pydantic v2 with `field_validator` decorators
- **Validated fields:**
  - Email: `EmailStr` type ensures RFC 5322 format
  - Password: min 8 / max 128 chars, must include uppercase, lowercase, digit, special character (`auth.py:90-105`)
  - Phone: E.164 format via regex (`auth.py:108-114`)
  - Date of birth: ISO format, must be in the past (`auth.py:162-174`)
  - Gender: allowed set (`male`, `female`, `other`, `prefer_not_to_say`)
  - Pagination: `ge=1`, `le=100` constraints
  - Terms acceptance: must be `True`
- **All schemas** use `model_config = {"from_attributes": True}` or `ConfigDict(extra="forbid")` to prevent extra field injection

### Protects Against
- Injection of malformed data, type confusion, mass assignment, business logic violations (e.g., future date of birth)

### Gaps
- Some string fields (e.g., `full_name`, `hospital_name`) only enforce length constraints but not character whitelisting
- `ChatMessageRequest.message` has no length limit or content validation beyond being a string

### Recommendation
- Add maximum length to `ChatMessageRequest.message`
- Consider character whitelisting for name fields to prevent XSS in stored names

---

## 6. Prompt Injection Resistance

**Status:** ✅ PASS

### Implementation
- **Files:** `backend/app/rag/guardrails.py`, `backend/app/rag/query_processor.py`, `backend/app/rag/rag_engine.py`
- **Pre-generation guardrails:** `backend/app/rag/guardrails.py:142-159`
  - `check_query_safety`: Regex patterns for self-harm, suicide, harm keywords
  - `check_insufficient_context`: Empty/low-context detection
- **Post-generation guardrails:** `backend/app/rag/guardrails.py:161-296`
  - `check_unsupported_claims`: Diagnostic/treatment language detection
  - `check_medical_uncertainty`: Overconfidence detection
  - `check_citation_hallucination`: Validates inline citations
  - `check_context_grounding`: Text overlap analysis
- **Query processing:** `backend/app/rag/query_processor.py:67-72` strips special characters with regex `[^\w\s\-'/,()]`
- **Enabled by default:** `RAGEngineConfig.enable_guardrails_pre=True`, `enable_guardrails_post=True`

### Protects Against
- Harmful content generation, prompt injection via special characters, hallucinated medical claims, diagnostic/treatment recommendations without context

### Gaps
- No dedicated prompt injection pattern detection (e.g., "ignore previous instructions", "system prompt")
- Query safety checks only cover self-harm patterns — not broader injection categories (role-play attacks, delimiter injection)
- Character stripping in `query_processor.py:70` is lenient — many special characters pass through
- No input length limit for the chat message before processing
- Medical disclaimer only appended at the end — does not protect against prompt extraction

### Recommendation
- Add prompt injection pattern detection (ignore-instructions, role-escalation attempts)
- Implement query length limiting at the API layer
- Consider a secondary LLM-based guardrail for comprehensive content safety
- Add deny-list for known prompt injection payload patterns

---

## 7. File Upload Validation

**Status:** ✅ PASS

### Implementation
- **Files:** `backend/app/services/document_service.py:230-247`, `backend/app/core/config.py:102-108`
- **Extension whitelist:** `.pdf`, `.png`, `.jpg`, `.jpeg` (hardcoded in `DocumentService.ALLOWED_TYPES`)
- **Config-level extensions:** `ALLOWED_EXTENSIONS` (includes `.dicom`), `DOCUMENT_ALLOWED_EXTENSIONS`
- **Size limits:** `MAX_UPLOAD_SIZE_MB=10`, `DOCUMENT_MAX_SIZE_MB=20`
- **Content hash deduplication:** SHA-256 hash checked before storage (`document_service.py:55-60`)
- **Virus scan placeholder:** Marks all uploads as `CLEAN` (`document_service.py:317-325`)
- **Storage:** Files saved via UUID to local filesystem (`storage/backend.py:31-35`)

### Protects Against
- Malicious file uploads (extension restriction), storage exhaustion (size limits), duplicate content (hash dedup)

### Gaps
- **No MIME type validation:** The `content_type` is trusted from the client but not validated against the file content
- **Virus scanning is a no-op:** Always marks as `CLEAN` without actual scanning (`document_service.py:319`)
- `.dicom` is in config `ALLOWED_EXTENSIONS` but not in `DocumentService.ALLOWED_TYPES` — potential inconsistency
- No image re-encoding/re-processing to strip embedded payloads
- No file content signature/magic byte verification

### Recommendation
- Implement actual virus scanning (ClamAV integration) or at minimum a scan API call
- Validate file content matches declared extension using magic bytes (`python-magic` or `file` command)
- Align `DocumentService.ALLOWED_TYPES` with config-level `ALLOWED_EXTENSIONS`
- Re-encode images on upload to strip EXIF/metadata exploits

---

## 8. Path Traversal Protection

**Status:** ✅ PASS

### Implementation
- **Files:** `backend/app/storage/backend.py:27-48`, `backend/app/services/document_service.py`
- **Storage path:** Files saved as `{base_path}/{uuid}` — the `file_id` is a UUID, not user-controlled
- **Retrieval:** `LocalStorageBackend.get()` constructs path as `self.base_path / file_id` — path traversal via UUID is not possible
- **Config:** `DOCUMENT_STORAGE_DIR="./documents"` and `UPLOAD_DIR="./uploads"` are isolated directories

### Protects Against
- Directory traversal attacks (../../etc/passwd), unauthorized file access, file system escape

### Gaps
- No explicit sanitization of `original_filename` in the `Content-Disposition` header when downloading (`documents.py:96`) — though this is a header injection concern, not path traversal
- `LocalStorageBackend` does not validate that the resolved path stays within `base_path` (uses `Path` join which collapses `..` but UUID inputs are safe)

### Recommendation
- Add an assertion in `LocalStorageBackend` to verify resolved path is within `base_path` (defense-in-depth)
- Sanitize `original_filename` for `Content-Disposition` header to prevent header injection

---

## 9. SQL Injection Protection

**Status:** ✅ PASS

### Implementation
- **Files:** `backend/app/database/session.py`, `backend/app/database/base.py`, all repository and service modules
- **ORM:** SQLAlchemy ORM used throughout — no raw SQL `text()` or `execute()` calls found
- **Session management:** `Session` dependency injected via `get_db()` (`session.py:47-53`), auto-closed in `finally` block
- **Model definitions:** Declarative `Base` class with typed column mappings
- **Query building:** Repository classes use ORM query API (filter, get, etc.) with parameterized queries

### Protects Against
- SQL injection attacks, unauthorized data access via query manipulation

### Gaps
- Database connection string includes plaintext credentials in `DATABASE_URL` (`config.py:32`) — credentials are logged if `DEBUG=True` enables SQL echo (`session.py:17`)
- Connection pooling limits are generous (`POOL_SIZE=10`, `MAX_OVERFLOW=20`)
- No query complexity limits

### Recommendation
- Disable SQL echo (`echo=settings.DEBUG`) in production — it logs parameterized queries with data
- Use environment-specific database credentials with least privilege
- Consider a query timeout middleware

---

## 10. Security Headers

**Status:** ✅ PASS

### Implementation
- **File:** `backend/app/middleware/security.py`
- **Enabled via:** `SECURITY_HEADERS_ENABLED` config flag (`backend/app/main.py:78-79`)
- **Headers set:**
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy: camera=(), microphone=(), geolocation=()`
  - `Cache-Control: no-store`
- **CORS:** `backend/app/middleware/cors.py` — allows configured origins, credentials, all methods and headers

### Protects Against
- MIME-sniffing attacks (`X-Content-Type-Options`), clickjacking (`X-Frame-Options: DENY`), XSS in legacy browsers (`X-XSS-Protection`), MITM/HSTS bypass (`Strict-Transport-Security`), referrer leakage (`Referrer-Policy`), API misuse via permissive CORS

### Gaps
- **No Content-Security-Policy (CSP) header:** This is a significant gap — CSP would protect against XSS and data injection attacks
- **CORS allows all headers and methods** (`allow_methods=["*"]`, `allow_headers=["*"]`) — permissive by default
- HSTS `includeSubDomains` should be validated against subdomain inventory before production
- `Cache-Control: no-store` is aggressive — may impact performance for static assets

### Recommendation
- Implement a CSP header restricted to the application's own domain and CDN
- Restrict CORS `allow_methods` and `allow_headers` to only what the application uses
- Add `X-Permitted-Cross-Domain-Policies: none` header
- Consider `X-DNS-Prefetch-Control: off` for privacy

---

## Summary

| # | Area | Status | Key Gaps |
|---|------|--------|----------|
| 1 | JWT Authentication | ✅ PASS | Shared signing key, no access token revocation |
| 2 | Role Authorization | ✅ PASS | No admin role, no automated endpoint coverage tests |
| 3 | CSRF Protection | ⚠️ WARNING | Substring origin matching, bypassed in dev, missing header = pass |
| 4 | Rate Limiting | ⚠️ WARNING | In-memory only (no Redis), GET requests not limited |
| 5 | Input Validation | ✅ PASS | Chat message has no max length, name fields lack char whitelist |
| 6 | Prompt Injection | ✅ PASS | No dedicated injection pattern detection, lenient char stripping |
| 7 | File Upload | ✅ PASS | No MIME validation, virus scan is no-op |
| 8 | Path Traversal | ✅ PASS | UUID-based storage prevents traversal |
| 9 | SQL Injection | ✅ PASS | Pure ORM usage, no raw SQL |
| 10 | Security Headers | ✅ PASS | Missing CSP, permissive CORS |

**8 PASS / 2 WARNING / 0 FAIL**

### Critical Priorities for Production
1. Implement Content-Security-Policy header
2. Fix CSRF origin matching (exact hostname comparison)
3. Implement Redis-backed rate limiting
4. Add actual virus scanning for uploads
5. Strengthen prompt injection pattern detection
