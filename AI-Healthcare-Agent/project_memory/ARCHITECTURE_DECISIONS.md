# Architecture Decision Records (ADR)

> Every important technical decision is recorded here with rationale, alternatives, and impact.
> New entries are appended. Never delete previous entries.

---

## ADR-001: FastAPI over Django

**Date:** 2026-07-03
**Decision:** Use FastAPI as the backend web framework
**Status:** Accepted

### Reason
FastAPI provides native async support, automatic OpenAPI documentation, Pydantic integration for request/response validation, and superior performance for AI/ML workloads. The project's heavy use of LangGraph, async OCR processing, and real-time features makes async-first architecture essential.

### Alternatives Considered
- **Django + DRF**: Mature ecosystem but synchronous by default, complex async setup, heavier ORM overhead
- **Flask**: Lightweight but lacks built-in validation, async support requires extensions
- **Node.js (Express)**: Strong async but loses Python AI/ML ecosystem (LangChain, LangGraph)

### Pros
- Native async/await support for I/O-bound operations
- Automatic OpenAPI/Swagger documentation generation
- Pydantic v2 integration for validation and serialization
- High performance (on par with Node.js/Go for API workloads)
- Excellent for AI/ML backend integration

### Cons
- Smaller ecosystem than Django
- Fewer third-party packages for common patterns
- Less mature admin interface options
- Community smaller than Django

### Impact
All future API development follows FastAPI patterns: dependency injection via `Depends()`, Pydantic schemas for validation, async endpoints for I/O operations.

---

## ADR-002: JWT with HS256 over RS256

**Date:** 2026-07-03
**Decision:** Use HS256 (symmetric) algorithm for JWT signing
**Status:** Accepted (with note for future migration)

### Reason
The project currently runs as a single service (monolith). HS256 is simpler to manage — a single secret key. RS256 would require key pair generation and management without immediate benefit. If the architecture splits into microservices, migrate to RS256.

### Alternatives Considered
- **RS256**: Asymmetric — public key for verification, private key for signing. Needed for microservices.
- **ES256**: Elliptic curve — faster than RSA but less library support.

### Pros
- Simple configuration (single secret key)
- Smaller token size than RSA
- Sufficient for single-service deployment
- Well-supported by python-jose

### Cons
- Cannot safely share verification with third parties
- Secret key rotation requires coordinated deployment
- If compromised, all tokens are forgeable

### Impact
When migrating to microservices, switch to RS256 or integrate with an OAuth2 provider.

---

## ADR-003: Refresh Tokens in Database

**Date:** 2026-07-11
**Decision:** Store refresh tokens in PostgreSQL (not just JWT)
**Status:** Accepted

### Reason
Healthcare applications require the ability to force-logout users, revoke sessions, and detect token theft. Stateless refresh tokens (pure JWT) cannot be revoked. DB-backed tokens enable server-side revocation, token rotation, and suspicious activity detection.

### Alternatives Considered
- **Pure JWT (stateless)**: Simple but cannot revoke individual sessions
- **Redis-backed**: Fast but adds infrastructure dependency. Planned for future rate limiting.
- **Hybrid**: JWT for access tokens (stateless), DB for refresh tokens (stateful) — chosen approach.

### Pros
- Server-side token revocation (logout)
- Token rotation tracking (detect stolen tokens)
- Session management (view active sessions, force logout all)
- Audit trail for security events

### Cons
- DB lookup on every refresh (slight latency)
- Storage growth over time (mitigated by cleanup_expired)
- Schema migration needed for new table

### Impact
All refresh token operations now include DB reads/writes. Background cleanup job needed for expired tokens.

---

## ADR-004: Token Rotation on Refresh

**Date:** 2026-07-11
**Decision:** Revoke old refresh token and issue new pair on every refresh
**Status:** Accepted

### Reason
If a refresh token is stolen, the attacker can use it indefinitely until expiry. Token rotation limits the window: if a rotated token is reused, the original token was compromised. This is a security best practice specified in RFC 6749.

### Alternatives Considered
- **Static refresh tokens**: Simple but vulnerable to replay attacks
- **Sliding expiration**: Extend token expiry on use but don't rotate — better UX, worse security

