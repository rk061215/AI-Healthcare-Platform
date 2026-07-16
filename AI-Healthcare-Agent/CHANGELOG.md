# Changelog

All notable changes to the AI Healthcare Follow-up Assistant project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-07-16

### Added

#### Phase R — GA Readiness & Final Polish

##### Security Hardening (Part 1)
- **CSRF fix**: replaced origin substring matching (`if allowed in url`) with strict scheme+host+port tuple comparison — closes `localhost:3000.evil.com` bypass
- **PostgreSQL rate limiter**: `PostgresRateLimiter` backed by `rate_limits` table; configurable via `RATE_LIMIT_PROVIDER` setting (`"in_memory"` default, `"postgres"` for production)
- `RateLimiterFactory` abstraction for provider selection

##### UX Polish (Part 2)
- Active nav link highlighting in sidebar (`usePathname()` matching) — both patient & doctor layouts
- Modal focus trapping + Escape key handler in reports page
- Dashboard loading states with `LoadingState` component — both patient & doctor
- Medicines page error toast: silent error swallow replaced with `toast.error()`

##### Deployment Hardening (Part 3)
- Docker image versions pinned:
  - `python:3.12.9-slim` (was `3.12-slim`)
  - `node:20.18-alpine` (was `20-alpine`)
  - `chromadb/chroma:0.5.23` (was `:latest`)
- `render.yaml`: Render Blueprint for backend (Docker, free) + frontend (Node standalone, free)
- `vercel.json`: Vercel deployment config (Next.js, API rewrites, security headers)
- `docker/nginx.conf`: Production Nginx reverse proxy with SSL, WebSocket, rate limiting

##### Configuration Review (Part 4)
- Audited all 81 settings in `config.py` vs both `.env.example` files
- Added 35 missing variables to `backend/.env.example` (OCR, Security, Document Storage, Rate Limiting, Appointment Management, Gemini/Embedding)

##### Phase Q Validation Reports (generated)
- `DEPLOYMENT_VALIDATION.md`: 30 PASS / 12 WARNING / 0 FAIL
- `END_TO_END_WORKFLOW_VALIDATION.md`: 5 scenarios fully traced
- `DEMO_WORKFLOWS.md`: 5 interview-ready demonstration workflows
- `SECURITY_VALIDATION_REPORT.md`: 8 PASS / 2 WARNING / 0 FAIL
- `PERFORMANCE_BENCHMARKS.md`: 15 measurement points
- `STRESS_TESTING_PLAN.md`: 6 stress test areas
- `UX_REVIEW.md`: 4 P0 / 6 P1 / 10 P2 issues identified
- `REAL_WORLD_READINESS_REPORT.md`: Overall 7.1/10
- `NEXT_RECOMMENDATIONS.md`: 7 bugs, 5 optimizations, v1.1 features, startup roadmap
- `DEPLOYMENT_HARDENING_REPORT.md`: Image pinning + deployment review

## [1.0.0-rc.1] — 2026-07-16

### Added

#### Phase P — Production Hardening (`backend/app/services/appointment/`)

##### Appointment Service Refactoring
- Extracted `AppointmentService` (699 lines → 249 lines) by delegating to focused sub-services
- `AppointmentAvailabilityService` — availability CRUD, available slot computation
- `AppointmentRecurringService` — recurring appointment generation with conflict checking
- Both sub-services in `backend/app/services/appointment/` package

##### Frontend Test Suite
- Introduced 40-unit test suite across services (auth, chat, reports, medicines, demo, patients, doctor), stores (auth, UI), and HTTP interceptors
- Vitest configured with jsdom, path aliases, and test-utils setup
- All 40/40 tests passing

##### Persistent Providers (PostgreSQL)
- `PostgresStore` — full `BaseMemoryStore` implementation on JSONB columns (content + metadata)
- `PostgresCheckpointStore` — full `BaseCheckpointStore` implementation for LangGraph checkpoints
- Models: `MemoryEntryModel`, `CheckpointEntry` with reusable abstract base
- Configurable via `CHECKPOINT_PROVIDER` setting; defaults to `"in_memory"`

