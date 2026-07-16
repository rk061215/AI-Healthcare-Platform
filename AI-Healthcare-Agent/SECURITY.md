# Security Policy

This document defines the security model, policies, and procedures for the AI Healthcare Follow-up Assistant. All contributors and maintainers must follow these guidelines.

## Table of Contents

- [Authentication](#authentication)
- [Authorization](#authorization)
- [JWT Policy](#jwt-policy)
- [Refresh Token Policy](#refresh-token-policy)
- [CSRF Policy](#csrf-policy)
- [Rate Limiting](#rate-limiting)
- [Secret Management](#secret-management)
- [OWASP Considerations](#owasp-considerations)
- [Dependency Updates](#dependency-updates)
- [Vulnerability Reporting](#vulnerability-reporting)

---

## Authentication

### Bearer Token Authentication

The API uses **Bearer JWT tokens** for authentication. Tokens are sent in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

### Login Flow

1. Client sends `POST /api/v1/auth/login` with `email`, `password`, and `role`.
2. Server validates credentials against bcrypt-hashed password in database.
3. Server returns an access token (15 min) and refresh token (7 or 30 days).
4. Client stores tokens and includes the access token in subsequent requests.

### Token Validation

- Access tokens are validated on every request via the `get_current_user()` dependency.
- The `verify_token()` function decodes and validates:
  - Signature (HMAC-SHA256 with `JWT_SECRET_KEY`).
  - Expiration (`exp` claim).
  - Token type (`type: "access"` or `type: "refresh"`).
- Invalid, expired, or wrong-type tokens return `401 Unauthorized` with `WWW-Authenticate: Bearer` header.

### Password Policy

| Requirement        | Rule                                      |
|--------------------|-------------------------------------------|
| Minimum length     | 8 characters                              |
| Uppercase          | At least 1 character                      |
| Lowercase          | At least 1 character                      |
| Number             | At least 1 digit                          |
| Special character  | At least 1 (`!@#$%^&*()_+-=[]{}|;:,.<>?`)|
| Storage            | bcrypt hash (never plaintext)             |
| Validation         | Server-side + client-side (Zod)           |

---

## Authorization

### Role-Based Access Control

The API implements **role-based access control (RBAC)** with two roles:

| Role      | Description                |
|-----------|----------------------------|
| `patient` | End user receiving care    |
| `doctor`  | Healthcare provider        |

### Dependency Chain

```
get_current_user()        → validates token, returns payload
├── get_current_patient() → requires role == "patient"
└── get_current_doctor()  → requires role == "doctor"
```

### Endpoint Authorization Matrix

| Endpoint                          | Required Role  | Ownership Check |
|-----------------------------------|----------------|-----------------|
| `POST /auth/register/*`          | Public         | N/A             |
| `POST /auth/login`               | Public         | N/A             |
| `POST /auth/refresh`             | Public         | N/A             |
| `POST /auth/logout`              | Authenticated  | N/A             |
| `GET /auth/me`                   | Authenticated  | Token-bound     |
| `POST /appointments`             | Patient        | N/A             |
| `GET /appointments`              | Patient        | Own only        |
| `GET /appointments/doctor`       | Doctor         | Own only        |
| `PATCH /appointments/{id}`       | Patient/Doctor | Ownership       |
| `DELETE /appointments/{id}`      | Patient/Doctor | Ownership       |
| `GET /patients/me`               | Patient        | Token-bound     |
| `GET /doctors/me`                | Doctor         | Token-bound     |

### Ownership Enforcement

For multi-tenant resources (appointments), ownership is enforced at the service layer:

```python
def _check_ownership(self, appointment: Appointment, user_id: str, role: str) -> None:
    if role == "patient" and str(appointment.patient_id) != user_id:
        raise ForbiddenException("You can only access your own appointments")
    if role == "doctor" and str(appointment.doctor_id) != user_id:
        raise ForbiddenException("You can only access your assigned appointments")
```

This prevents **IDOR (Insecure Direct Object Reference)** attacks where a user modifies another user's resource by guessing its ID.

---

## JWT Policy

### Token Structure

**Access Token:**

```json
{
  "sub": "user-uuid",
  "role": "patient",
  "exp": 1700000000,
  "iat": 1699999100,
  "type": "access"
}
```

**Refresh Token:**

```json
{
  "sub": "user-uuid",
  "role": "patient",
  "exp": 1700600000,
  "iat": 1699999100,
  "type": "refresh",
  "jti": "unique-uuid-v4"
}
```

### Signing

| Parameter      | Value                    |
|----------------|--------------------------|
| Algorithm      | HS256 (HMAC-SHA256)      |
| Secret key     | `JWT_SECRET_KEY` (env)   |
| Library        | `python-jose`            |

### Token Lifetimes

| Token Type       | Default TTL | Config Variable                          |
|------------------|-------------|------------------------------------------|
| Access           | 15 minutes  | `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`        |
| Refresh (normal) | 7 days      | `JWT_REFRESH_TOKEN_EXPIRE_DAYS`         |
| Refresh (remember me) | 30 days | `JWT_REFRESH_TOKEN_REMEMBER_ME_DAYS`   |

### Security Rules

1. **Short-lived access tokens** limit the XSS damage window to 15 minutes.
2. **Unique jti** on every refresh token prevents replay attacks.
3. **Token hashing** — refresh tokens are stored as SHA-256 hashes in the database, never as raw JWTs.
4. **Token rotation** — every refresh invalidates the old token and issues a new pair.
5. **Server-side revocation** — logout hashes the provided refresh token and revokes it in the database.
6. **Secret key rotation** — change `JWT_SECRET_KEY` immediately if a compromise is suspected. Old tokens will be invalidated.

---

## Refresh Token Policy

### Storage

| Field       | Type      | Description                              |
|-------------|-----------|------------------------------------------|
| `jti`       | UUID v4   | Unique identifier for the token          |
| `token_hash`| SHA-256   | Hash of the raw refresh token string     |
| `user_id`   | UUID      | Owner of the token                       |
| `role`      | string    | User role at time of issuance            |
| `is_revoked`| boolean   | Whether the token has been revoked       |
| `expires_at`| timestamp | Token expiration                         |

### Rotation Flow

```
1. Client sends POST /auth/refresh with refresh_token in body
2. Server hashes the provided token, looks up by hash
3. Server verifies: token exists, not revoked, not expired, correct type
4. Server revokes old token (is_revoked = true)
5. Server issues new access + refresh token pair
6. If old token is reused → all tokens for that user are revoked
```

### Reuse Detection

If a revoked refresh token is presented again, the system revokes **all** refresh tokens for that user. This prevents attackers from using a stolen refresh token even if they manage to capture one before rotation.

---

## CSRF Policy

### Architecture

This application uses **Bearer token authentication** (not cookies). Since browsers do not automatically attach `Authorization` headers to cross-origin requests, the API is inherently CSRF-safe.

### Defense-in-Depth

The `CSRFTokenMiddleware` adds origin validation as a second layer:

- **Validates** `Origin` header against allowed origins on POST/PUT/PATCH/DELETE.
- **Falls back** to `Referer` header if `Origin` is absent (same-origin requests).
- **Bypassed** for GET/HEAD/OPTIONS (safe methods).
- **Disabled** in `development` environment to avoid friction during local development.

### Allowed Origins

Configured via `BACKEND_CORS_ORIGINS`:

```
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

Add production domains to this list before deploying.

### Why Not CSRF Tokens?

Traditional CSRF tokens protect against cookie-based auth attacks. Since this API never uses cookies for authentication, double-submit cookie patterns would add complexity without meaningful security benefit. Origin header validation provides sufficient defense-in-depth.

---

## Rate Limiting

### Tiers

| Tier    | Limit                     | Scope               | Applies To                     |
|---------|---------------------------|---------------------|--------------------------------|
| Login   | 5 requests per minute     | Per IP address      | `POST /auth/login`             |
| Global  | 60 requests per minute    | Per IP address      | All POST/PUT/PATCH/DELETE      |

### Behavior

- When a limit is exceeded, the API returns `429 Too Many Requests`.
- Response includes a `Retry-After` header with seconds until the next allowed request.
- GET/HEAD/OPTIONS requests are **not** rate-limited.

### Architecture

- **Development**: In-memory sliding window (`InMemoryRateLimiter`).
- **Production**: Redis-backed via `REDIS_URL` configuration. When `REDIS_URL` is set, `settings.redis_enabled` returns `true`, and the middleware should use Redis-based storage (implementation pending — see `TODO` in `rate_limit.py`).

### Response Format

```json
HTTP 429 Too Many Requests
Retry-After: 45

{
  "error": "Rate limit exceeded. Please slow down.",
  "retry_after": 45
}
```

---

## Secret Management

### What Constitutes a Secret

- `JWT_SECRET_KEY`
- `OPENAI_API_KEY`
- `GOOGLE_APPLICATION_CREDENTIALS` file path and contents
- `DATABASE_URL` (contains credentials)
- Any API keys, tokens, or passwords

### Rules

1. **Never commit secrets** to the repository.
2. **Use environment variables** for all secrets (read via `pydantic-settings`).
3. **`.env.example` files** contain placeholder values (`change-me-to-a-random-secret-key`), never real secrets.
4. **`.env` files** are gitignored (confirmed in `.gitignore`).
5. **Service account key files** (`*.json`) are gitignored.
6. **CI/CD secrets** use GitHub Encrypted Secrets, never plaintext in workflow files.
7. **Docker Compose** uses environment files (`.env`), not hardcoded values.
8. **Logging** must never output secrets — see [Logging Standards](CODE_STYLE.md#logging-standards).

### Key Rotation

- Rotate `JWT_SECRET_KEY` immediately if a compromise is suspected.
- Rotate `OPENAI_API_KEY` if it is exposed in logs, error messages, or client-side code.
- Rotate database credentials on staff departure or suspected breach.

---

## OWASP Considerations

### Top 10 Coverage

| OWASP Category                    | Mitigation Strategy                                                 |
|-----------------------------------|---------------------------------------------------------------------|
| **Broken Access Control**         | RBAC via FastAPI dependency chain; ownership checks in service layer|
| **Cryptographic Failures**        | bcrypt for passwords, SHA-256 for token hashing, HS256 for JWTs     |
| **Injection**                     | SQLAlchemy ORM prevents SQLi; Pydantic validates all input shapes   |
| **Insecure Design**               | Rate limiting, CSRF protection, token rotation, reuse detection     |
| **Security Misconfiguration**     | Centralized config via `pydantic-settings`; CORS restricted to origins|
| **Vulnerable Components**         | Regular dependency updates (see Dependency Updates section)         |
| **Authentication Failures**       | Brute-force protection via rate limiting; secure password policy    |
| **Data Integrity Failures**       | JWT signature verification; token type validation                   |
| **Logging & Monitoring**          | Loguru with structured logging; error tracking per request          |
| **SSRF**                          | No user-provided URLs fetched by the server                         |

### Additional Protections

- **XSS**: React/Next.js auto-escapes output; CSP headers recommended for production.
- **CORS**: Restricted to known origins; no wildcard in production.
- **HTTPS**: TLS termination is the responsibility of the deployment infrastructure.
- **Validation**: All input validated by Pydantic schemas; file uploads restricted by type and size.

---

## Dependency Updates

### Schedule

| Frequency     | Scope                        | Tool              |
|---------------|------------------------------|-------------------|
| Weekly        | All Python dependencies      | `pip-audit`       |
| Weekly        | All npm dependencies         | `npm audit`       |
| Monthly       | Major version upgrades       | Manual review     |
| On-demand     | Security advisories          | GitHub Dependabot |

### Process

1. **Check for vulnerabilities** weekly:

   ```bash
   # Backend
   pip-audit

   # Frontend
   cd frontend && npm audit
   ```

2. **Update dependencies** in a dedicated chore PR:

   ```bash
   # Backend
   pip install --upgrade -r requirements.txt
   pip freeze > requirements.txt

   # Frontend
   npm update
   ```

3. **Run full test suite** after any dependency update.
4. **Pin exact versions** in `requirements.txt` for reproducibility.
5. **Document breaking changes** in the PR description and CHANGELOG.

### Critical Vulnerabilities

If a critical vulnerability is found (CVSS >= 9.0):

1. Create an immediate hotfix branch.
2. Update the affected dependency.
3. Run the full test suite.
4. Bypass the regular review process if necessary (document in the commit).
5. Notify downstream consumers.

---

## Vulnerability Reporting

### Reporting Process

If you discover a security vulnerability in this project:

1. **Do not open a public issue** — this could be exploited before a fix is deployed.
2. **Report via GitHub Security Advisory**:
   - Go to the repository → Security → Advisories → New advisory.
   - Provide a detailed description of the vulnerability.
   - Include steps to reproduce (if applicable).
   - Suggest a fix (if possible).
3. **Alternative**: Email the maintainers directly (contact information in the repository profile).

### Response Timeline

| Severity   | Initial Response | Fix Published  |
|------------|-----------------|----------------|
| Critical   | 24 hours        | 7 days         |
| High       | 48 hours        | 14 days        |
| Medium     | 1 week          | 30 days        |
| Low        | 1 month         | Next release   |

### What to Include

- **Type of vulnerability** (XSS, IDOR, RCE, etc.).
- **Affected components** (endpoint, library, config).
- **Version** where the vulnerability exists.
- **Impact** — what an attacker could achieve.
- **Proof of concept** (if available and safe to share).
- **Suggested fix** (if any).

### Disclosure Policy

- We will acknowledge receipt within 48 hours.
- We will keep you informed of progress.
- We will credit you in the security advisory (unless you prefer anonymity).
- We coordinate public disclosure after the fix is deployed.

---

*Last updated: 2026-07-11*
