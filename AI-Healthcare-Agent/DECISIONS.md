# Engineering Decision Log

> Permanent historical record of every significant technical, architectural, security, AI,
> database, deployment, and product decision made during the development of the
> AI Healthcare Follow-up Assistant.
>
> This document is the primary reference for future contributors, maintainers, and
> anyone performing technical due diligence. Every decision records not only WHAT
> was chosen, but WHY, what alternatives were considered, and how the choice
> impacts the project's future.
>
> **Started:** 2026-07-14
> **Current Version:** 0.8.0
> **Status:** Active — updated continuously

---

## Table of Contents

1. [Purpose & Process](#purpose--process)
2. [Decision Categories](#decision-categories)
3. [Decision Status Definitions](#decision-status-definitions)
4. [Decision Entries](#decision-entries)
   - [DEC-001: FastAPI over Django](#dec-001-fastapi-over-django)
   - [DEC-002: Next.js over Plain React](#dec-002-nextjs-over-plain-react)
   - [DEC-003: PostgreSQL as Primary Database](#dec-003-postgresql-as-primary-database)
   - [DEC-004: SQLAlchemy ORM](#dec-004-sqlalchemy-orm)
   - [DEC-005: Repository Pattern](#dec-005-repository-pattern)
   - [DEC-006: Service Layer](#dec-006-service-layer)
   - [DEC-007: JWT Authentication](#dec-007-jwt-authentication)
   - [DEC-008: Refresh Token Rotation](#dec-008-refresh-token-rotation)
   - [DEC-009: Hash Refresh Tokens in Database](#dec-009-hash-refresh-tokens-in-database)
   - [DEC-010: Role-Based Access Control](#dec-010-role-based-access-control)
   - [DEC-011: LangGraph for AI Orchestration](#dec-011-langgraph-for-ai-orchestration)
   - [DEC-012: LangChain for AI Utilities](#dec-012-langchain-for-ai-utilities)
   - [DEC-013: ChromaDB for MVP Vector Database](#dec-013-chromadb-for-mvp-vector-database)
   - [DEC-014: Store Prompts as Markdown Files](#dec-014-store-prompts-as-markdown-files)
   - [DEC-015: Maintain project_memory as Persistent Knowledge Base](#dec-015-maintain-project_memory-as-persistent-knowledge-base)
   - [DEC-016: Docker Compose for Local Development](#dec-016-docker-compose-for-local-development)
   - [DEC-017: Alembic for Database Migrations](#dec-017-alembic-for-database-migrations)
   - [DEC-018: Semantic Versioning](#dec-018-semantic-versioning)
   - [DEC-019: Clean Architecture](#dec-019-clean-architecture)
   - [DEC-020: Dependency Injection Throughout Backend](#dec-020-dependency-injection-throughout-backend)
   - [DEC-021: Freeze Medical Parser at MVP](#dec-021-freeze-medical-parser-at-mvp)
   - [DEC-022: Provider-Independent Embedding Layer](#dec-022-provider-independent-embedding-layer)
   - [DEC-023: Prompt Management System with Versioning and Caching](#dec-023-prompt-management-system-with-versioning-and-caching)

---

## Purpose & Process

### Purpose

This Engineering Decision Log exists to:

1. **Preserve context** — Future contributors should understand why decisions were
   made, not just what was decided. This prevents re-litigating settled questions.
2. **Accelerate onboarding** — New team members can read this document to understand
   the project's technical foundation in minutes rather than weeks.
3. **Enable accountability** — Every decision is timestamped, attributed, and linked
   to its reasoning, alternatives, and consequences.
4. **Support due diligence** — Investors, auditors, and compliance reviewers can
   trace the reasoning behind every architectural choice.
5. **Prevent regression** — When revisiting an old decision, the log provides the
   original context so we don't repeat past mistakes.

### Decision Process

Every significant decision follows this workflow:

```
1. Identify Need ──> 2. Research Options ──> 3. Evaluate Trade-offs
       │                                         │
       ▼                                         ▼
4. Document Decision ──> 5. Implement ──> 6. Revisit if needed
```

Decisions are made by the engineering lead after consultation with relevant
stakeholders (clinical advisors for medical decisions, DevOps for infrastructure,
etc.). Minority opinions and rejected alternatives are documented alongside
the chosen path.

### Decision Categories

| Category | Scope |
|----------|-------|
| **Architecture** | System-level structure, patterns, layering |
| **Database** | Storage engine, schema design, migrations, indexing |
| **Backend** | Python/FastAPI implementation, libraries, middleware |
| **Frontend** | React/Next.js implementation, UI framework, state management |
| **Security** | Authentication, authorization, data protection, compliance |
| **Authentication** | Identity management, token strategy, session handling |
| **AI** | Model selection, agent design, prompt strategy |
| **LangGraph** | Graph structure, state management, node design |
| **RAG** | Retrieval strategy, embedding model, vector search |
| **Prompt Engineering** | Prompt format, versioning, loading strategy |
| **Infrastructure** | Docker, networking, storage, compute |
| **Deployment** | Hosting, CI/CD, environment strategy |
| **DevOps** | Build pipeline, monitoring, alerting |
| **Performance** | Latency targets, optimization strategy, caching |
| **Testing** | Framework, approach, coverage targets |
| **Documentation** | Standards, tooling, maintenance |
| **UX** | User experience, accessibility, design decisions |
| **API** | REST design, versioning, response format |
| **Business Logic** | Domain rules, workflow design |

### Decision Status Definitions

| Status | Meaning |
|--------|---------|
| **Proposed** | Under discussion, not yet accepted |
| **Accepted** | Approved but not yet implemented |
| **Implemented** | Deployed and in production |
| **Deprecated** | No longer recommended for new development, but still in use |
| **Replaced** | Superseded by a newer decision (cross-referenced) |
| **Rejected** | Considered and explicitly not chosen |

### Review Process

Decisions are reviewed:

- **Informally** — During code review when new code touches a decision's area
- **Formally** — When a decision's Future Review criteria are triggered
- **On-demand** — When a team member believes a decision should be revisited

### Update Rules

```
1. NEVER overwrite or edit a previous decision entry.
2. If a decision changes:
   a. Mark the old decision as "Replaced"
   b. Add a "Replaced By" field referencing the new decision ID
   c. Create a new decision entry with the updated rationale
3. Maintain chronological order by decision ID.
4. Keep decision IDs sequential (DEC-001, DEC-002, ...).
5. Cross-reference related decisions with "See Also" fields.
6. All dates are ISO 8601 (YYYY-MM-DD).
```

---

## Decision Entries

---

### DEC-001: FastAPI over Django

**Date:** 2026-07-03
**Category:** Architecture, Backend
**Status:** Implemented
**Title:** Use FastAPI instead of Django REST Framework

**Context:**
The project needed a Python backend framework for a healthcare AI assistant with
real-time chat, streaming responses, and LLM integration. Django REST Framework
was the incumbent choice, but this project has specific requirements: async
support for streaming LLM responses, automatic OpenAPI documentation for a
frontend team, and lightweight deployment.

**Decision:**
Use FastAPI as the primary backend framework. All API routes, middleware, and
dependency injection use FastAPI idioms.

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| Django REST Framework | Heavy ORM coupling, synchronous by default (requires separate ASGI setup for async), more boilerplate for one-off endpoints, larger deployment footprint. Django's "batteries included" (admin panel, ORM, auth) is powerful for CRUD apps but adds complexity for an AI-agent-heavy system. |
| Flask | Missing native async support, no automatic OpenAPI docs, requires manual validation with marshmallow/pydantic, less structured for large projects. |
| Sanic | Smaller ecosystem, fewer third-party integrations, less community support for production deployment. |
| Starlette (raw) | FastAPI is built on Starlette. Using Starlette directly would require manual implementation of dependency injection, validation, and OpenAPI generation — all provided by FastAPI out of the box. |

**Advantages:**
- Native async/await support for streaming LLM responses and concurrent DB queries
- Automatic OpenAPI/Swagger documentation from Pydantic models
- Built-in dependency injection system (FastAPI Depends)
- Pydantic-based request/response validation at zero additional cost
- Excellent performance (comparable to Node.js/Go)
- Large ecosystem with production-tested deployment patterns

**Disadvantages:**
- Smaller community than Django (though growing rapidly)
- Less "batteries included" — no built-in admin panel, auth system, or ORM
- Requires explicit layering (no forced MVC structure)
- Async SQLAlchemy patterns are less mature than sync

**Impact:**
- **Architecture:** Modular route structure with dependency injection
- **Performance:** Sub-10ms overhead per request vs 50ms+ for DRF
- **Development Speed:** Faster iteration due to auto-validation and auto-docs
- **Maintainability:** Clear separation between route definitions, business logic, and data access
- **Cost:** Lower compute cost due to better async throughput

**Dependencies:** None (foundation decision)

**Risks:**
- async SQLAlchemy patterns are still evolving; may encounter edge cases with complex queries
- Team must be comfortable with Python async patterns (asyncio, await, async context managers)

**Future Review:** When Django adds first-class async support and the team size grows significantly

**Related Files:**
- `backend/app/main.py` — FastAPI application entry point
- `backend/app/api/v1/` — All route definitions
- `backend/app/core/config.py` — Framework configuration
- `backend/pyproject.toml` — Dependencies

**Related ADRs:** ADR-001 (Use FastAPI for Backend API)

---

### DEC-002: Next.js over Plain React

**Date:** 2026-07-03
**Category:** Frontend, Architecture
**Status:** Implemented
**Title:** Use Next.js instead of plain React

**Context:**
The frontend needs server-side rendering for SEO on landing pages, API route
middleware for auth protection, and file-based routing to organize patient and
doctor views. A plain React app with Create React App would require additional
libraries for routing, SSR, and middleware.

**Decision:**
Use Next.js 15 with App Router, React Server Components, and Tailwind CSS for
the frontend application.

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| Create React App | No SSR, no built-in routing, requires React Router + express middleware separately. Abandoned by the React team in favor of Next.js. |
| Remix | Smaller ecosystem, fewer UI component libraries compatible, less adoption for healthcare applications. |
| Vite + React Router | Requires manual setup for SSR, auth middleware, and route organization. No file-based routing. |
| SvelteKit | Team lacks Svelte experience; TypeScript ecosystem is richer in React. |

**Advantages:**
- File-based routing maps directly to patient/doctor route organization
- React Server Components reduce client-side JavaScript bundle
- Middleware runs at the edge for auth redirects without page load
- Built-in image optimization, font loading, and performance best practices
- Massive ecosystem of React components (shadcn/ui, Radix, etc.)
- TypeScript-first development

**Disadvantages:**
- Heavier build than plain Vite
- Server Components add a new mental model (client vs server boundaries)
- App Router is relatively new (v15) and some patterns are still stabilizing
- Edge middleware has limitations (no async localStorage, no DB access)

**Impact:**
- **Architecture:** Clean separation of auth layouts, patient routes, doctor routes
- **Performance:** SSR for initial load, client-side navigation for SPA feel
- **Development Speed:** File-based routing eliminates route configuration
- **Security:** Middleware runs before page load, preventing unauthorized access

**Dependencies:** None (foundation decision)

**Risks:**
- App Router breaking changes in future Next.js releases
- Server Component boundaries can be confusing for new developers

**Future Review:** When Next.js releases a new major version or if performance
benchmarks show a better alternative

**Related Files:**
- `frontend/src/app/` — All routes and layouts
- `frontend/src/middleware.ts` — Auth guard middleware
- `frontend/next.config.ts` — Framework configuration
- `frontend/tailwind.config.ts` — Style configuration

**Related ADRs:** ADR-002 (Use Next.js for Frontend Framework)

---

### DEC-003: PostgreSQL as Primary Database

**Date:** 2026-07-03
**Category:** Database
**Status:** Implemented
**Title:** Use PostgreSQL as the primary database

**Context:**
The application stores relational healthcare data with complex relationships
(patients, doctors, medicines, appointments, chat history, adherence logs).
The database must support JSON fields for flexible AI extraction results, strong
ACID compliance for medical data integrity, and be production-ready for HIPAA
considerations.

**Decision:**
Use PostgreSQL 16 as the primary production database. Use SQLite for local
development and testing where PostgreSQL-specific features are not required.

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| MySQL | Weaker JSON support, less mature for complex queries (no CTE optimization, no partial indexes), historically weaker async driver support. |
| SQLite | Excellent for testing but lacks concurrency, connection pooling, and audit features needed for production healthcare workloads. |
| MongoDB | Document store is a poor fit for highly relational healthcare data (patient ↔ doctor ↔ medicine ↔ appointments). No ACID across multiple documents without transactions. No foreign key enforcement. |
| Amazon Aurora | Excellent for production but over-engineered for MVP. Can migrate later. PostgreSQL compatibility means minimal migration cost. |

**Advantages:**
- Mature JSONB support for flexible AI extraction schemas
- Strong ACID compliance critical for medical data integrity
- Excellent concurrency with MVCC
- Rich indexing (B-tree, GiST, GIN, partial, expression) for healthcare queries
- `pg_stat_statements` for query performance monitoring
- `uuid-ossp` and `pgcrypto` extensions for UUID PKs and token hashing
- Large ecosystem of managed hosting (Neon, RDS, Supabase, etc.)

**Disadvantages:**
- Heavier than SQLite for local development
- Connection pooling required for production (PGBouncer)
- Vacuuming required for long-running transaction-heavy workloads
- Larger Docker image than SQLite-only setups

**Impact:**
- **Architecture:** Relational model with 10 tables, 16 composite indexes, 4 check constraints
- **Performance:** Excellent query performance with proper indexing
- **Scalability:** Read replicas, connection pooling, and partitioning available when needed
- **Security:** Row-level security, SSL connections, encryption at rest
- **Cost:** Free open-source; hosting costs vary by provider

**Dependencies:** None (foundation decision)

**Risks:**
- Schema migrations must handle PostgreSQL-specific features gracefully for SQLite test compatibility
- Hosting costs scale with storage and connection count

**Future Review:** When data exceeds 10 million rows or when read replica
architecture is needed

**Related Files:**
- `backend/app/database/session.py` — Database session configuration
- `backend/app/models/` — All SQLAlchemy models
- `backend/alembic/versions/0001_initial_schema.py` — Migration
- `docker-compose.yml` — PostgreSQL service

**Related ADRs:** ADR-003 (Use PostgreSQL for Production Database)

---

### DEC-004: SQLAlchemy ORM

**Date:** 2026-07-03
**Category:** Database, Backend
**Status:** Implemented
**Title:** Use SQLAlchemy as the Object-Relational Mapper

**Context:**
The project needs an ORM to map 10 database tables to Python objects, manage
relationships (patient → medicines, doctor → patients, reports → extractions),
and support both PostgreSQL (production) and SQLite (testing) with minimal code
changes.

**Decision:**
Use SQLAlchemy 2.0 with the new-style declarative mapping (`Mapped`/`mapped_column`
annotations) and sync sessions. Async sessions are prepared for but not required
until the AI agent layer needs concurrent DB access.

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| SQLAlchemy 1.x (legacy) | Outdated patterns; SQLAlchemy 2.0 is the supported future with cleaner type hints and better async support. |
| Django ORM | Tied to Django framework (contradicts DEC-001). Cannot use without adopting Django. |
| Tortoise ORM | Async-native but less mature ecosystem, fewer third-party integrations, smaller community. |
| psycopg2 (raw SQL) | No relationship mapping, no migration tooling, requires manual query building for all operations. |
| Prisma (Python) | Python client is less mature than TypeScript version; limited ecosystem for healthcare-specific queries. |

**Advantages:**
- Mature, battle-tested ORM with 15+ years of production use
- Async support via `AsyncSession` and `asyncpg` for future AI concurrency needs
- Declarative mapping with full type hints (Pydantic-compatible)
- Relationship loading strategies (lazy, eager, selectin, joined) for N+1 prevention
- Alembic integration for migrations (see DEC-017)
- Dialect abstraction enables SQLite in testing and PostgreSQL in production
- Rich query API (filter, join, subquery, CTE, window functions)

**Disadvantages:**
- Steep learning curve for complex queries
- Sync/async duality can cause confusion (sync session vs async session)
- Lazy loading can cause N+1 problems if not carefully managed
- Some PostgreSQL-specific features require raw SQL fallbacks

**Impact:**
- **Architecture:** Clean model → repository → service separation
- **Performance:** Proper eager loading prevents N+1; query optimization via `QueryOptimizer`
- **Maintainability:** Models define schema in one place; migrations are generated
- **Testing:** SQLite in tests means fast, isolated, repeatable test runs

**Dependencies:** DEC-001 (FastAPI), DEC-003 (PostgreSQL)

**Risks:**
- Async SQLAlchemy patterns are still maturing; may encounter edge cases
- SQLite dialect differences require careful testing (JSONB → JSON, UUID handling)

**Future Review:** When async session patterns stabilize and the team needs
concurrent DB access across agents

**Related Files:**
- `backend/app/database/base.py` — `Base`, `TimestampMixin`, `UUIDMixin`, `SoftDeleteMixin`
- `backend/app/database/session.py` — Session factory
- `backend/app/models/` — All 10 model definitions
- `backend/app/database/query_optimizer.py` — Eager loading strategies

**Related ADRs:** ADR-004 (Use SQLAlchemy 2.0 ORM)

---

### DEC-005: Repository Pattern

**Date:** 2026-07-03
**Category:** Architecture, Backend
**Status:** Implemented
**Title:** Use Repository Pattern for Data Access

**Context:**
Business logic should not depend on SQLAlchemy query APIs directly. Services
need a clean interface for data access that can be mocked in tests, optimized
centrally, and kept consistent across all data operations.

**Decision:**
Implement a `BaseRepository` generic class with CRUD operations (`create`, `get`,
`get_multi`, `paginate`, `update`, `delete`). Specialized repositories extend the
base for custom queries. All database access goes through repositories — never
directly through SQLAlchemy sessions in service or API code.

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| Direct SQLAlchemy in services | Violates separation of concerns. Services become tightly coupled to ORM. Harder to test (must mock ORM), harder to optimize (queries scattered across codebase). |
| ActiveRecord pattern (Django-style) | Models contain both data and behavior. Becomes unwieldy as query complexity grows. Violates single responsibility principle. |
| CQRS with separate read/write models | Over-engineered for MVP. Adds significant complexity with minimal benefit for CRUD-heavy operations. Can be introduced later if needed. |
| Raw SQL with query builders | No ORM mapping, no type safety, no migration integration. Would require building a repository layer anyway. |

**Advantages:**
- Clean separation: API → Service → Repository → Model
- All queries are centralized — easy to optimize, log, and monitor
- Repositories are easy to mock in unit tests
- Consistent interface across all 10 data entities
- Pagination, filtering, and sorting are handled uniformly via `PageParams`/`FilterRule`/`SortRule`

**Disadvantages:**
- Boilerplate for repository registration and wiring
- Generic repository methods may not cover all specialized query needs
- Extra abstraction layer adds indirection when debugging queries

**Impact:**
- **Architecture:** API → Service → Repository → Model (4-layer)
- **Testing:** Services can be tested with mock repositories
- **Maintainability:** Adding a new query means adding a repository method, not scattering SQL in services
- **Performance:** Central eager-loading configuration prevents N+1 queries

**Dependencies:** DEC-004 (SQLAlchemy)

**Risks:**
- Over-generic repositories may abstract away database-specific optimizations
- Teams may be tempted to bypass repositories for "quick" queries, eroding the pattern

**Future Review:** When query patterns become complex enough to warrant a separate
query object pattern or CQRS

**Related Files:**
- `backend/app/repositories/base.py` — `BaseRepository`
- `backend/app/repositories/` — 8 specialized repositories
- `backend/app/repositories/__init__.py` — Repository exports
- `backend/app/database/query.py` — `PageParams`, `FilterRule`, `SortRule`, `paginate_query`

**Related ADRs:** ADR-005 (Repository Pattern for Data Access)

---

### DEC-006: Service Layer

**Date:** 2026-07-03
**Category:** Architecture, Backend
**Status:** Implemented
**Title:** Use Service Layer for Business Logic

**Context:**
API route handlers should not contain business logic. Without a service layer,
routes become bloated with mixed concerns (HTTP handling, validation, business
rules, data access). Testing business logic requires HTTP clients and full
application setup.

**Decision:**
Implement a service layer between API routes and repositories. Each service
class encapsulates a domain's business logic (e.g., `AuthService`,
`ReportService`, `EmergencyService`). Service classes receive a DB session
via constructor injection.

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| Business logic in API routes | Violates separation of concerns. Routes become untestable without HTTP. Mixed responsibility (status codes with business rules). |
| Business logic in models (Active Record) | Models become fat and violate SRP. Testability suffers. Harder to reuse logic across different API contexts. |
| Use-case / Interactor pattern (Clean Architecture) | Adds significant boilerplate with one class per use case. Can be introduced later if service classes grow too large. |

**Advantages:**
- Business logic is testable without HTTP (pure Python unit tests)
- Routes are thin: parse request → call service → format response
- Services can be composed and reused across different routes
- Service layer provides a clear boundary for transactions and error handling
- Consistent error patterns via custom exception hierarchy

**Disadvantages:**
- Extra layer of boilerplate for simple CRUD operations
- Service classes can grow large without discipline
- Constructor injection requires manual wiring (mitigated by FastAPI `Depends`)

**Impact:**
- **Architecture:** API → Service → Repository (3-layer within business logic)
- **Testing:** 10 service classes with isolated unit tests
- **Maintainability:** Clear ownership — each domain has exactly one service
- **Development Speed:** Thin routes mean faster endpoint creation

**Dependencies:** DEC-005 (Repository Pattern)

**Risks:**
- Services may become "god classes" if not kept focused on a single domain
- Transaction management across multiple repositories requires careful coordination

**Future Review:** When service classes exceed 500 lines or when cross-domain
workflows (e.g., "upload report → extract medicines → update reminder schedule")
become complex enough for a workflow/orchestration layer

**Related Files:**
- `backend/app/services/` — 10 service classes
- `backend/app/services/__init__.py` — Service exports
- `backend/app/core/exceptions.py` — Custom exception hierarchy

**Related ADRs:** ADR-006 (Service Layer for Business Logic)

---

### DEC-007: JWT Authentication

**Date:** 2026-07-11
**Category:** Security, Authentication
**Status:** Implemented
**Title:** JWT Authentication with Access and Refresh Tokens

**Context:**
The healthcare application needs stateless authentication that works across
backend API, frontend SPA, and future mobile apps. Session-based auth (cookies)
creates CSRF concerns and server-side state management overhead. The auth system
must support role-based access (patient, doctor) and token expiration for security.

**Decision:**
Use JWT-based authentication with a dual-token strategy:
- **Access token:** Short-lived (15 minutes), contains user ID and role, signed with HS256
- **Refresh token:** Longer-lived (7 days default, 30 days with "remember me"), stored
  in the database with a SHA-256 hash, supports rotation and revocation

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| Session cookies with server-side storage | Requires Redis/DB session store, CSRF protection, harder to scale horizontally. Stateful — every request hits session storage. |
| OAuth2 / OIDC with external provider | Over-engineered for MVP. Can be added as a social login option later. Built-in auth gives full control over the healthcare-specific user model. |
| API keys | No built-in expiration, no user context, no revocation without key rotation. Poor UX for browser-based applications. |
| Magic link / passwordless | Better UX but requires email infrastructure at MVP stage. Can be added alongside JWT later. |

**Advantages:**
- Stateless access tokens — no DB lookup on every request
- Short-lived access tokens minimize the damage window if a token is leaked (15 min)
- Refresh token rotation prevents replay attacks
- DB-backed refresh tokens enable server-side logout
- Works seamlessly with mobile apps and third-party integrations
- Bearer token pattern is well-understood and widely supported

**Disadvantages:**
- Token revocation for access tokens is not possible (must wait for expiry)
- Refresh tokens require DB queries (mitigated by indexed lookup)
- JWT size adds ~500 bytes to every request header
- HS256 requires careful secret key management

**Impact:**
- **Architecture:** Stateless auth with DB-backed refresh tokens
- **Security:** Short access token TTL (15 min), rotating refresh tokens, SHA-256 hashing
- **Performance:** Access token verification is O(1) — no DB call
- **UX:** "Remember me" for 30-day sessions; seamless refresh in Axios interceptor
- **Scalability:** Stateless access tokens scale horizontally without shared session store

**Dependencies:** DEC-003 (PostgreSQL for refresh token storage)

**Risks:**
- HS256 secret key rotation requires all tokens to be reissued
- Access tokens cannot be revoked; if a token is stolen, it's valid for 15 minutes
- JWT library vulnerabilities must be monitored

**Future Review:** When the system needs OAuth2 integration for EHR systems or
when RS256 is needed for microservice-to-microservice auth

**Related Files:**
- `backend/app/core/security.py` — Token creation, hashing, validation
- `backend/app/services/auth_service.py` — Registration, login, logout, refresh
- `backend/app/models/refresh_token.py` — RefreshToken model with jti, hash, revocation
- `backend/app/api/v1/auth.py` — Auth endpoints
- `backend/app/api/deps.py` — `get_current_user`, `require_role()`

**Related ADRs:** ADR-007 (JWT with Access and Refresh Tokens)

---

### DEC-008: Refresh Token Rotation

**Date:** 2026-07-11
**Category:** Security, Authentication
**Status:** Implemented
**Title:** Implement Refresh Token Rotation on Every Refresh

**Context:**
If a refresh token is stolen, the attacker can generate new access tokens
indefinitely until the refresh token expires (up to 30 days). Standard JWT
refresh patterns are vulnerable to replay attacks if a token is compromised.

**Decision:**
On every refresh token usage:
1. Revoke the old refresh token (set `is_revoked = True`)
2. Issue a completely new refresh token with a new UUID jti
3. If the old token was already revoked (reuse detection), revoke ALL tokens
   for that user — indicating a possible token theft

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| Static refresh token (no rotation) | Vulnerable to indefinite token theft. An attacker who steals a refresh token retains access until it expires. |
| Refresh token with expiration only | No reuse detection. Cannot distinguish between legitimate re-use and token theft. |
| Token binding (public key pinning) | Significantly more complex. Requires the client to generate and store a key pair. Over-engineered for MVP. |

**Advantages:**
- Replay attack prevention — a stolen token can be used at most once
- Reuse detection — token theft is detected and all sessions are revoked
- Aligns with OAuth 2.0 best practices (RFC 6749, RFC 6819)

**Disadvantages:**
- Every refresh invalidates the previous token, which can cause issues if network requests race
- Client must handle the case where a refresh succeeds but the new token is lost (race condition)
- Slightly more complex implementation than static refresh tokens

**Impact:**
- **Security:** Drastically reduces the window of vulnerability from stolen refresh tokens
- **Architecture:** DB-backed token state with `is_revoked` flag
- **UX:** The Axios interceptor has a lock/queue pattern to prevent concurrent refresh races

**Dependencies:** DEC-007 (JWT Authentication), DEC-009 (Hash Refresh Tokens)

**Risks:**
- Race condition: two concurrent refreshes could both succeed before either detects
  the other's revocation
- Mobile clients with poor connectivity may lose a new refresh token before saving it

**Future Review:** When implementing session management UI that shows active sessions
and allows remote logout

**Related Files:**
- `backend/app/services/auth_service.py` — `refresh_token()` with rotation logic
- `backend/app/models/refresh_token.py` — `RefreshToken` model
- `backend/app/repositories/refresh_token_repository.py` — Revocation queries

**Related ADRs:** ADR-008 (Refresh Token Rotation)

---

### DEC-009: Hash Refresh Tokens in Database

**Date:** 2026-07-11
**Category:** Security, Authentication
**Status:** Implemented
**Title:** Store SHA-256 Hashed Refresh Tokens

**Context:**
Refresh tokens are credentials that grant long-lived access (up to 30 days).
If the database is breached, plain-text refresh tokens would allow an attacker
to impersonate any active user indefinitely.

**Decision:**
Store refresh tokens as SHA-256 hashes in the database. The raw JWT string is
never persisted. Token verification compares the SHA-256 hash of the provided
token against the stored hash.

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| Store raw JWTs in DB | Database breach exposes all active sessions immediately. Any user with DB access could impersonate any patient or doctor. |
| Encrypt tokens with application key | More complex key management. Encryption is reversible — a key leak exposes all tokens. Hashing is one-way and more secure. |
| Store only jti (token ID) | Requires another mechanism to associate the jti with a user. Still need to verify the token signature on every refresh. |

**Advantages:**
- Database breach does not leak active sessions — hashes are computationally infeasible to reverse
- Verification is fast (SHA-256 is microseconds)
- Indexed lookups on `token_hash` are efficient
- Follows password-storage best practices (never store credentials in plain text)

**Disadvantages:**
- Cannot display the raw token to the user (they'd need to re-authenticate to see it)
- Token uniqueness collisions are theoretically possible but astronomically unlikely with UUID v4 inputs
- Extra hashing step adds ~50 microseconds per refresh

**Impact:**
- **Security:** Major — prevents long-term impersonation from DB breaches
- **Architecture:** `token_hash` column with unique index on `refresh_tokens` table
- **Compliance:** Aligns with HIPAA security rule (45 CFR §164.312) for access token protection

**Dependencies:** DEC-007 (JWT Authentication), DEC-008 (Token Rotation)

**Risks:**
- Hash algorithm must be upgraded if SHA-256 is deprecated (unlikely in the near future)
- Rainbow table attacks are not a concern because each token contains a UUID v4 jti with high entropy

**Future Review:** If SHA-256 is deprecated by NIST or if the security team recommends
bcrypt/scrypt for token hashing

**Related Files:**
- `backend/app/core/security.py` — `hash_token()` function
- `backend/app/models/refresh_token.py` — `token_hash` column

**Related ADRs:** ADR-009 (Hash Refresh Tokens in Database)

---

### DEC-010: Role-Based Access Control

**Date:** 2026-07-11
**Category:** Security, Authentication
**Status:** Implemented
**Title:** Role-Based Access Control with Patient and Doctor Roles

**Context:**
The healthcare application has two distinct user types — patients and doctors —
with entirely different permissions. Patients can view their own data, upload
reports, and chat. Doctors can view their assigned patients' data, acknowledge
alerts, and access clinical summaries. Some endpoints (admin) are reserved for
future use.

**Decision:**
Implement RBAC with two roles (`patient`, `doctor`) enforced at the FastAPI
dependency level. A `require_role()` factory dependency returns a dependency
that checks the current user's role. Route handlers declare required roles at
the decorator level.

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| Permission-based ACL (attribute-level) | Over-engineered for MVP. Would require a permission registry, role-permission mapping, and attribute-level checks. Can evolve from RBAC later. |
| Policy-based (OPA, Casbin) | Adds an entire policy engine for what is currently two roles. Useful when roles multiply (nurse, admin, pharmacist) but overkill now. |
| Row-level security (PostgreSQL RLS) | Moves authorization into the database, making it harder to debug and test. Application-level RBAC is more transparent. |

**Advantages:**
- Simple, auditable, and well-understood pattern
- FastAPI dependency injection makes RBAC declarative and testable
- Easy to verify: each route explicitly lists allowed roles
- `get_current_patient` and `get_current_doctor` dependencies provide typed access

**Disadvantages:**
- Two roles means some if/else logic in shared services
- Role checks in dependencies don't handle row-level access (patient can only see their own data)
- Adding a new role requires updating every RBAC decorator

**Impact:**
- **Architecture:** Routes declare `require_role("patient")` or `require_role("doctor")`
- **Security:** Role enforcement at the API boundary — no role check is skipped
- **Testing:** Auth tests verify every endpoint with both roles and unauthenticated access

**Dependencies:** DEC-007 (JWT Authentication)

**Risks:**
- Hard-coded role strings scattered across route decorators (mitigated by constants)
- Row-level access control must be handled separately in repositories (patient_id scoping)

**Future Review:** When adding additional roles (nurse, admin, pharmacist, system)
or when attribute-based permissions are needed

**Related Files:**
- `backend/app/api/deps.py` — `require_role()`, `get_current_patient`, `get_current_doctor`
- `backend/app/services/auth_service.py` — Role extraction from JWT

**Related ADRs:** ADR-010 (Role-Based Access Control)

---

### DEC-011: LangGraph for AI Orchestration

**Date:** 2026-07-03
**Category:** AI, LangGraph, Architecture
**Status:** Implemented
**Title:** Use LangGraph for AI Agent Orchestration

**Context:**
The system has 5 AI agents (Medical Report, Patient Chat, Emergency Detection,
Medicine Reminder, Doctor Summary) that need to execute multi-step workflows
with state management, error handling, retries, conditional branching, and
human-in-the-loop interrupts. A simple LLM-call-per-request pattern is
insufficient for these requirements.

**Decision:**
Use LangGraph (LangChain's graph-based agent framework) to build each agent as
a stateful `StateGraph` with typed state schemas, conditional edges, retry logic,
and checkpointing. The Orchestrator is a parent graph that routes to agent
subgraphs.

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| Custom state machine with if/else | Would require building graph execution, state persistence, checkpointing, and error recovery from scratch. LangGraph provides all of this. |
| LangChain Agents (legacy) | The older AgentExecutor pattern is less flexible than LangGraph for DAG-style workflows. LangGraph is the recommended replacement. |
| Semantic Kernel (Microsoft) | C#-centric ecosystem; Python support is less mature. Smaller community for healthcare AI patterns. |
| CrewAI | More focused on multi-agent collaboration with role-based agents. Less control over graph structure and state management. |

**Advantages:**
- State graph pattern maps naturally to agent workflows (state → node → edge)
- Built-in checkpointing with `PostgresSaver`/`MemorySaver`
- Human-in-the-loop via `interrupt()` for safety-critical decisions
- Conditional routing enables validation gates and escalation paths
- Subgraph composition for the Orchestrator pattern
- Streaming support for real-time token delivery
- LangSmith integration for LLM observability

**Disadvantages:**
- Relatively new framework (v0.2.x) — APIs may change
- Debugging complex graphs requires LangSmith (another dependency)
- Error messages from LangGraph internals can be opaque
- Subgraph state management requires careful schema design

**Impact:**
- **Architecture:** 5 agent subgraphs + 1 Orchestrator parent graph
- **Performance:** Graph overhead is negligible compared to LLM call latency
- **Development Speed:** LangGraph handles execution, state, and persistence
- **Safety:** Interrupts enable human review without building custom pause/resume
- **Observability:** LangSmith traces every node execution and LLM call

**Dependencies:** DEC-012 (LangChain for AI Utilities)

**Risks:**
- LangGraph API instability during development
- Team must learn graph-based thinking (nodes, edges, state, conditional routing)
- Complex error propagation across subgraphs

**Future Review:** When LangGraph reaches v1.0 or if a compelling alternative emerges

**Related Files:**
- `backend/app/langgraph/` — Graph definitions, nodes, edges
- `backend/app/agents/` — Agent implementations (medical, chat, emergency, reminder, summary)
- `project_memory/LANGGRAPH_DESIGN.md` — Complete LangGraph workflow design
- `project_memory/AI_ARCHITECTURE.md` — AI architecture with state schemas

**Related ADRs:** ADR-011 (LangGraph for Agent Orchestration)

---

### DEC-012: LangChain for AI Utilities

**Date:** 2026-07-03
**Category:** AI, LangGraph
**Status:** Implemented
**Title:** Use LangChain for AI Utility Functions

**Context:**
The project needs utility functions for LLM calls, prompt templating, token
counting, output parsing, and integration with LangSmith tracing. Building
these from scratch would be time-consuming and error-prone.

**Decision:**
Use LangChain for AI utility functions where they add value:
- `ChatOpenAI` for LLM model abstraction
- `StrOutputParser` / `JsonOutputParser` for response parsing
- LangSmith `traceable` decorator for function-level tracing
- Prompt templates (limited — prefer `PromptLoader` for healthcare prompts)

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| Direct OpenAI API calls | Lowest overhead but no LangSmith tracing, no built-in output parsing, no model abstraction for fallback chains. Would need to build all utilities from scratch. |
| Custom LLM wrapper with fallback | Building a production-grade LLM client with proper error handling, retries, fallbacks, and tracing is 200+ lines of code. LangChain provides this out of the box. |
| Instructor (python library) | Excellent for structured outputs but doesn't provide tracing, fallbacks, or the broader ecosystem. Can be used alongside LangChain for JSON mode. |

**Advantages:**
- Model abstraction with consistent interface across providers
- Built-in output parsers (JSON, string, structured)
- LangSmith tracing with zero-config integration
- Retry and fallback support via `fallbacks` parameter
- Token counting utilities

**Disadvantages:**
- LangChain API is notoriously unstable — breaking changes are frequent
- Heavy dependency tree — pulls in many transitive dependencies
- Abstraction leaks require understanding both LangChain AND the underlying API
- Over-reliance on LangChain can make debugging harder

**Impact:**
- **Architecture:** LLM calls go through `ChatOpenAI` with custom fallback chain
- **Development Speed:** Reduces boilerplate for common LLM operations
- **Observability:** LangSmith tracing is automatic for LangChain calls
- **Cost:** Minimal overhead — LangChain is a thin wrapper

**Dependencies:** None

**Risks:**
- LangChain version upgrades may break prompts or output parsing
- Vendor lock-in for LLM provider switching (mitigated by using the base client
  interface, not provider-specific features)
- Bloating the codebase with unnecessary LangChain abstractions

**Future Review:** If LangChain's API instability creates maintenance burden,
evaluate a migration to a thinner wrapper

**Related Files:**
- `backend/app/core/llm_client.py` — `LLMClient` with fallback chain
- `backend/app/prompts/` — Prompt templates (loaded via PromptLoader, not LangChain)

**Related ADRs:** ADR-012 (LangChain for LLM Utilities)

---

### DEC-013: ChromaDB for MVP Vector Database

**Date:** 2026-07-03
**Category:** AI, RAG, Database
**Status:** Implemented
**Title:** Use ChromaDB as MVP Vector Database

**Context:**
The Patient Chat Agent needs RAG (Retrieval-Augmented Generation) over patient
reports. A vector database is required to store and query document embeddings.
The MVP needs something lightweight that can run locally in Docker, requires no
external cloud service, and integrates easily with LangChain.

**Decision:**
Use ChromaDB as the vector database for MVP. It runs as a Docker container
alongside the application, supports cosine similarity search with HNSW indexing,
and stores metadata for patient-level filtering.

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| Pinecone | Managed cloud service — requires internet, has costs ($70+/month), introduces latency. Better for production at scale but overkill for MVP. Hard to migrate away from (vendor lock-in). |
| Qdrant | Excellent performance but more complex to self-host. ChromaDB's simpler API is better for rapid prototyping. Can migrate to Qdrant if ChromaDB performance is insufficient. |
| Weaviate | Requires more infrastructure (separate Docker compose, schema definitions). ChromaDB's collection-based API is simpler. |
| pgvector (PostgreSQL extension) | Eliminates the need for a separate vector database — embeddings live alongside relational data. Strongly considered but ChromaDB's HNSW index is faster at scale. pgvector is a strong candidate for post-MVP migration. |
| FAISS (in-process) | No built-in metadata filtering, no persistence without serialization, no client-server architecture. Not suitable for production. |

**Advantages:**
- Self-hosted in Docker — no cloud dependency for MVP
- Simple Python API with minimal configuration
- Built-in metadata filtering (patient_id scoping)
- HNSW indexing for fast approximate nearest neighbor search
- LangChain integration via `Chroma` vector store class
- Collection management supports isolation of different document types

**Disadvantages:**
- Less performant than Qdrant or Pinecone at very large scales (>1M vectors)
- Limited filtering capabilities compared to dedicated databases
- No built-in replication or sharding for high availability
- Community-maintained; less enterprise support than alternatives

**Impact:**
- **Architecture:** Separate vector store alongside PostgreSQL for relational data
- **Performance:** Adequate for <100K document chunks (MVP scale)
- **Cost:** Free (self-hosted in Docker)
- **Scalability:** Can be replaced with pgvector, Qdrant, or Pinecone post-MVP without
  changing the RAG pipeline interface

**Dependencies:** DEC-012 (LangChain — ChromaDB integration occurs via LangChain)

**Risks:**
- ChromaDB may not scale to production volume; migration plan needed
- Data duplication between PostgreSQL and ChromaDB requires careful sync
- ChromaDB stability at high query volumes is unproven

**Future Review:** When document count exceeds 100K chunks or when query latency
exceeds 500ms p95. Strong candidate for migration to pgvector to eliminate the
separate infrastructure dependency.

**Related Files:**
- `backend/app/rag/vector_store.py` — ChromaDB client wrapper
- `backend/app/rag/embeddings.py` — Embedding service
- `backend/app/rag/retriever.py` — Retrieval logic
- `backend/app/core/config.py` — ChromaDB connection settings

**Related ADRs:** ADR-013 (ChromaDB for MVP Vector Store)

---

### DEC-014: Store Prompts as Markdown Files

**Date:** 2026-07-14
**Category:** Prompt Engineering, AI, Backend
**Status:** Implemented
**Title:** Store Prompts as Standalone Markdown Files with Frontmatter

**Context:**
The project has 18 prompts across 6 categories (medical, chat, emergency, summary,
RAG, system). Previous prompts were hardcoded as Python string variables in
`app/prompts/*.py`. This made prompts invisible to non-developers, impossible to
version independently, and hard to review in isolation. Clinical reviewers need
to validate prompts without reading Python code.

**Decision:**
Migrate all prompts to standalone Markdown files in `backend/prompts/`. Each file
includes YAML frontmatter with version, purpose, input/output schema, guardrails,
and examples. A `PromptLoader` class loads and renders prompts at runtime.

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| Hardcoded Python strings | Original approach. Prompts embedded in Python code — invisible to reviewers, no versioning, no discoverability. Requires developer access to modify. |
| JSON files | More machine-readable but less human-editable. Markdown is more natural for long prompt text with examples. |
| YAML files | Similar to JSON — YAML is readable but Markdown is more familiar for documentation purposes. |
| Database storage | Adds query overhead for prompt loading. Prompts change infrequently so caching on disk is more efficient. |
| External prompt management tool (e.g., PromptLayer) | Over-engineered for MVP. Can be added later for A/B testing and prompt analytics. |

**Advantages:**
- Non-developers (clinicians, reviewers) can read and edit prompts in any text editor
- Each prompt has explicit versioning, author, and changelog
- `PROMPT_INDEX.md` provides a searchable central registry
- Prompts are independent of the codebase — can be reviewed in PRs without touching Python
- `PromptLoader` with caching ensures zero-overhead runtime loading
- Frontmatter enables machine-readable metadata extraction

**Disadvantages:**
- File I/O for prompt loading (mitigated by in-memory caching)
- YAML frontmatter parsing adds a dependency (`pyyaml`)
- No built-in guard against prompt drift (mitigated by version field)

**Impact:**
- **Architecture:** Prompts are external artifacts loaded by `PromptLoader`
- **Development Speed:** Prompt changes are faster — edit markdown, restart server (no code change)
- **Collaboration:** Clinical reviewers can submit PRs for prompt changes
- **Versioning:** Each prompt version is git-traceable

**Dependencies:** DEC-011 (LangGraph — prompts are used within LangGraph nodes)

**Risks:**
- Prompt files and agent code can drift apart if file paths are renamed without updating references
- No compile-time validation that prompt variables exist in the frontmatter

**Future Review:** When prompt versioning needs A/B testing or when the number
of prompts exceeds 50

**Related Files:**
- `backend/prompts/` — 18 prompt Markdown files across 6 categories
- `backend/prompts/PROMPT_INDEX.md` — Central registry
- `backend/app/core/prompt_loader.py` — `PromptLoader` class
- `project_memory/AI_WORKFLOW.md` — Updated with PromptLoader references

**Related ADRs:** ADR-014 (Markdown Prompt Files)

---

### DEC-015: Maintain project_memory as Persistent Knowledge Base

**Date:** 2026-07-11
**Category:** Documentation, Architecture
**Status:** Implemented
**Title:** Maintain `project_memory/` as the Persistent Project Knowledge Base

**Context:**
AI-assisted development sessions are stateless — each session starts fresh without
context from previous sessions. Without a persistent knowledge base, every session
requires re-explaining the project's architecture, decisions, status, and plans.
This wastes time and leads to inconsistent decisions.

**Decision:**
Create and maintain a `project_memory/` directory at the project root containing
architectural documentation, design documents, architecture decision records,
changelogs, status reports, and session notes. Every AI-assisted session reads
relevant memory files before making changes and updates them after.

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| No persistent memory / rely on human memory | Impractical for complex projects. Humans forget decisions; AI sessions have no long-term memory. Leads to repeated mistakes and re-litigated decisions. |
| Notion / Confluence wiki | External to the codebase — easily out of sync with actual code. Requires separate access, manual updates, and discipline to keep current. |
| In-code comments only | Comments explain individual code decisions but cannot capture architecture-level reasoning, design alternatives, or project-wide status. |
| GitHub Wiki | Slightly better than Notion but still external. Wikis tend to become stale because they're not part of the PR workflow. |

**Advantages:**
- Lives in the same repository as the code — versioned, reviewed in PRs, always in sync
- AI assistants can read the entire directory at session start to reconstruct full context
- Architecture Decision Records (ADRs) provide auditable decision history
- Session notes enable continuity across AI development sessions
- New contributors can read 10 files and understand the entire project

**Disadvantages:**
- Requires discipline to update after every significant change
- Documentation files can drift from implementation if not updated
- Some files (CHANGELOG, CURRENT_STATUS) need updating on every PR

**Impact:**
- **Architecture:** Project knowledge is as persistent as the code itself
- **Development Speed:** AI-assisted sessions start with full context — no ramp-up time
- **Maintainability:** Every design decision is documented with rationale
- **Collaboration:** New team members can self-onboard from project_memory

**Dependencies:** None

**Risks:**
- File count grows — `project_memory/` could become unwieldy without organization
- Outdated files are worse than no files (misleading information)

**Future Review:** When `project_memory/` exceeds 20 files, consider sub-directories
by category

**Related Files:**
- `project_memory/AI_ARCHITECTURE.md` — AI system architecture
- `project_memory/AI_WORKFLOW.md` — AI workflow documentation
- `project_memory/ARCHITECTURE_DECISIONS.md` — ADRs (ADR-001 through ADR-031)
- `project_memory/CHANGELOG.md` — Version history
- `project_memory/CURRENT_STATUS.md` — Current project state
- `project_memory/DOCUMENT_PIPELINE.md` — Document pipeline design
- `project_memory/MEDICAL_SAFETY.md` — Medical safety design
- `project_memory/LANGGRAPH_DESIGN.md` — LangGraph workflow design
- `project_memory/OBSERVABILITY.md` — Observability design
- `project_memory/ENGINEERING_ROADMAP.md` — Sprint plan to v1.0

**Related ADRs:** Referenced across all ADRs

---

### DEC-016: Docker Compose for Local Development

**Date:** 2026-07-03
**Category:** Infrastructure, DevOps
**Status:** Implemented
**Title:** Use Docker Compose for Local Development Environment

**Context:**
The application has multiple services: FastAPI backend, PostgreSQL database,
ChromaDB vector store, Redis (optional), ClamAV (virus scanning), and a Next.js
frontend. Developers need a single-command setup that works across Windows,
macOS, and Linux. Manual installation of PostgreSQL, ChromaDB, and dependencies
is error-prone and time-consuming.

**Decision:**
Use Docker Compose to orchestrate all services for local development. A single
`docker compose up` starts the entire stack. Each service (PostgreSQL 16,
ChromaDB, backend, frontend) has its own container with health checks and
dependency ordering.

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| Manual installation (brew/apt/pip) | Requires every developer to manually install PostgreSQL, ChromaDB, Python, Node.js, and dependencies. Version mismatches are common. Setup takes 30+ minutes. Different across OS platforms. |
| Dev containers (VS Code) | Great for individual IDE setup but doesn't help with CI/CD or non-VS Code users. Can be layered on top of Docker Compose. |
| Vagrant + VirtualBox | Full VM is heavier than containers. Slower startup, larger disk footprint, less portable. |
| Kubernetes (minikube / kind) | Over-engineered for local development. Adds significant complexity (ingress, service discovery, persistent volumes) for what Docker Compose handles simply. |

**Advantages:**
- Single command: `docker compose up` starts everything
- Consistent environment across all developers and CI/CD
- Services are isolated but communicate via Docker network
- PostgreSQL and ChromaDB are ephemeral — easy to reset
- Matches production deployment (Docker containers)
- Easy to add new services (Redis, ClamAV, etc.)

**Disadvantages:**
- Docker resource usage (RAM, disk) is higher than native
- Hot-reload in Docker is more complex than native development
- File permission issues on Linux (Docker runs as root)
- Network latency between containers for high-frequency DB calls

**Impact:**
- **DevOps:** New developer setup time reduced from hours to minutes
- **Architecture:** Container boundaries match service boundaries
- **Testing:** CI/CD uses the same Docker Compose configuration
- **Portability:** Works identically on Windows, macOS, and Linux

**Dependencies:** None (infrastructure decision)

**Risks:**
- Docker Desktop licensing changes (macOS/Windows) may require migration to Rancher Desktop or Colima
- Resource exhaustion on developer machines with <8GB RAM

**Future Review:** When the team grows beyond 5 developers, consider standardizing
on a remote dev environment (GitHub Codespaces, DevContainer)

**Related Files:**
- `docker-compose.yml` — Main Docker Compose configuration
- `docker-compose.dev.yml` — Development overrides (hot-reload, debug ports)
- `backend/Dockerfile` — Backend container
- `frontend/Dockerfile` — Frontend container (for preview/staging)
- `docker/postgres/init.sql` — PostgreSQL initialization

**Related ADRs:** ADR-016 (Docker Compose for Local Development)

---

### DEC-017: Alembic for Database Migrations

**Date:** 2026-07-03
**Category:** Database, Backend
**Status:** Implemented
**Title:** Use Alembic for Database Migration Management

**Context:**
The database schema evolves as the application grows. There are 10 tables with
relationships, indexes, and constraints. Without a migration tool, schema changes
must be applied manually — leading to drift between environments, lost changes,
and broken deployments.

**Decision:**
Use Alembic (SQLAlchemy's migration tool) for all database schema changes.
Migrations are hand-written for production-critical changes (constraints, indexes)
and auto-generated for routine column additions. Every migration is reviewed in
PRs alongside code changes.

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| Manual SQL scripts | No version tracking, no automatic upgrade/downgrade, no integration with SQLAlchemy models. Easy to forget scripts in one environment. |
| Auto-create tables from models (Base.metadata.create_all) | No migration path — drops and recreates tables on every deploy. Destructive in production. |
| Django-style migration (no tool needed) | Django has built-in migrations. SQLAlchemy requires a separate tool — Alembic is the standard choice. |
| Prisma migrations (TypeScript) | Prisma is a different ORM; doesn't work with SQLAlchemy models. Would require maintaining schema definitions in two places. |

**Advantages:**
- Automatic migration generation from SQLAlchemy model changes
- Version-controlled migration history (each migration is a Python file)
- Upgrade and downgrade paths for safe rollbacks
- Auto-detects new tables, columns, indexes, and constraint changes
- Branching and merging support for parallel development

**Disadvantages:**
- Auto-generated migrations must be reviewed — they can miss complex changes
- Downgrade paths are not auto-generated and require manual implementation
- Merge conflicts on migration branches are common in team environments

**Impact:**
- **Architecture:** Schema changes are versioned, reviewed, and traceable
- **Deployments:** Migrations run automatically on deploy; rollback is a command away
- **Development Speed:** Auto-generation handles 80% of migration cases
- **Reliability:** Downgrade paths ensure safe rollbacks

**Dependencies:** DEC-004 (SQLAlchemy ORM)

**Risks:**
- Long-running migrations on large tables can lock production DB
- Migration merge conflicts are a common source of deployment failures
- Hand-written production migration (0001_initial_schema.py) must perfectly match models

**Future Review:** When tables exceed 10 million rows, evaluate zero-downtime
migration strategies (gh-ost, pt-online-schema-change)

**Related Files:**
- `backend/alembic.ini` — Alembic configuration
- `backend/alembic/env.py` — Alembic environment setup
- `backend/alembic/versions/0001_initial_schema.py` — Initial migration (hand-crafted)
- `backend/app/database/base.py` — Model metadata for autogenerate

**Related ADRs:** ADR-017 (Alembic for Migrations)

---

### DEC-018: Semantic Versioning

**Date:** 2026-07-03
**Category:** Documentation, DevOps
**Status:** Implemented
**Title:** Use Semantic Versioning for All Releases

**Context:**
The project needs a consistent versioning scheme to track progress, communicate
breaking changes, and support deployment rollbacks. Without versioning, it's
impossible to know which version is deployed, what changed, or how to roll back.

**Decision:**
Follow [Semantic Versioning 2.0](https://semver.org/) format: `MAJOR.MINOR.PATCH`.
Pre-release versions use `.alpha`, `.beta`, `.rc` suffixes. Every version is:
1. Tagged in Git (`git tag v0.7.0`)
2. Documented in `CHANGELOG.md` with the Keep a Changelog format
3. Reflected in the application's `/health` endpoint response
4. Bumped only when meaningful work completes

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| Date-based versioning (2026.07.14) | Doesn't communicate breaking changes or scope. Hard to determine compatibility between versions. |
| No versioning | Every deployment is an unknown. Impossible to correlate bugs to a specific release. |
| Git SHA as version | Useful for CI/CD but not human-readable. Cannot communicate scope or breaking changes. |

**Advantages:**
- Communicates scope of changes: MAJOR = breaking, MINOR = feature, PATCH = fix
- `CHANGELOG.md` provides a human-readable history of every version
- Git tags enable instant rollback (`git checkout v0.7.0`)
- `/health` endpoint exposes version for operational visibility

**Disadvantages:**
- Requires discipline to bump correctly and update changelog
- Pre-release versions (0.x) are ambiguous about what constitutes a breaking change
- Semantic versioning is less meaningful before v1.0 (any 0.x change could be breaking)

**Impact:**
- **Architecture:** Version is a first-class concept — exposed in health endpoint, config, CI/CD
- **Deployments:** Every deploy is traceable to a version number
- **Documentation:** CHANGELOG.md serves as the canonical version history

**Dependencies:** None

**Risks:**
- Version drift — version in code may not match deployed version
- Multiple active versions in dev, staging, and prod must be tracked

**Future Review:** When transitioning from pre-release (0.x) to stable (1.x),
define what constitutes a breaking change post-1.0

**Related Files:**
- `project_memory/CHANGELOG.md` — Full version history
- `backend/app/core/health.py` — Version exposed in health endpoint
- `backend/app/core/config.py` — Version constant

**Related ADRs:** ADR-018 (Semantic Versioning)

---

### DEC-019: Clean Architecture

**Date:** 2026-07-03
**Category:** Architecture, Backend
**Status:** Implemented
**Title:** Adopt Clean Architecture / Layered Architecture

**Context:**
The backend needs a consistent, testable architecture that separates concerns
and allows independent evolution of API, business logic, and data access layers.
Without a clear architecture, code tends to become entangled — business logic
leaks into routes, query logic leaks into services, and testing becomes difficult.

**Decision:**
Adopt a layered architecture loosely inspired by Clean Architecture principles:

```
API Layer (routes) ──> Service Layer ──> Repository Layer ──> Model Layer
     │                     │                    │                   │
  HTTP concerns        Business logic        Data access        Database schema
  Request/response     Orchestration         Query building     Table definitions
  Validation           Transactions          Eager loading      Relationships
  Auth (RBAC)          Error handling        Pagination         Migrations
```

Each layer depends only on the layer below it. The API layer never accesses
repositories directly. The service layer never handles HTTP concerns.

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| Fat controllers (logic in routes) | Untestable without HTTP. Business logic coupled to request/response format. Cannot reuse logic across endpoints. |
| Flat structure (no layering) | Projects with >10 endpoints become unmaintainable. No clear ownership — every file imports from every other file. |
| Microservices | Over-engineered for MVP. Adds network overhead, deployment complexity, and data consistency challenges. Can split later if needed. |
| Event-driven / CQRS | Adds significant complexity with event buses, projections, and eventual consistency. Beneficial at scale but premature for MVP. |

**Advantages:**
- Each layer has a single responsibility and is independently testable
- API layer can be swapped (REST → GraphQL) without touching business logic
- Database can be swapped (PostgreSQL → MySQL) by changing only repositories
- New developers can understand the system by learning one layer at a time
- Consistent file organization — every feature follows the same pattern

**Disadvantages:**
- Boilerplate — every feature requires code in 4 layers
- Simple CRUD operations feel over-architected (GET/POST/DELETE with no business logic)
- Inexperienced developers may bypass layers for "quickness"
- Extra indirection when debugging — must trace through 3 layers to find a bug

**Impact:**
- **Architecture:** 4-layer backend with strict dependency direction
- **Testing:** Each layer is independently testable with mocks at the boundary
- **Maintainability:** Adding a new feature means adding code to all 4 layers — but each
  addition is isolated and predictable
- **Development Speed:** Slower initial velocity, faster velocity as the system grows

**Dependencies:** DEC-005 (Repository Pattern), DEC-006 (Service Layer)

**Risks:**
- Teams may create anemic service layers that just proxy to repositories
- Over-engineering simple operations (e.g., soft-delete requires changes in all 4 layers)

**Future Review:** When the team agrees that the architecture is causing more
overhead than it saves — typically at very small or very large scales

**Related Files:**
- `backend/app/api/` — API layer (6 route files)
- `backend/app/services/` — Service layer (10 service files)
- `backend/app/repositories/` — Repository layer (9 repository files)
- `backend/app/models/` — Model layer (10 model files)

**Related ADRs:** ADR-019 (Clean Architecture)

---

### DEC-020: Dependency Injection Throughout Backend

**Date:** 2026-07-03
**Category:** Backend, Architecture
**Status:** Implemented
**Title:** Use Dependency Injection Throughout the Backend

**Context:**
Services need access to database sessions, repositories, external API clients,
and configuration. Hard-coding these dependencies makes the system rigid,
untestable, and tightly coupled. Without DI, services would create their own
dependencies internally, making unit testing impossible without side effects.

**Decision:**
Use FastAPI's built-in dependency injection (the `Depends` function) for all
cross-cutting concerns: DB sessions, current user, authorization, repositories,
and external clients. Services receive dependencies via constructor injection.
Route handlers declare API dependencies via function parameters.

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| Global singletons (import `db` directly) | Untestable — tests cannot replace the global DB with a test instance. Hidden coupling — every import creates a dependency. |
| Service locator pattern | Hides dependencies — impossible to know what a service needs by looking at its constructor. The need to pass dependencies to a container is a code smell. |
| Manual wiring in every route | Repetitive — every route handler would create its own session, repositories, and services. Violates DRY principle. |

**Advantages:**
- Dependencies are explicit — every class declares what it needs in its constructor
- Testing is simple — pass mock repositories to the service constructor
- FastAPI's `Depends` handles lifecycle management (creates session on request,
  closes on response)
- Dependency graph is visible and verifiable at startup (no circular imports)
- Replacing a dependency (e.g., test DB → production DB) requires changing only the
  DI wiring

**Disadvantages:**
- FastAPI's `Depends` creates anonymous dependencies — stack traces show `Depends()` not
  the actual dependency name
- Constructor injection in service classes requires manual wiring for non-FastAPI contexts
  (background tasks, CLI scripts)
- Overuse of DI can make code feel "magical" — dependencies appear without explicit
  instantiation

**Impact:**
- **Architecture:** DI container (FastAPI) manages object graph and lifecycle
- **Testing:** 100% of services are testable with mock dependencies
- **Maintainability:** Adding a new dependency means adding a constructor parameter,
  not changing global state
- **Flexibility:** The entire backend's behavior can be configured at the DI level

**Dependencies:** DEC-001 (FastAPI provides the DI system)

**Risks:**
- Circular dependencies between services are possible without compiler enforcement
- Inexperienced developers may struggle to understand where dependencies come from

**Future Review:** When background task and CLI needs grow, consider a DI framework
that works outside of FastAPI (e.g., `dependency-injector`)

**Related Files:**
- `backend/app/api/deps.py` — Shared DI dependencies (current user, DB session, auth)
- `backend/app/services/auth_service.py` — Example of constructor injection
- `backend/app/api/v1/auth.py` — Example of route-level `Depends` usage

**Related ADRs:** ADR-020 (Dependency Injection)

---

---

### DEC-021: Freeze Medical Parser at MVP

**Date:** 2026-07-15
**Category:** Architecture, Backend, Business Logic
**Status:** Implemented
**Title:** Freeze Medical Parser Implementation at MVP (Extractor + Validator Only)

**Context:**
The original medical parser plan (documented in DOCUMENT_PIPELINE.md) specified 6+ modules:
extractor, validator, normalizer, confidence engine, postprocessor, document classifier,
and parser orchestrator. Only the extractor and validator were implemented. Continuing
parser module development would delay the RAG foundation (vector store, chunking, ingestion)
needed for the Patient Chat Agent and downstream agents.

The RAG pipeline is the critical path to functional AI agents. The medical parser, while
important, can be enhanced incrementally after the core AI infrastructure is operational.

**Decision:**
Freeze all medical parser development at the current MVP state (extractor + validator only).
No new parser modules (normalizer, confidence engine, postprocessor, document classifier,
parser orchestrator) will be implemented until the RAG pipeline (Vector Store Phase C,
Chunking Phase D, Ingestion Phase E) is functional.

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| Complete all parser modules first | Delays RAG foundation by 2-3 sprints. Parser modules are independent of AI infrastructure — they can be added later without breaking changes. |
| Implement parser and RAG in parallel | Increases sprint complexity and context switching. The RAG pipeline has no dependency on advanced parsing features. |
| Abandon parser entirely | Extractor + validator covers basic use cases. Normalization/classification are enhancements, not hard requirements for MVP. |

**Advantages:**
- RAG pipeline becomes the immediate priority — unblocks Patient Chat, Emergency, and Summary agents
- Parser modules can be added independently later without architectural changes
- Extractor + validator is sufficient for basic document ingestion (raw text → structured → stored)
- Keeps sprint scope focused on the critical path to functional AI

**Disadvantages:**
- Medicine parsing lacks normalization (e.g., "po" → "oral", "bid" → "twice daily")
- No confidence scoring for extracted entities
- No document-type-aware parsing (prescription vs lab report vs discharge summary treated identically)
- No post-processing cleanup of extracted data

**Impact:**
- **Scope:** Medical parser frozen at current MVP — extractor and validator only
- **Schedule:** RAG foundation work begins immediately (Phase C: Vector Store)
- **Architecture:** Parser module stubs remain in design docs; no code is removed
- **Risk:** If parser enhancements are needed sooner, they can be added as independent sprint items

**Dependencies:** None (independent decision)

**Risks:**
- Clinical users may encounter extraction quality issues that advanced modules would fix
- Normalization aliases must be documented for future implementation
- Post-processing cleanup may be needed sooner if extraction quality is poor

**Future Review:** When RAG pipeline is functional (Phase C-E complete), revisit parser
enhancements as post-MVP improvements

**Related Files:**
- `project_memory/DOCUMENT_PIPELINE.md` — Full pipeline design with all parser modules specified
- `backend/app/medical_parser/extractor.py` — Implemented (MVP)
- `backend/app/medical_parser/validator.py` — Implemented (MVP)

**Related ADRs:** ADR-021 (Freeze Medical Parser at MVP)

---

### DEC-022: Provider-Independent Embedding Layer

**Date:** 2026-07-15
**Category:** AI, RAG, Architecture
**Status:** Implemented
**Title:** Build Provider-Independent Embedding Layer

**Context:**
The original RAG design (DOCUMENT_PIPELINE.md, AI_WORKFLOW.md) hardcoded
`text-embedding-3-small` (OpenAI) as the embedding model. This created vendor
lock-in: switching to Gemini, Voyage, Cohere, or open-source models would require
rewriting the embedding integration, changing all imports, and updating the
vector store configuration.

The project already uses `google.generativeai` for Gemini LLM calls (via
`app/ai/providers/gemini_provider.py`), so Gemini embeddings are a natural fit.
However, the architecture should support any provider without code changes.

**Decision:**
Create a provider-independent embedding layer (`app/embeddings/`) separate from
the AI provider layer (`app/ai/`). Core design:

1. **BaseEmbedding ABC** — defines the interface: `embed_text()`, `embed_batch()`,
   `embed_query()`, `dimension`, `model_name`, `provider_name`, `health_check()`
2. **EmbeddingRegistry** — global registry mapping provider names to `Type[BaseEmbedding]`
3. **EmbeddingFactory** — configuration-driven instantiation via `EmbeddingFactory.create()`
4. **EmbeddingService** — high-level API for embed/batch/query with metadata tracking
5. **GeminiEmbedding** — full implementation using `google.generativeai`
6. **Future provider skeletons** — OpenAI, SentenceTransformers, Voyage (registered,
   `initialize()` raises `NotImplementedError`)
7. **EmbeddingConfig** — dataclass with provider, model, dimension, batch_size settings
8. **ReEmbeddingService** — ABC for detecting and migrating outdated embeddings

All embedding logic is in `app/embeddings/`, keeping `app/ai/` focused on LLM
inference. Provider selection is driven by `EMBEDDING_PROVIDER` config setting.

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| Keep text-embedding-3-small hardcoded | Simplest approach but creates vendor lock-in. Changing providers requires code changes across multiple files. |
| Merge embeddings into app/ai/ | Embeddings and LLM inference have different concerns (batch processing, dimension tracking, re-embedding). Keeping them separate follows single-responsibility principle. |
| Use LangChain embedding abstractions | LangChain's `Embeddings` class could wrap providers, but it introduces a heavy dependency and API instability. Custom ABC gives full control and zero external dependency. |

**Advantages:**
- Provider switching requires changing one config value (`EMBEDDING_PROVIDER`)
- New providers are added by implementing `BaseEmbedding` and registering — no other code changes
- Embedding layer is independently testable with mock providers
- ReEmbeddingService enables version migration when models change
- Gemini embeddings reuse the existing `google.generativeai` SDK
- Dimension lookup tables in each provider avoid runtime API calls for dimension metadata

**Disadvantages:**
- More initial code than a hardcoded embedding call (8 files + tests)
- Future providers with unique features (e.g., multi-vector, late interaction) may not fit the ABC
- Provider skeletons must be maintained to avoid bit-rot

**Impact:**
- **Architecture:** `app/embeddings/` as a standalone layer — separate from `app/ai/`
- **Performance:** Gemini batch embedding is efficient; dimension is cached in lookup table
- **Flexibility:** Providers are plug-and-play via `EmbeddingRegistry`
- **Maintainability:** Adding a provider = implement ABC + register + test

**Dependencies:** `google.generativeai` (existing dependency)

**Risks:**
- `google.generativeai` embedding API may change (pre-1.0 SDK)
- Provider dimension lookup tables must be updated when models change
- BaseEmbedding ABC may need extension for advanced features (sparse embeddings, late interaction)

**Future Review:** When adding a second production provider, validate that the ABC
interface covers both providers' capabilities. Extend if needed.

**Related Files:**
- `backend/app/embeddings/` — Complete embedding layer (8 files)
- `backend/app/embeddings/base_embedding.py` — BaseEmbedding ABC
- `backend/app/embeddings/embedding_registry.py` — EmbeddingRegistry
- `backend/app/embeddings/embedding_factory.py` — EmbeddingFactory
- `backend/app/embeddings/embedding_service.py` — EmbeddingService
- `backend/app/embeddings/providers/gemini_embedding.py` — Gemini implementation
- `backend/app/embeddings/providers/future/` — Provider skeletons (OpenAI, SentenceTransformers, Voyage)
- `backend/app/core/config.py` — `EMBEDDING_PROVIDER` config setting

**Related ADRs:** ADR-022 (Provider-Independent Embedding Layer)

---

### DEC-023: Prompt Management System with Versioning and Caching

**Date:** 2026-07-15
**Category:** Prompt Engineering, AI, Performance
**Status:** Implemented
**Title:** Build Prompt Management System with Versioning, Caching, and Registry

**Context:**
The Prompt Library (DEC-014) migrated all 18 prompts to standalone Markdown files
with YAML frontmatter. The `PromptLoader` class (`app/core/prompt_loader.py`)
handles file loading and rendering. However, three gaps remained:

1. **No versioning system** — prompts had a `version` field in frontmatter but no
   programmatic version comparison, history tracking, or version-aware rendering
2. **No caching** — each prompt load hit the filesystem; no shared cache across requests
3. **No registry** — no way to discover prompts by category, list available prompts,
   or preload all prompts at startup

**Decision:**
Create a Prompt Management System (`app/prompts/`) wrapping the existing `PromptLoader`:

1. **RAGPrompt** — extends the loaded prompt with `PromptVersion` (semver comparison,
   `is_compatible()`, `is_newer_than()`), content hash, and metadata
2. **RAGPromptLoader** — wraps `CorePromptLoader`, returns `RAGPrompt` instances
3. **PromptCache** — TTL+LRU cache with per-key TTL, hit/miss stats, `clear()`, `invalidate()`
4. **PromptManager** — registry with `list_categories()`, `list_prompts()`, `get_prompt()`,
   `render()`, `get_version()`, `preload_all()`, `invalidate_cache()`

The existing `PromptLoader` (`app/core/prompt_loader.py`) is preserved unchanged —
the new layer wraps it without modification.

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| Add caching/versioning to PromptLoader directly | Modifies working production code. Better to extend via wrapper (Open/Closed principle). |
| Use external prompt management service (PromptLayer, LangSmith Hub) | Over-engineered for MVP. Can be added for A/B testing and analytics post-MVP. |
| Skip caching — rely on OS filesystem cache | File I/O for every prompt load is unnecessary overhead at scale. In-memory TTL cache is simple and effective. |

**Advantages:**
- Zero changes to existing `PromptLoader` — no regression risk
- PromptManager provides a single entry point for all prompt operations
- TTL+LRU cache reduces filesystem reads; configurable per-key TTLs
- Semantic version comparison enables prompt migration detection
- `preload_all()` loads all prompts at startup for zero-latency first access
- Cache stats (hit/miss) enable monitoring of prompt loading efficiency

**Disadvantages:**
- Two layers to load a prompt (PromptManager → RAGPromptLoader → CorePromptLoader)
- PromptManager must be initialized before use (registry population)
- Cache invalidation requires manual calls when prompts change on disk

**Impact:**
- **Architecture:** `app/prompts/` wraps `app/core/prompt_loader.py` — no modification to existing code
- **Performance:** In-memory cache with configurable TTL eliminates repeated file I/O
- **Developer Experience:** Discoverable API — `list_categories()`, `list_prompts()`, version checks
- **Maintainability:** Versioning enables safe prompt updates with compatibility checks

**Dependencies:** DEC-014 (Store Prompts as Markdown Files), PromptLoader (`app/core/prompt_loader.py`)

**Risks:**
- Cached prompts may become stale if files change on disk without cache invalidation
- Two-layer design adds minor complexity for debugging prompt loading issues

**Future Review:** When adding A/B prompt testing, consider integrating with LangSmith Hub
or a dedicated prompt management platform

**Related Files:**
- `backend/app/prompts/__init__.py` — Public exports
- `backend/app/prompts/cache.py` — PromptCache
- `backend/app/prompts/loader.py` — RAGPromptLoader, RAGPrompt, PromptVersion
- `backend/app/prompts/manager.py` — PromptManager
- `backend/prompts/PROMPT_INDEX.md` — Updated with RAG prompt management docs
- `backend/app/core/prompt_loader.py` — Unchanged (wrapped by new layer)

**Related ADRs:** ADR-023 (Prompt Management System)

---

### DEC-024: Separate Retriever from Context Builder

**Date:** 2026-07-15
**Category:** AI, RAG, Architecture
**Status:** Implemented
**Title:** Maintain Separate Retriever and Context Builder Layers

**Context:**
During Phase D design, two approaches were considered: a single "RAG retriever"
that both searches and formats context, or separate layers for retrieval and
context assembly. The retrieval layer wraps the vector store and handles
semantic search with filtering. The context builder transforms raw retrieved
documents into an LLM-optimized context string.

**Decision:**
Keep `BaseRetriever` (semantic search + filtering) and `ContextBuilder`
(dedup → rank → compress → budget → citations → assemble) as completely
separate layers with distinct ABCs, registries, factories, and services.
They communicate via `RetrievedDocument` → `ContextBuilder.build()`.

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| Single RAG retriever class | Violates single-responsibility principle. Retrieval (search + filter) and context assembly (dedup, rank, compress, format) are different concerns with different testability requirements. |
| Merge into the RAG Engine later | Pre-mature coupling. Keeping them separate now enables independent testing and provider swapping. They can be composed in the RAG Engine. |

**Trade-offs:**
- **Advantage:** Each layer is independently testable (57 + 67 tests)
- **Advantage:** Providers can be swapped independently (vector vs hybrid retriever; different budget strategies)
- **Advantage:** Context Builder works with any retriever — it only needs `RetrievedDocument` objects
- **Disadvantage:** Extra abstraction layer between search and LLM call
- **Disadvantage:** Slightly more code than a unified class

**Consequences:**
- `RetrieverService.search()` returns `list[RetrievedDocument]` → `ContextBuilder.build()` accepts them
- RAG Engine will compose: query → retriever → context builder → LLM → response
- Each layer follows the same ABC → Registry → Factory → Provider → Service pattern

**Related Files:**
- `backend/app/retrieval/` — 13 files
- `backend/app/context/` — 10 files

---

### DEC-025: Context Builder Responsible for Token Budgeting

**Date:** 2026-07-15
**Category:** AI, RAG, Performance
**Status:** Implemented
**Title:** Context Builder Owns Token Budget Management

**Context:**
Retrieved documents often exceed the LLM's context window. Token budgeting
must happen somewhere in the pipeline: in the retriever (limit results), in
the context builder (compress results), or in the LLM call (truncate prompt).
Each approach has different implications for answer quality.

**Decision:**
The `ContextBuilder` owns all token budget management via `TokenBudgetManager`.
Three strategies are implemented:
1. **fixed_max** — hard token cap, drops fragments from the end
2. **priority_truncation** — drops lowest-priority fragments when over budget
3. **section_preserve** — keeps complete sections, drops lowest-priority section

The retriever should return more results than fit in the context (e.g., top_k=20
for a 4096-token budget), and the Context Builder intelligently selects the best
subset.

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| Limit `top_k` in retriever | Blind truncation — may miss relevant but lower-ranked results that would be preferred by section priority. No budget awareness. |
| Let the LLM truncate | Wastes tokens on irrelevant content. LLMs are poor at ignoring context they've already received. Expensive on token-based billing. |
| Truncate in the RAG Engine | Duplicates logic. Context Builder already has all the information (scores, sections, metadata) needed for intelligent truncation. |

**Trade-offs:**
- **Advantage:** Intelligent section-aware budgeting preserves critical medical sections
- **Advantage:** Same budget logic serves all consumers (Chat Agent, Summary Agent, etc.)
- **Advantage:** Testable in isolation — 9 tests for the 3 strategies
- **Disadvantage:** Token estimation is heuristic (~3 chars/token); may be imprecise for non-English text
- **Disadvantage:** Section_preserve strategy may drop relevant fragments from non-priority sections

**Consequences:**
- `ContextConfig.strategy` selects the budget algorithm
- `ContextConfig.max_tokens` defines the budget
- `ContextConfig.priority_sections` controls section ordering for strategies 2 and 3
- Future: add strategy='sliding_window' for long-document Q&A

**Related Files:**
- `backend/app/context/token_budget.py` — `TokenBudgetManager`, `estimate_tokens()`
- `backend/app/context/config.py` — `ContextConfig.strategy`, `.max_tokens`, `.priority_sections`
- `backend/app/context/models.py` — `TokenUsageInfo`

---

### DEC-026: Provider-Independent Vector Store

**Date:** 2026-07-15
**Category:** AI, RAG, Architecture
**Status:** Implemented
**Title:** Build Provider-Independent Vector Store Layer

**Context:**
The original RAG design hardcoded ChromaDB as the vector database. While
ChromaDB is excellent for MVP (free, self-hosted, simple API), the project
needs the ability to migrate to other providers (Qdrant, Weaviate, Pinecone,
pgvector) without rewriting the retrieval pipeline.

**Decision:**
Create a provider-independent vector store layer (`app/vector_store/`) following
the same ABC → Registry → Factory → Provider → Service pattern used by the
embedding and AI provider layers:

1. `BaseVectorStore` ABC — defines the interface
2. `VectorStoreRegistry` — provider registration
3. `VectorStoreFactory.create()` — config-driven instantiation
4. `VectorService` — high-level API with error handling and logging
5. `ChromaDBStore` — full ChromaDB implementation (active)
6. Future provider skeletons: QdrantStore, WeaviateStore, PineconeStore

Provider selection is driven by `VectorStoreConfig.provider`.

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| Hardcode ChromaDB everywhere | Fastest implementation but creates vendor lock-in. Changing vector databases would require rewriting every file that imports ChromaDB. |
| Use LangChain's vector store abstractions | LangChain has `VectorStore` wrappers but they're tightly coupled to LangChain's embedding interface. Our custom ABC gives full control and zero external dependency. |
| Use pgvector (PostgreSQL extension) | Eliminates the separate database but adds migration complexity. ChromaDB is better for rapid prototyping. pgvector is a strong post-MVP candidate. |

**Trade-offs:**
- **Advantage:** Zero code changes to switch vector databases — change `provider` in config
- **Advantage:** New providers implement `BaseVectorStore` — no other code changes
- **Advantage:** In-memory mock store for testing without ChromaDB running
- **Advantage:** 94 tests across all vector store components
- **Disadvantage:** Some provider-specific features (e.g., Qdrant's geo-filtering) may not fit the ABC
- **Disadvantage:** More initial code than hardcoded ChromaDB

**Consequences:**
- `RetrieverService` takes a `VectorService` instance — completely provider-agnostic
- Future: migrate to pgvector to eliminate the separate ChromaDB infrastructure dependency
- Future: add QdrantStore for production-scale deployments

**Related Files:**
- `backend/app/vector_store/` — 14 files
- `backend/app/vector_store/base_vector_store.py` — ABC
- `backend/app/vector_store/providers/chromadb_store.py` — ChromaDB implementation
- `backend/app/vector_store/vector_service.py` — High-level API

---

### DEC-027: Free-Tier-First Architecture

**Date:** 2026-07-15
**Category:** Architecture, Infrastructure, Business Logic
**Status:** Implemented
**Title:** Maintain Free-Tier-First Architecture for Entire MVP

**Context:**
The MVP must be demonstrable to stakeholders and potential investors without
requiring them to sign up for paid services, enter credit card information,
or provision cloud infrastructure. Every component in the stack must be
available at no cost while still providing production-quality functionality.

**Decision:**
Every technology dependency in the MVP stack is either free open-source or
has a free API tier sufficient for development and demonstration:

| Component | Technology | Cost | Rationale |
|-----------|-----------|------|-----------|
| LLM | Gemini API (Google) | Free | 60 requests/minute free tier — sufficient for MVP |
| Embeddings | Gemini Embedding API | Free | Included in Gemini free tier |
| Vector Store | ChromaDB | Free | Self-hosted in Docker; no license cost |
| Database | PostgreSQL | Free | Open-source; self-hosted in Docker |
| OCR | Tesseract (local) + Google Vision | Free | Tesseract is free; Google Vision has free quota |
| Backend | FastAPI + Uvicorn | Free | Open-source |
| Frontend | Next.js + React + shadcn/ui | Free | Open-source |
| Containerization | Docker + Docker Compose | Free | Open-source |
| CI/CD | GitHub Actions | Free | Public repo; 2000 min/month free |
| Monitoring | Loguru (local logging) | Free | Open-source |

Explicitly excluded from MVP (despite being commonly used):
- OpenAI API (paid beyond small credits)
- Pinecone (paid — $70+/month)
- Redis Cloud (free tier exists but not needed for MVP)
- AWS/Azure/GCP cloud services (no cloud deployment until Phase 9)
- Any service requiring a credit card for initial setup

**Alternatives Considered:**

| Alternative | Reason for Rejection |
|-------------|----------------------|
| OpenAI API | Requires credit card and paid credits. Gemini free tier provides equivalent functionality at zero cost. |
| Pinecone vector store | $70+/month for production tier. ChromaDB is free and self-hosted. |
| AWS Textract OCR | Pay-per-page. Tesseract is free; Google Vision has free tier. |
| Managed cloud deployment | Requires paid hosting. Local Docker deployment is free. |

**Trade-offs:**
- **Advantage:** Zero-cost barrier for stakeholders to evaluate the MVP
- **Advantage:** No credit card required for any dependency
- **Advantage:** All code runs locally — no internet dependency for core functionality
- **Advantage:** Easy migration path — each free component has a paid upgrade path
- **Disadvantage:** Gemini free tier has rate limits (60 req/min) — may need optimization
- **Disadvantage:** ChromaDB may not scale to production volume; migration plan needed
- **Disadvantage:** Self-hosted databases require local setup (Docker)

**Consequences:**
- Provider-independent architecture enables upgrading individual components without architectural changes
- When MVP is validated, upgrade path: ChromaDB → Qdrant/Pinecone, Gemini → GPT-4o, local → cloud
- Rate limiting and queue management must handle Gemini free tier constraints
- All AI infrastructure layers (AI, embeddings, vector store, retrieval) support provider switching via config

**Related Files:**
- `backend/app/core/config.py` — Provider selection settings
- `backend/app/embeddings/providers/gemini_embedding.py` — Free-tier embedding
- `backend/app/vector_store/providers/chromadb_store.py` — Free-tier vector store
- `docker/docker-compose.yml` — Self-hosted infrastructure

---

*End of Decision Log — Last updated: 2026-07-15*