##### CI/CD & Security
- Frontend CI: added `test` job (npm ci → npm run test:run)
- Backend CI: includes pytest with coverage reporting
- `backend/.env.example`: added SENTRY_DSN, LANGSMITH_API_KEY, CHECKPOINT_PROVIDER, Gemini/AI config, backup, and OpenTelemetry variables
- `root .env.example`: already included SENTRY_DSN and LANGSMITH_API_KEY

##### Cleanup
- Removed duplicate `python-jose==3.3.0` and `httpx==0.28.1` from `requirements.txt`
- Added missing `__init__.py` to `validation/dataset/fixtures/`
- Removed fragile `api-client.test.ts` (interceptor behavior tested indirectly via service tests)

## [0.19.0] — 2026-07-16

### Added

#### Phase N — Frontend UI Polish, Demo Mode, Observability & Deployment (`frontend/`, `app/demo/`, `app/monitoring/`, `app/security/`)

##### Real Document Datasets (`datasets/`)
- 9 medical document types with real clinical data: Prescription, CBC Report, Lipid Profile, Thyroid Panel, Kidney Function Test, Liver Function Test, Diabetes Panel, Radiology Report, Discharge Summary
- JSON and JSONL dataset files with standardized schemas
- Dataset import, benchmark, and extraction statistics scripts (`scripts/`)
- Mock embedding and QA generation for demo/testing workflows

##### Frontend UI Polish (`frontend/`)
- **Chat Page**: conversation UI with message bubbles, streaming-like responses, inline citations with source highlighting, confidence score display, suggested questions panel
- **Reports Page**: drag-drop file upload with progress indicator, processing pipeline visualization (stages: Upload → Parse → Chunk → Embed → Store), detailed report view with extracted sections and metadata
- **Medicines Page**: filterable/sortable medicine grid (name, dosage, frequency, adherence, prescribed date), adherence tracking with visual indicators, search and category filtering

##### Demo Mode (`app/demo/`)
- Backend API endpoints: `/api/demo/login` (auto-auth with demo credentials), `/api/demo/reset` (reset demo state), `/api/demo/seed` (seed sample data)
- Frontend guided demo page with step-by-step walkthrough
- Demo service (`DemoService`) for managing demo state and data seeding
- Login page "Try Demo" button for instant access

##### Demo Scenarios (`scripts/demo_scenarios.py`)
- 5 pre-built demo scenarios: Patient Follow-up, Medication Adherence, Lab Results Review, Emergency Detection, Doctor Summary
- Each scenario includes scripted conversation flow with expected responses

##### Observability (`app/monitoring/`)
- Structured logging: JSON format output, rotating file handlers (daily rotation, 30-day retention), per-request correlation IDs via middleware
- In-process metrics collector: counters (requests, errors, documents processed), histograms/latencies (API endpoint durations, retrieval times, LLM inference times), error tracking by type and endpoint
- Monitoring endpoints: `GET /health` (overall), `GET /ready` (readiness), `GET /live` (liveness), `GET /metrics` (Prometheus-formatted metrics data)

##### Security Hardening (`app/security/`)
- Rate limiting middleware: configurable per-endpoint limits, IP-based tracking, sliding window algorithm, in-memory and Redis backends
- Security headers middleware: CORS, HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
- CSRF protection: double-submit cookie pattern, exempt endpoints configuration, optional header-based validation
- Input validation utilities: sanitization helpers, schema validation wrappers, SQL injection protection
- Security audit script (`scripts/security_audit.py`) — checks 15 security categories with scoring

##### Deployment (`deploy/`)
- Production docker-compose: backend API, frontend SPA, PostgreSQL, Redis, Nginx reverse proxy, automatic SSL via Let's Encrypt
- Deployment guides for Render, Railway, and VPS (manual + Docker-based)
- Deployment readiness check script (`scripts/check_deployment_readiness.py`) — verifies environment variables, database connectivity, Redis, disk space, and security settings

