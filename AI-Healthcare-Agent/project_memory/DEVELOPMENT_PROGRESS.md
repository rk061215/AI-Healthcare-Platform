# Development Progress

> Project diary tracking every completed task, decision, and lesson learned.
> New entries are appended — never delete previous entries.

---

## Entry 001 — Project Initialization & Foundation

**Date:** 2026-07-03
**Version:** 0.1.0
**Feature:** Foundation Phase (Complete Project Scaffold)

### Files Created
- `frontend/` — Next.js 15, Tailwind CSS, shadcn/ui, TypeScript, Zustand, Axios, React Hook Form, Zod
- `backend/` — FastAPI, SQLAlchemy, Alembic, Pydantic, JWT security, bcrypt
- `docker/` — Docker Compose for PostgreSQL 16 + ChromaDB
- `scripts/` — setup.ps1, migrate.sh
- `.github/workflows/` — CI/CD for backend and frontend
- `docs/` — Architecture documentation
- 10 SQLAlchemy models, 10 Pydantic schemas, 9 repositories, 10 services, 6 API routers
- 5 LangGraph agent skeletons with orchestrator
- RAG system skeletons (embeddings, vector store, retriever)
- OCR system skeletons (Google Vision, preprocessor)
- 4 prompt templates, 2 background task skeletons
- 7 shadcn/ui primitives, 4 shared components
- 12 frontend pages, 3 layouts, middleware auth guard
- Full test infrastructure with 5 initial auth tests

### Files Modified
- None (initial creation)

### Why
Establish the complete project scaffold so all future development has a consistent foundation, coding standards, and architecture patterns in place.

### Implementation Summary
Created a production-ready monorepo with clean architecture separation (API → Service → Repository → Model), full TypeScript/Python type safety, dark mode, responsive layouts, JWT auth scaffolding, LangGraph agent structure, RAG pipeline skeleton, and Docker-based infrastructure.

### Problems Faced
- Ensuring SQLAlchemy UUID types work across PostgreSQL and SQLite (test)
- Maintaining consistent naming across Python and TypeScript codebases
- Configuring shadcn/ui to work with Next.js App Router

### How They Were Solved
- Used SQLAlchemy's generic `UUID` type with PostgreSQL dialect fallback
- Established naming conventions table in PROJECT_PLAN.md
- Followed shadcn/ui official Next.js setup guide with `components.json`

### Lessons Learned
- Always establish folder structure and naming conventions before writing code
- Docker Compose is essential for reproducible development environments
- Investing in CI/CD from day one prevents integration issues later
- shadcn/ui's CSS variable approach makes theming straightforward

### Next Recommended Task
Implement production-ready authentication (Phase 2)

---

## Entry 002 — Production Authentication System

**Date:** 2026-07-11
**Version:** 0.2.0
**Feature:** Authentication (Register, Login, Logout, Refresh, Me, RBAC)

### Files Created
- `backend/app/models/refresh_token.py` — RefreshToken SQLAlchemy model (jti, token_hash, user_id, role, is_revoked, expires_at)
- `backend/app/repositories/refresh_token_repository.py` — RefreshToken CRUD, revocation, cleanup
- `project_memory/` — Persistent project memory system (10 documentation files)

### Files Modified
- `backend/app/models/patient.py` — Added `terms_accepted`, `terms_accepted_at`
- `backend/app/models/doctor.py` — Added `hospital_name`, `years_of_experience`
- `backend/app/core/config.py` — Added `JWT_REFRESH_TOKEN_REMEMBER_ME_DAYS`, reduced access token to 15min
- `backend/app/core/security.py` — Added `hash_token()`, `create_token_pair()`, enhanced `create_refresh_token()` with jti
- `backend/app/schemas/auth.py` — Production-grade validation: password strength (8+ chars, upper, lower, digit, special), phone E.164, DOB, gender enum, terms_accepted, confirm_password match
- `backend/app/services/auth_service.py` — Complete rewrite: register (patient/doctor), unified login, logout with revocation, refresh with rotation, get_current_user
- `backend/app/api/v1/auth.py` — 6 unified endpoints: register/patient, register/doctor, login, logout, refresh, me
- `backend/app/api/deps.py` — Enhanced with `require_role()` factory, better error headers
- `backend/app/models/__init__.py` — Added RefreshToken export
- `backend/app/repositories/__init__.py` — Added RefreshTokenRepository export
- `backend/tests/conftest.py` — Stronger passwords, new fixtures
- `backend/tests/test_api/test_auth.py` — 18 comprehensive tests
- `frontend/src/types/index.ts` — Enhanced with PatientUser, DoctorUser, UserProfile types
- `frontend/src/lib/store/auth-store.ts` — Added rememberMe, isLoading, setTokens, getRole
- `frontend/src/services/api-client.ts` — Refresh queue, failed request retry pattern
- `frontend/src/services/auth.ts` — Unified login(), logout(), getMe()
- `frontend/src/app/(auth)/login/page.tsx` — Complete rewrite with remember me, unified login
- `frontend/src/app/(auth)/register/page.tsx` — Complete rewrite with 2-step wizard
- `frontend/src/middleware.ts` — Role-based redirects with cookie parsing
- `frontend/src/app/patient/layout.tsx` — Server-side logout call
- `frontend/src/app/doctor/layout.tsx` — Server-side logout call
- `PROJECT_PLAN.md` — Updated with Phase 2 completion
- `TASKS.md` — 15 auth tasks marked complete, 96 total tasks
- `CHANGELOG.md` — Version 0.2.0 entry