### Pros
- Limits stolen refresh token damage window
- Detects token theft (old token reuse)
- Follows OAuth2 security best practices

### Cons
- More complex implementation
- Race conditions if multiple clients share a token
- Requires proper token hash comparison

### Impact
Refresh endpoint is no longer idempotent. Each call invalidates the previous token. Frontend must handle token refresh carefully (queue pattern to prevent races).

---

## ADR-005: Zustand for State Management over Redux/Context

**Date:** 2026-07-03
**Decision:** Use Zustand for frontend state management
**Status:** Accepted

### Reason
Zustand provides a minimal API with no boilerplate compared to Redux, better performance than React Context for frequent updates, and built-in persist middleware for localStorage/cookie sync.

### Alternatives Considered
- **Redux Toolkit**: Powerful but excessive boilerplate for this project's state complexity
- **React Context**: Built-in but causes unnecessary re-renders on large state trees
- **Jotai**: Similar to Zustand but more atomic — less suitable for auth state

### Pros
- Minimal API (create, set, get)
- No boilerplate (no reducers, actions, dispatchers)
- Built-in persist middleware
- Tiny bundle size (~1KB)
- Works outside React components (useful for Axios interceptors)

### Cons
- Less middleware ecosystem than Redux
- Fewer devtools options
- Community smaller than Redux

### Impact
All global state (auth, UI preferences) managed through Zustand stores. API client accesses store directly for tokens.

---

## ADR-006: Two-Step Registration Over Single Form

**Date:** 2026-07-11
**Decision:** Registration uses role selection step → full form step
**Status:** Accepted

### Reason
Patient and doctor registration have significantly different fields. A single form would be cluttered and confusing. Two-step wizard provides clear user flow with context-appropriate fields.

### Alternatives Considered
- **Single form with conditional fields**: More complex validation, confusing UX
- **Separate pages (/register/patient, /register/doctor)**: More navigation overhead
- **Tab-based form**: Similar to current login but harder to validate

### Pros
- Clean user experience
- Simple validation per step
- Clear role context before data entry
- Reusable back navigation

### Cons
- Extra user interaction (one more click)
- State management across steps
- Slightly more frontend code

### Impact
Registration page is now a controlled multi-step form. Form state resets on role change. Validation is schema-per-role.

---

## ADR-007: Separate Login/Refresh Response Models

**Date:** 2026-07-11
**Decision:** Use `AuthResponse` (with user data) for login/register, `RefreshResponse` (tokens only) for refresh
**Status:** Accepted

### Reason
The refresh endpoint doesn't need to return user data — the client already has it. Returning user data on refresh would require an unnecessary DB lookup and increase response size. Separate models ensure precise API contracts.

### Alternatives Considered
- **Single AuthResponse with optional user field**: More flexible but less explicit
- **Always return user data from refresh**: Extra DB query for no benefit

### Pros
- Precise API contracts per endpoint
- No wasted DB lookups on refresh
- Clear documentation for API consumers
- Better performance (refresh is pure token operation)

### Cons
- Two models to maintain
- Slightly more code

### Impact
Frontend refresh handler only updates tokens, not user data. Less state update logic.

---

## ADR-008: Password Validation Rules (Server + Client)

**Date:** 2026-07-11
**Decision:** Enforce password complexity on both server (Pydantic) and client (Zod)
**Status:** Accepted

### Reason
Healthcare applications require strong password policies. Server-side validation is mandatory for security. Client-side validation provides instant feedback. Both must implement identical rules to prevent confusion.

### Rules Enforced
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character (!@#$%^&*()_+-=[]{};':"\|,.<>/?)

### Alternatives Considered
- **Server-only validation**: Poor UX (wait for round trip)
- **Client-only validation**: Security risk (can be bypassed)
- **Weaker rules**: Not appropriate for healthcare

### Pros
- Security: server enforces, client provides UX
- Instant user feedback
- Consistent validation behavior
- Healthcare-appropriate security posture

### Cons
- Duplicate regex patterns to maintain
- Can cause confusion if rules diverge
- Some users find strong passwords inconvenient

### Impact
Both Zod and Pydantic schemas define the same regex. Future password policy changes must update both.