### Documentation
- CHANGELOG.md — Phase N entry
- CURRENT_STATUS.md — v0.19.0, 99% progress, 9.2/10 health
- SYSTEM_READINESS.md — updated to 9.0+/10
- RELEASE_NOTES_v0.19.0.md — professional release notes
- SESSION_NOTES.md — Phase N session documentation
- DEPLOYMENT_GUIDE.md — Render, Railway, VPS deployment instructions
- SECURITY.md — updated with security hardening details

##### Repository Polish & Portfolio Release
- Complete README rewrite — architecture diagrams, badges, tech stack, statistics, screenshots section
- Added CODE_OF_CONDUCT.md, SUPPORT.md, ROADMAP.md (GitHub community standards)
- Added issue templates (bug, feature, documentation) and PR template
- Created assets/README.md with screenshot capture guide
- Removed generated files (AUDIT_REPORT.md, RUNTIME_INTEGRATION_REPORT.md)
- All documentation updated to consistently reference v0.19.0
- Repository now presentation-ready for portfolio, resume, and internship applications

## [0.18.0] — 2026-07-16

(Skipped — Phase N consolidated into v0.19.0)

## [0.17.0] — 2026-07-16

### Added

#### Phase M — Clinical Validation, Dataset Management & AI Optimization (`app/validation/`)

- Dataset management: ground truth data classes (10 document types, 4 difficulty levels, 10 categories), JSON/JSONL loader/saver, CRUD manager, structural validator, train/val/test splitter, sample golden QA fixture
- Benchmark system: 12 metrics (retrieval recall, precision@K, MRR, NDCG, citation P/R/F1, groundedness, answer relevance, hallucination rate, latency, memory, tokens), configurable runner with warmup + multi-run, suite aggregation, persistent history with regression comparison
- Optimization module: chunk optimizer (size 128-2048, overlap 0-128, 4 strategies), prompt optimizer (variant scoring), retrieval optimizer (top_k/threshold/rerank/hybrid/MMR grid search), reranking optimizer (5 strategies)
- Evaluation suite: clinical test runner (per-question answer matching, citation scoring, difficulty/category breakdown), regression suite (8 configurable quality gates), report generator (4 report types + performance dashboard JSON), statistics (confusion matrix, precision/recall/F1, McNemar test, confidence intervals)
- 110 validation tests — all passing, zero regressions
- Total test suite: 1754 passing

### Documentation
- ARCHITECTURE.md — Clinical Validation Pipeline section (16)
- AI_WORKFLOW.md, CURRENT_STATUS.md, PROJECT_OVERVIEW.md, CHANGELOG.md, SESSION_NOTES.md
- VALIDATION_REPORT.md, BENCHMARK_SUMMARY.md, SYSTEM_READINESS.md

## [0.16.0] — 2026-07-16

### Added

#### Phase L — LangGraph Runtime Integration (`app/langgraph/`)

##### GraphBootstrap Module (`bootstrap.py`)
- `GraphBootstrap.register_graphs()` — registers `MedicalQAGraph` in global `GraphRegistry` at startup
- `GraphBootstrap.validate_dependencies()` — validates all 10 subsystems: AI provider, RAG engine, memory service, tool service, MedicalQAAgent, retriever service, context builder, embedding service, vector store, prompt manager
- `GraphBootstrap.run_full_bootstrap()` — combined registration + validation with diagnostics
- `GraphBootstrapResult` dataclass — tracks registration status, validation errors, subsystem diagnostics
- Module-level `get_bootstrap_result()` / `set_bootstrap_result()` for health check integration

##### Service Wiring (`graph_context.py`)
- Added fields: `agent_executor`, `rag_engine`, `context_builder`, `retriever_service`, `ai_provider`, `session_manager`
- `get_agent_executor()` — creates `AgentExecutor` wrapping `MedicalQAAgent`
- `populate_services()` — injects all available services into `GraphState.services`