### Why
Authentication is the first production feature and security foundation for a healthcare application. The existing skeleton auth was not production-ready — missing password validation, token revocation, unified login, remember me, and proper error handling.

### Implementation Summary
Built a complete production-ready authentication system with:

**Backend:**
- 6 API endpoints following RESTful conventions
- RefreshToken model for DB-backed token management
- Token rotation (revoke old, issue new on every refresh)
- Strong password validation (8+ chars, uppercase, lowercase, number, special)
- Phone validation (E.164), email validation, DOB validation, gender validation
- Remember Me: 7-day default vs 30-day refresh tokens
- Role-based access control with reusable FastAPI dependencies
- 18 automated tests covering all auth flows

**Frontend:**
- Unified login page with role toggle and remember me checkbox
- 2-step registration wizard (role selection → full form)
- Client-side password validation matching server rules
- Axios interceptor with refresh queue (prevents concurrent refresh storms)
- Middleware with role-based redirect parsing Zustand cookies
- Server-side logout API call before clearing local state

### Problems Faced
1. **AuthResponse model conflict**: The `/refresh` endpoint doesn't need to return user data, but the `AuthResponse` schema required it. Created a separate `RefreshResponse` model.
2. **Token hash calculation**: Needed to ensure consistent SHA-256 hashing between token creation and verification. Extracted `hash_token()` utility function.
3. **Concurrent refresh storms**: Multiple 401 responses could trigger parallel refresh calls. Implemented a queue pattern that holds failed requests during refresh and retries them atomically.
4. **Refresh token reuse detection**: Required storing token hash in DB and comparing on each refresh. Implemented `token_hash` column + comparison in refresh flow.
5. **Zustand cookie parsing in middleware**: Next.js middleware runs on the edge and can't access localStorage. Parsed the Zustand persist cookie to determine auth state.

### How They Were Solved
1. Separate response models for auth vs refresh
2. Centralized `hash_token()` in `security.py` using `hashlib.sha256`
3. Queue-based interceptor pattern with `isRefreshing` lock and `failedQueue` array
4. SHA-256 token hash stored in `refresh_tokens` table, compared on each refresh
5. `JSON.parse(decodeURIComponent(cookie))` in middleware to read auth state

### Lessons Learned
- Always separate response models when endpoint semantics differ
- Token rotation is critical for refresh token security
- The Axios interceptor queue pattern prevents race conditions in auth refresh
- DB-backed refresh tokens add complexity but enable critical security features (logout, revocation)
- Next.js middleware is powerful but limited — can't use async localStorage APIs
- Testing auth flows requires careful fixture management (unique emails, proper password format)

### Next Recommended Task
Integrate Google Cloud Vision API for OCR (Phase 4)

---

## Entry 003 — Production Data Layer (Sprint 3B)

**Date:** 2026-07-14
**Version:** 0.4.0
**Feature:** Production Data Layer (Migration, Seed, Health, Backup, Reset, N+1 Prevention)

### Files Created
- `backend/app/core/seed.py` — `SeedData` class with 30+ records across all 10 tables
- `backend/app/core/health.py` — `DatabaseHealthChecker` with `HealthResult`/`DatabaseHealth`
- `backend/app/core/backup.py` — `BackupManager` with verify, list, cleanup, timeout
- `backend/app/core/database_reset.py` — `DatabaseReset` with dialect-aware truncate
- `backend/app/database/query_optimizer.py` — `QueryOptimizer` with eager-loading strategies
- `backend/tests/test_api/test_database_integration.py` — 44 integration tests

### Files Modified
- `backend/alembic/versions/0001_initial_schema.py` — Full rewrite matching all 10 models
- `backend/app/api/v1/health.py` — Enhanced `/api/v1/health` and `/api/v1/health/details`
- `backend/tests/test_api/test_database_reset.py` — 5 updated tests
- `backend/tests/test_api/test_health.py` — 4 updated tests
- `project_memory/DATABASE_DOCUMENTATION.md` — Full rewrite with schema, indexes, ER diagram
- `project_memory/CHANGELOG.md` — Version 0.4.0 entry
- `project_memory/CURRENT_STATUS.md` — Updated to v0.4.0
- `TASKS.md` — 7 Sprint 3B tasks marked complete

### Why
The original Alembic migration was auto-generated from an earlier model state and didn't match current models. The project needed a production-grade data layer with verified relationships, proper indexes, seed data for development, health monitoring, backup infrastructure, and N+1 query prevention.

### Implementation Summary
Built a complete production PostgreSQL layer:

**Migration:** Hand-crafted `0001_initial_schema.py` matching all 10 SQLAlchemy models with 16 composite indexes, 4 check constraints, FK ondelete actions (CASCADE/SET NULL), soft-delete columns, and auto-update `updated_at` triggers.

**Seed Data:** `SeedData` class with realistic healthcare data (patients with conditions, doctors with specializations, reports with OCR fields, appointments spanning dates, adherence logs with mixed statuses, emergency alerts with different risk levels). Admin doctor email `admin@healthcare.com`.

**Utilities:**
- `DatabaseHealthChecker` — Connection latency, table existence, migration revision, PostgreSQL pool/index stats
- `BackupManager` — `pg_dump`, verify (validates SQL header), list (human-readable), periodic cleanup (30-day retention), error handling
- `DatabaseReset` — Schema verification via `inspect()` (works on SQLite + PostgreSQL), dialect-aware truncate, seed data delegation

**Query Optimization:** `QueryOptimizer` with per-model eager-loading strategies using `selectinload`; `paginate_with_optimization()` combining pagination, sorting, filtering with automatic N+1 prevention.

**Testing:** 44 new integration tests covering model verification (column types, nullable, defaults), relationship cascades (CASCADE delete, SET NULL), composite/uniqueness constraints, pagination (page/offset validation, emptiness), filtering by all relevant fields, sorting ascending/descending, N+1 detection via SQLAlchemy logging, seed data existence/correctness, health check responses, database reset flow, and soft-delete behavior. All 124 tests pass.

### Problems Faced
1. **Migration drift** — Original auto-generated migration referenced nonexistent columns; had to rewrite from scratch as a single-revision target
2. **SQLite vs PostgreSQL dialect differences** — `TRUNCATE` not supported in SQLite, `pg_stat_activity` / `pg_indexes` not available, `gen_random_uuid()` not available
3. **N+1 detection** — Counting emitted queries in tests required SQLAlchemy event listeners; had to set up per-test
4. **bcrypt version warning** — `(trapped) error reading bcrypt version` from incompatible `bcrypt.__about__` module; non-blocking

### How They Were Solved
1. Hand-crafted migration with all columns, indexes, constraints explicitly defined
2. Added dialect guards (`if "postgresql" in str(engine.url)`) for PG-specific features; used `inspect()` for cross-dialect schema verification
3. Used SQLAlchemy `before_cursor_execute` event with a counter for N+1 detection tests
4. bcrypt warning identified as non-blocking; no code changes needed

### Lessons Learned
- Auto-generated Alembic migrations are fragile — hand-craft for production
- Always design for dialect compatibility when the test DB differs from production
- A single `QueryOptimizer` with per-model strategies is simpler and more maintainable than per-endpoint optimization
- The `inspect()` API is powerful for dialect-agnostic schema inspection
- Integration tests with `before_cursor_execute` counters can reliably detect N+1 queries
- Soft delete at the database level (deleted_at + deleted_by columns) is a good scaffolding pattern even before implementing query-level filtering

### Next Recommended Task
Integrate Google Cloud Vision API for OCR (Phase 4)