##### ChatService Graph Integration (`app/chat/chat_service.py`)
- `ChatService` accepts optional `medical_qa_graph` parameter
- Dual execution path:
  - **Graph path** (default when available): routes through `MedicalQAGraph` → memory → agent → tool → retrieval → response → persist
  - **Direct path** (fallback): original RAG-only `RAGEngine.answer()` call
- `_ask_via_graph()` — creates `GraphState`, populates services, executes graph, converts result to `ChatResponse`
- All existing public methods unchanged with zero API contract modifications
- Lazy `TYPE_CHECKING` import to avoid circular dependency

##### Startup Integration (`app/main.py`)
- `GraphBootstrap.run_full_bootstrap()` called in FastAPI `lifespan`
- Bootstrap result stored via `set_bootstrap_result()` for health checks

##### Health Checks (`app/api/v1/ready.py`)
- 10 subsystem checks: database, migrations, graph_registry, tool_registry, memory_framework, ai_provider, embedding_provider, vector_store, retriever, prompt_manager
- Graph bootstrap status via `get_bootstrap_result()`

##### Chat API (`app/api/v1/chat.py`)
- `POST /api/v1/chat/message` now uses `GraphChatService` with `MedicalQAGraph`
- Returns `graph_executed` flag in response metadata

##### Checkpoint Abstraction
- `BaseCheckpointStore` ABC — `save()`, `load()`, `list_checkpoints()`, `delete()`, `health_check()`
- `InMemoryCheckpointStore` — current implementation
- Design supports future `RedisCheckpointStore` / `PostgresCheckpointStore`

##### 101 LangGraph Tests — all passing
- Graph state (11), config (3), exceptions (7), events (9), checkpoint (13), metrics (8), registry (7), executor (6), runtime (7), context (6), bootstrap (5), nodes (12), chat service graph integration (14)

##### Documentation Updates
- ARCHITECTURE.md — added LangGraph Runtime layer section
- AI_WORKFLOW.md — added LangGraph Runtime section with pipeline diagram, startup sequence, execution path
- CURRENT_STATUS.md — v0.16.0, Phase L complete, 283 LangGraph + integration tests, ~1322 total
- CHANGELOG.md — Phase L entry with all changes
- SESSION_NOTES.md — Phase L session
- LANGGRAPH_RUNTIME_AUDIT.md — Phase K0 audit
- RUNTIME_INTEGRATION_REPORT.md — Phase L integration report

### Architecture
```
FastAPI Lifespan
  └─ GraphBootstrap.run_full_bootstrap()
       ├─ register_graphs()   → GraphRegistry (medical_qa)
       └─ validate_dependencies() → 10 subsystems

POST /api/v1/chat/message
  └─ ChatService.ask()
       └─ MedicalQAGraph.execute()
            ├─ load_memory_node
            ├─ medical_qa_node (via AgentExecutor)
            ├─ tool_selector_node → tool_executor_node (conditional)
            ├─ retriever_node → context_builder_node (conditional)
            ├─ response_generator_node
            └─ persist_memory_node
```

### Changed
- `app/langgraph/graph_context.py` — added 6 new service fields and `populate_services()` method
- `app/langgraph/__init__.py` — exports `GraphBootstrap`, `GraphBootstrapResult`, `get_bootstrap_result`, `set_bootstrap_result`
- `app/chat/chat_service.py` — accepts `medical_qa_graph` parameter, dual execution path
- `app/main.py` — bootstraps LangGraph in lifespan
- `app/api/v1/chat.py` — uses graph-enabled ChatService
- `app/api/v1/ready.py` — 10 subsystem health checks

## [0.15.0] — 2026-07-15

[Phase J — Tool Calling Framework from previous version]

---

## [0.14.0] — 2026-07-15

[Phase I — Agent Framework from previous version]

---

[Previous versions 0.13.0 through 0.0.0 remain unchanged]

---

*The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).*
