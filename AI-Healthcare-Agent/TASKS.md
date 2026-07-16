# AI Healthcare Follow-up Assistant — Task Tracker

**Last Updated:** 2026-07-14
**Overall Progress:** 46% (7 of 14 phases complete)
**Current Version:** 0.7.0
**Target Version:** 1.0.0 (MVP)

---

## Phase Legend

| Icon | Status |
|------|--------|
| ✅ | Completed |
| 🔄 | In Progress |
| ⏳ | Pending |
| ❌ | Blocked |

---

## SPRINT 3A: Critical Production Fixes ✅ (COMPLETE — v0.3.0)

| ID | Task | Hours | Status |
|----|------|-------|--------|
| C1-001 | Create Alembic migration matching all 10 models | 1.0 | ✅ |
| C2-001 | Fix IDOR vulnerabilities with ownership checks | 1.5 | ✅ |
| C3-001 | Implement sliding-window rate limiting | 2.0 | ✅ |
| C4-001 | Implement CSRF protection | 1.0 | ✅ |
| C5-001 | Sync environment variables | 0.25 | ✅ |
| FIX-001 | Fix SQLAlchemy reserved name conflict (metadata) | 0.25 | ✅ |
| FIX-002 | Fix database session module (lazy init) | 0.5 | ✅ |
| FIX-003 | Fix SQLite compatibility | 0.5 | ✅ |
| FIX-004 | Fix auth header dependency (401 vs 422) | 0.25 | ✅ |
| FIX-005 | Fix AuthResponse schema | 0.25 | ✅ |
| FIX-006 | Pin bcrypt version | 0.1 | ✅ |
| TEST-001 | Write IDOR ownership tests | 1.0 | ✅ |
| TEST-002 | Write rate limit tests | 0.5 | ✅ |
| TEST-003 | Write CSRF tests | 0.5 | ✅ |
| TEST-004 | Write migration tests | 0.5 | ✅ |
| TEST-005 | Fix test infrastructure | 0.5 | ✅ |

---

## PHASE 1: Foundation ✅ (COMPLETE — v0.1.0)

| ID | Task | Hours | Status |
|----|------|-------|--------|
| PROJ-001 | Initialize Next.js + Tailwind + shadcn/ui | 2.0 | ✅ |
| PROJ-002 | Initialize FastAPI + SQLAlchemy + Alembic | 2.0 | ✅ |
| PROJ-003 | Create Docker Compose configuration | 1.0 | ✅ |
| PROJ-004 | Create complete folder structure (120+ stubs) | 1.0 | ✅ |
| PROJ-005 | Configure environment variables | 0.5 | ✅ |
| PROJ-006 | Set up code quality tools | 0.5 | ✅ |
| PROJ-007 | Create database models (9 tables) | 2.0 | ✅ |
| PROJ-008 | Create Pydantic schemas (10 modules) | 2.0 | ✅ |
| PROJ-009 | Implement core configuration module | 1.0 | ✅ |
| PROJ-010 | Create repository layer (base + 8 repos) | 2.0 | ✅ |
| PROJ-011 | Create service layer (10 services) | 3.0 | ✅ |
| PROJ-012 | Create API routes (6 routers) | 2.0 | ✅ |
| PROJ-013 | Create middleware layer | 0.5 | ✅ |
| PROJ-014 | Create agent skeletons (5 agents + orchestrator) | 3.0 | ✅ |
| PROJ-015 | Create RAG skeletons | 1.0 | ✅ |
| PROJ-016 | Create OCR skeletons | 0.5 | ✅ |
| PROJ-017 | Create prompt templates (legacy Python) | 1.0 | ✅ |
| PROJ-018 | Create background task skeletons | 0.5 | ✅ |
| PROJ-019 | Create test infrastructure | 1.0 | ✅ |
| PROJ-020 | Create frontend type system | 1.0 | ✅ |
| PROJ-021 | Create frontend API client | 1.0 | ✅ |
| PROJ-022 | Create frontend state management | 1.0 | ✅ |
| PROJ-023 | Create UI primitive components | 2.0 | ✅ |
| PROJ-024 | Create shared components | 1.0 | ✅ |
| PROJ-025 | Build auth pages (login + register) | 2.0 | ✅ |
| PROJ-026 | Build patient layout + dashboard | 2.0 | ✅ |
| PROJ-027 | Build patient pages (5 pages) | 2.0 | ✅ |
| PROJ-028 | Build doctor layout + pages | 2.0 | ✅ |
| PROJ-029 | Create middleware for auth guard | 0.5 | ✅ |
| PROJ-030 | Create CI/CD workflows | 1.0 | ✅ |
| PROJ-031 | Create setup scripts | 0.5 | ✅ |
| PROJ-032 | Write project documentation | 3.0 | ✅ |

---

## PHASE 2: Authentication ✅ (COMPLETE — v0.2.0)

| ID | Task | Hours | Status |
|----|------|-------|--------|
| AUTH-001 | Implement JWT token service | 2.0 | ✅ |
| AUTH-002 | Build patient registration endpoint | 1.0 | ✅ |
| AUTH-003 | Build doctor registration endpoint | 1.0 | ✅ |
| AUTH-004 | Build unified login endpoint | 1.0 | ✅ |
| AUTH-005 | Implement role-based access control | 1.0 | ✅ |
| AUTH-006 | Implement logout + token revocation | 1.0 | ✅ |
| AUTH-007 | Implement /me endpoint | 0.5 | ✅ |
| AUTH-008 | Add strong password validation | 0.5 | ✅ |
| AUTH-009 | Create RefreshToken DB model | 0.5 | ✅ |
| AUTH-010 | Write auth tests (18 tests) | 1.0 | ✅ |
| AUTH-011 | Build enhanced login page | 1.0 | ✅ |
| AUTH-012 | Build enhanced registration page | 1.5 | ✅ |
| AUTH-013 | Build API client with auto-refresh queue | 1.0 | ✅ |
| AUTH-014 | Update middleware for role-based redirects | 0.5 | ✅ |
| AUTH-015 | Update doctor/patient models with new fields | 0.5 | ✅ |

---

## SPRINT 3B: Production Data Layer ✅ (COMPLETE — v0.4.0)

| ID | Task | Hours | Status |
|----|------|-------|--------|
| DB-001 | Rewrite Alembic migration to match models | 1.0 | ✅ |
| DB-002 | Create seed data script (30+ records) | 1.0 | ✅ |
| DB-003 | Add database health checks | 0.5 | ✅ |
| DB-004 | Enhance backup manager | 0.5 | ✅ |
| DB-005 | Enhance database reset | 0.5 | ✅ |
| DB-006 | Add query optimization (N+1 prevention) | 1.0 | ✅ |
| DB-007 | Write integration tests (44 tests) | 2.0 | ✅ |

---

## SPRINT 3C: Prompt Library ✅ (COMPLETE — v0.5.0)

| ID | Task | Hours | Status |
|----|------|-------|--------|
| PRM-001 | Create 18 standalone prompt Markdown files | 3.0 | ✅ |
| PRM-002 | Create PROMPT_INDEX.md central registry | 0.5 | ✅ |
| PRM-003 | Implement PromptLoader class | 1.0 | ✅ |
| PRM-004 | Add YAML frontmatter to all prompts | 1.0 | ✅ |
| PRM-005 | Write PromptLoader tests | 0.5 | ✅ |
| PRM-006 | Deprecate old Python prompt files with migration notices | 0.5 | ✅ |
| PRM-007 | Update AI_WORKFLOW.md with PromptLoader references | 0.5 | ✅ |

---

## DESIGN PHASE: AI Architecture ✅ (COMPLETE — v0.6.0)

| ID | Task | Hours | Status |
|----|------|-------|--------|
| ARC-001 | AI Architecture design (18 sections) | 4.0 | ✅ |
| ARC-002 | Document Pipeline architecture design (20 sections) | 3.0 | ✅ |
| ARC-003 | Medical Safety system design (15 sections) | 3.0 | ✅ |
| ARC-004 | LangGraph workflow design (13 sections + diagrams) | 2.0 | ✅ |
| ARC-005 | Observability design (17 sections + diagrams) | 2.0 | ✅ |
| ARC-006 | Write 23 Architecture Decision Records (ADR-009 through ADR-031) | 3.0 | ✅ |

---

## SPRINT 3D: Observable Infrastructure ⏳ (PENDING — v0.8.0)

**Goal:** Production monitoring with logging, metrics, tracing, error tracking, and dashboards.
**Est. Hours:** 21 | **Tests:** 28 | **Dependencies:** None

### Logging & Tracing

| ID | Task | Hours | Status |
|----|------|-------|--------|
| OBS-001 | Configure structured JSON logging (prod) + colorized console (dev) | 1.0 | ⏳ |
| OBS-002 | Implement Request-ID middleware (UUID v4 per request) | 0.5 | ⏳ |
| OBS-003 | Add structured fields to all log entries (request_id, agent, duration) | 0.5 | ⏳ |
| OBS-004 | Implement PII masking filter for logs | 0.5 | ⏳ |
| OBS-005 | Set up OpenTelemetry SDK with OTLP exporter | 1.0 | ⏳ |
| OBS-006 | Instrument FastAPI middleware with OpenTelemetry spans | 1.0 | ⏳ |
| OBS-007 | Instrument LangGraph nodes with child spans | 1.0 | ⏳ |
| OBS-008 | Add trace context propagation to LangGraph state | 0.5 | ⏳ |

### Metrics

| ID | Task | Hours | Status |
|----|------|-------|--------|
| OBS-009 | Set up Prometheus `/metrics` endpoint | 1.0 | ⏳ |
| OBS-010 | Implement RED metrics (rate/errors/duration) for all endpoints | 1.0 | ⏳ |
| OBS-011 | Implement agent-level metrics (invocations, latency, errors) | 1.0 | ⏳ |
| OBS-012 | Implement LLM metrics (calls, tokens, cost, fallbacks) | 1.0 | ⏳ |
| OBS-013 | Implement business metrics (guardrail violations, escalations) | 0.5 | ⏳ |

### Error Tracking & LLM Observability

| ID | Task | Hours | Status |
|----|------|-------|--------|
| OBS-014 | Integrate Sentry SDK with PII sanitization hook | 1.0 | ⏳ |
| OBS-015 | Configure Sentry alert rules (Slack + PagerDuty) | 0.5 | ⏳ |
| OBS-016 | Set up LangSmith tracing for all LLM calls | 1.0 | ⏳ |
| OBS-017 | Implement LLM cost tracker (per-request + daily budget) | 1.0 | ⏳ |
| OBS-018 | Annotate LangSmith runs with prompt version + agent metadata | 0.5 | ⏳ |

### Health Endpoints & Dashboards

| ID | Task | Hours | Status |
|----|------|-------|--------|
| OBS-019 | Implement `/ready` readiness probe endpoint | 0.5 | ⏳ |
| OBS-020 | Enhance `/live` liveness probe endpoint | 0.25 | ⏳ |
| OBS-021 | Create 7 Grafana dashboards as JSON exports | 2.0 | ⏳ |
| OBS-022 | Add observability stack to Docker Compose (Prometheus + Grafana) | 1.0 | ⏳ |

### Testing

| ID | Task | Hours | Status |
|----|------|-------|--------|
| OBS-T1 | Unit tests: PII filter, cost calculator, health check logic | 1.0 | ⏳ |
| OBS-T2 | Integration tests: metrics endpoint, trace propagation | 1.0 | ⏳ |
| OBS-T3 | E2E tests: Sentry capture, LangSmith trace, Prometheus scrape | 1.0 | ⏳ |

---

## SPRINT 3E: Document Pipeline Implementation ⏳ (PENDING — v0.9.0)

**Goal:** End-to-end document upload pipeline: upload → validate → scan → store → OCR → chunk → queue.
**Est. Hours:** 28 | **Tests:** 38 | **Dependencies:** None

### Upload & Validation

| ID | Task | Hours | Status |
|----|------|-------|--------|
| PIP-001 | Implement `POST /api/v1/reports/upload` with multipart handling | 1.5 | ⏳ |
| PIP-002 | Add quarantine directory and move-to-permanent logic | 0.5 | ⏳ |
| PIP-003 | Implement concurrent upload limits (5/patient, 100MB/day) | 0.5 | ⏳ |
| PIP-004 | Implement 4-layer file validation (HTTP → extension → magic bytes → app) | 1.5 | ⏳ |
| PIP-005 | Add magic byte signature verification (PDF, JPEG, PNG) | 0.5 | ⏳ |
| PIP-006 | Add PDF/image integrity checks (`pypdf`, `PIL.Image.verify()`) | 0.5 | ⏳ |

### Virus Scan & Storage

| ID | Task | Hours | Status |
|----|------|-------|--------|
| PIP-007 | Implement ClamAV virus scan integration | 1.0 | ⏳ |
| PIP-008 | Create `security_scan_log` table and threat response logic | 0.5 | ⏳ |
| PIP-009 | Add scan-unavailable fail-open handling | 0.5 | ⏳ |
| PIP-010 | Create `FileStorage` abstract base class | 1.0 | ⏳ |
| PIP-011 | Implement `LocalFileStorage` backend | 0.5 | ⏳ |
| PIP-012 | Implement `S3FileStorage` backend | 1.0 | ⏳ |
| PIP-013 | Implement patient-scoped directory structure | 0.5 | ⏳ |

### OCR Integration

| ID | Task | Hours | Status |
|----|------|-------|--------|
| PIP-014 | Implement `GoogleVisionOCR` with `document_text_detection` | 1.5 | ⏳ |
| PIP-015 | Add per-page OCR result merging | 0.5 | ⏳ |
| PIP-016 | Implement PDF-to-image conversion for scanned PDFs | 1.0 | ⏳ |
| PIP-017 | Implement `TesseractOCR` fallback | 1.0 | ⏳ |
| PIP-018 | Implement `DirectPDFExtractor` for text-layer PDFs | 0.5 | ⏳ |
| PIP-019 | Add OCR method selection logic | 0.5 | ⏳ |

### Image Preprocessing

| ID | Task | Hours | Status |
|----|------|-------|--------|
| PIP-020 | Implement orientation correction (EXIF + OSD) | 0.5 | ⏳ |
| PIP-021 | Implement grayscale conversion + median denoise | 0.5 | ⏳ |
| PIP-022 | Implement CLAHE contrast enhancement | 0.5 | ⏳ |
| PIP-023 | Implement adaptive threshold binarization | 0.5 | ⏳ |
| PIP-024 | Implement deskew correction | 0.5 | ⏳ |
| PIP-025 | Implement DPI normalization | 0.5 | ⏳ |

### Chunking & Queue

| ID | Task | Hours | Status |
|----|------|-------|--------|
| PIP-026 | Implement `DocumentChunker` with header-based pre-splitting | 1.0 | ⏳ |
| PIP-027 | Add recursive character splitting with configurable parameters | 0.5 | ⏳ |
| PIP-028 | Implement `ChunkMetadata` schema | 0.5 | ⏳ |
| PIP-029 | Create `PipelineQueue` ABC with in-memory implementation | 1.0 | ⏳ |
| PIP-030 | Create Redis queue implementation | 1.0 | ⏳ |
| PIP-031 | Implement async background worker | 1.0 | ⏳ |
| PIP-032 | Add per-stage retry logic with exponential backoff | 1.0 | ⏳ |
| PIP-033 | Implement dead-letter queue for failed jobs | 0.5 | ⏳ |

### Testing

| ID | Task | Hours | Status |
|----|------|-------|--------|
| PIP-T1 | Unit tests: validators, preprocessor, chunker, queue | 2.0 | ⏳ |
| PIP-T2 | Integration tests: upload flow, OCR pipeline, queue lifecycle | 2.0 | ⏳ |
| PIP-T3 | E2E tests: full pipeline with sample PDF + image | 1.0 | ⏳ |

---

## SPRINT 4A: Medical Report Agent ⏳ (PENDING — v0.10.0)

**Goal:** AI extract structured medical data from OCR text — medicines, disease, follow-up.
**Est. Hours:** 21 | **Tests:** 40 | **Dependencies:** Sprint 3E

### LangGraph Nodes

| ID | Task | Hours | Status |
|----|------|-------|--------|
| MRA-001 | Implement `extract_entities` node (report_analysis prompt) | 1.5 | ⏳ |
| MRA-002 | Implement `extract_medicines` node (medicine_extraction prompt) | 1.5 | ⏳ |
| MRA-003 | Implement `validate_extraction` node (diagnosis_check prompt) | 1.0 | ⏳ |
| MRA-004 | Implement `check_consistency` node (rule-based cross-reference) | 0.5 | ⏳ |
| MRA-005 | Implement `store_results` node (DB transaction) | 1.0 | ⏳ |
| MRA-006 | Build Medical Report subgraph with conditional edges | 1.0 | ⏳ |

### LLM Integration

| ID | Task | Hours | Status |
|----|------|-------|--------|
| MRA-007 | Implement `LLMClient` with fallback chain (mini → 3.5 → rule) | 1.5 | ⏳ |
| MRA-008 | Implement `safe_llm_call` error handler | 0.5 | ⏳ |
| MRA-009 | Integrate PromptLoader for all 3 medical prompts | 0.5 | ⏳ |
| MRA-010 | Implement `@with_retry` decorator for LLM nodes | 0.5 | ⏳ |

### Validation & Normalization

| ID | Task | Hours | Status |
|----|------|-------|--------|
| MRA-011 | Implement `SchemaValidator` with JSON schema validation | 1.0 | ⏳ |
| MRA-012 | Implement `JSONRepair` (missing fields, type coercion, enum fix) | 0.5 | ⏳ |
| MRA-013 | Implement `MedicineNormalizer` (route/frequency alias expansion) | 1.0 | ⏳ |
| MRA-014 | Implement deduplication logic against existing active medicines | 0.5 | ⏳ |
| MRA-015 | Implement business validation rules (name in text, dosage unit) | 0.5 | ⏳ |

### Frontend

| ID | Task | Hours | Status |
|----|------|-------|--------|
| MRA-016 | Build drag-and-drop file upload component | 1.5 | ⏳ |
| MRA-017 | Build extraction results display with confidence indicator | 1.0 | ⏳ |
| MRA-018 | Build manual correction interface for extracted data | 1.0 | ⏳ |
| MRA-019 | Add upload progress bar and status polling | 0.5 | ⏳ |

### Testing

| ID | Task | Hours | Status |
|----|------|-------|--------|
| MRA-T1 | Unit tests: all LangGraph nodes, normalizer, validator | 1.5 | ⏳ |
| MRA-T2 | Integration tests: full extraction pipeline with mock LLM | 1.0 | ⏳ |
| MRA-T3 | E2E tests: upload → OCR → extract → display with sample prescriptions | 1.0 | ⏳ |
| MRA-T4 | Accuracy test: 10 sample prescriptions, measure extraction accuracy | 1.0 | ⏳ |

---

## SPRINT 4B: Patient Chat Agent + RAG ⏳ (PENDING — v0.11.0)

**Goal:** Patient chat with RAG, streaming, source citations, multi-turn conversation.
**Est. Hours:** 23 | **Tests:** 32 | **Dependencies:** Sprint 4A

### RAG Infrastructure

| ID | Task | Hours | Status |
|----|------|-------|--------|
| CHT-001 | Set up ChromaDB collection with HNSW cosine config | 1.0 | ⏳ |
| CHT-002 | Implement embedding service (`text-embedding-3-small`, batch 20) | 1.0 | ⏳ |
| CHT-003 | Implement vector ingestion pipeline (chunk → embed → store) | 1.5 | ⏳ |
| CHT-004 | Add metadata filtering by patient_id | 0.5 | ⏳ |
| CHT-005 | Implement multi-query generation for complex questions | 1.0 | ⏳ |
| CHT-006 | Implement retriever with deduplication | 1.0 | ⏳ |
| CHT-007 | Implement context compression (rag/context_compression prompt) | 0.5 | ⏳ |

### Chat LangGraph

| ID | Task | Hours | Status |
|----|------|-------|--------|
| CHT-008 | Implement `retrieve_context` node (vector search + metadata filter) | 1.0 | ⏳ |
| CHT-009 | Implement `compress_context` node | 0.5 | ⏳ |
| CHT-010 | Implement `generate_response` node (patient_chat prompt) | 1.0 | ⏳ |
| CHT-011 | Implement `check_guardrails` node (guardrails prompt) | 0.5 | ⏳ |
| CHT-012 | Implement `format_output` node (output_formatter + citation_format) | 0.5 | ⏳ |
| CHT-013 | Implement `should_escalate` router node | 0.5 | ⏳ |
| CHT-014 | Build Chat Agent subgraph with conditional edges | 1.0 | ⏳ |

### Streaming & Context

| ID | Task | Hours | Status |
|----|------|-------|--------|
| CHT-015 | Implement SSE streaming endpoint (`POST /chat/stream`) | 1.0 | ⏳ |
| CHT-016 | Add client disconnect handling (CancelledError) | 0.5 | ⏳ |
| CHT-017 | Implement conversation window (last 20 verbatim, older summarized) | 1.0 | ⏳ |
| CHT-018 | Build context loader (patient data, chat history, medicines) | 0.5 | ⏳ |

### Frontend

| ID | Task | Hours | Status |
|----|------|-------|--------|
| CHT-019 | Build chat message list component | 1.0 | ⏳ |
| CHT-020 | Build streaming message display with typing indicator | 0.5 | ⏳ |
| CHT-021 | Build source citation popover component | 0.5 | ⏳ |
| CHT-022 | Build chat input with send button + loading state | 0.5 | ⏳ |

### Testing

| ID | Task | Hours | Status |
|----|------|-------|--------|
| CHT-T1 | Unit tests: retriever, compressor, guardrails, context window | 1.5 | ⏳ |
| CHT-T2 | Integration tests: chat with mock ChromaDB, streaming, multi-turn | 1.5 | ⏳ |
| CHT-T3 | E2E tests: upload → ingest → chat → verify sources | 1.0 | ⏳ |

---

## SPRINT 4C: Emergency Detection + Medicine Reminder ⏳ (PENDING — v0.12.0)

**Goal:** Symptom triage with escalation + automated reminders with adherence tracking.
**Est. Hours:** 23 | **Tests:** 35 | **Dependencies:** Sprint 4A

### Emergency LangGraph

| ID | Task | Hours | Status |
|----|------|-------|--------|
| EMG-001 | Implement `analyze_symptoms` node (symptom_triage prompt) | 1.0 | ⏳ |
| EMG-002 | Implement `assess_risk` node (risk_assessment prompt) | 1.0 | ⏳ |
| EMG-003 | Implement `decide_escalation` router node | 0.5 | ⏳ |
| EMG-004 | Implement `generate_alert` node (escalation prompt) | 1.0 | ⏳ |
| EMG-005 | Implement `store_alert` node (DB write) | 0.5 | ⏳ |
| EMG-006 | Build Emergency Agent subgraph | 0.5 | ⏳ |

### Risk Classification & Escalation

| ID | Task | Hours | Status |
|----|------|-------|--------|
| EMG-007 | Implement keyword-based risk classifier (HIGH/MEDIUM/LOW) | 1.0 | ⏳ |
| EMG-008 | Implement overall risk matrix (emergency + extraction + alert frequency) | 0.5 | ⏳ |
| EMG-009 | Implement escalation engine with acknowledgment timeouts | 1.0 | ⏳ |
| EMG-010 | Implement doctor notification channels (in-app + email) | 1.0 | ⏳ |
| EMG-011 | Add escalation guarantee logic (60s doctor notification for HIGH) | 0.5 | ⏳ |

### Emergency Frontend

| ID | Task | Hours | Status |
|----|------|-------|--------|
| EMG-012 | Build symptom check form with free-text input | 0.5 | ⏳ |
| EMG-013 | Build risk level display component (color-coded) | 0.5 | ⏳ |
| EMG-014 | Add disclaimer injection (D2/D3/D4 by risk level) | 0.5 | ⏳ |

### Reminder Backend

| ID | Task | Hours | Status |
|----|------|-------|--------|
| REM-001 | Implement rule-based dose schedule generator | 1.0 | ⏳ |
| REM-002 | Implement `POST /adherence/log` endpoint | 0.5 | ⏳ |
| REM-003 | Implement `check_schedule` DB query node | 0.5 | ⏳ |
| REM-004 | Implement `detect_missed_doses` comparison node | 1.0 | ⏳ |
| REM-005 | Implement `generate_reminders` transform node | 0.5 | ⏳ |
| REM-006 | Implement `update_adherence_stats` node | 0.5 | ⏳ |
| REM-007 | Build Reminder Agent subgraph | 0.5 | ⏳ |

### Reminder Frontend

| ID | Task | Hours | Status |
|----|------|-------|--------|
| REM-008 | Build daily medicine schedule view | 1.0 | ⏳ |
| REM-009 | Build adherence rate chart (7-day + 30-day) | 1.0 | ⏳ |
| REM-010 | Add taken/missed dose indicators | 0.5 | ⏳ |

### Doctor Alert UI

| ID | Task | Hours | Status |
|----|------|-------|--------|
| EMG-015 | Build doctor alert list with risk color coding | 1.0 | ⏳ |
| EMG-016 | Add alert acknowledgment workflow | 0.5 | ⏳ |
| EMG-017 | Add escalation timeout display | 0.5 | ⏳ |

### Testing

| ID | Task | Hours | Status |
|----|------|-------|--------|
| EMG-T1 | Unit tests: risk classifier, escalation engine, schedule generator | 2.0 | ⏳ |
| EMG-T2 | Integration tests: emergency flow, reminder lifecycle | 1.0 | ⏳ |
| EMG-T3 | E2E tests: symptom check → triage → escalate; schedule → remind | 1.0 | ⏳ |

---

## SPRINT 4D: Doctor Dashboard + Summary Agent ⏳ (PENDING — v0.13.0)

**Goal:** Doctor dashboard with AI summaries, adherence overview, patient detail, report review.
**Est. Hours:** 22 | **Tests:** 27 | **Dependencies:** Sprint 4A, 4B, 4C

### Summary LangGraph

| ID | Task | Hours | Status |
|----|------|-------|--------|
| SUM-001 | Implement `aggregate_data` node (pull from 5 sources) | 1.5 | ⏳ |
| SUM-002 | Implement `compress_chat_history` node | 0.5 | ⏳ |
| SUM-003 | Implement `generate_summary` node (doctor_summary prompt) | 1.0 | ⏳ |
| SUM-004 | Implement `format_summary` node (compute adherence_metrics + risk_flags) | 1.0 | ⏳ |
| SUM-005 | Build Summary Agent subgraph | 0.5 | ⏳ |

### Dashboard APIs

| ID | Task | Hours | Status |
|----|------|-------|--------|
| SUM-006 | Implement patient list with search + filter API | 1.0 | ⏳ |
| SUM-007 | Implement patient detail aggregation API | 1.0 | ⏳ |
| SUM-008 | Implement dashboard statistics API | 0.5 | ⏳ |

### Dashboard Frontend

| ID | Task | Hours | Status |
|----|------|-------|--------|
| SUM-009 | Build patient list component with search | 1.0 | ⏳ |
| SUM-010 | Build patient detail view (medicines, reports, alerts, chat) | 1.5 | ⏳ |
| SUM-011 | Build AI summary display with expandable sections | 1.0 | ⏳ |
| SUM-012 | Build adherence overview section with charts | 1.5 | ⏳ |
| SUM-013 | Build report review panel (OCR text + extracted medicines side-by-side) | 1.0 | ⏳ |
| SUM-014 | Build dashboard statistics cards | 0.5 | ⏳ |

### Testing

| ID | Task | Hours | Status |
|----|------|-------|--------|
| SUM-T1 | Unit tests: summary nodes, data aggregation | 1.5 | ⏳ |
| SUM-T2 | Integration tests: summary with mock data, patient list filters | 1.5 | ⏳ |
| SUM-T3 | E2E tests: doctor logs in → views list → detail → summary | 1.0 | ⏳ |

---

## SPRINT 4E: Deployment + Final Testing ⏳ (PENDING — v1.0.0)

**Goal:** Production deployment, security audit, load test, documentation finalization.
**Est. Hours:** 20 | **Tests:** 12 | **Dependencies:** All prior sprints

### Infrastructure

| ID | Task | Hours | Status |
|----|------|-------|--------|
| DEP-001 | Optimize Docker images (multi-stage, slim builds) | 1.0 | ⏳ |
| DEP-002 | Create production Docker Compose configuration | 0.5 | ⏳ |
| DEP-003 | Add ClamAV + ChromaDB + Redis to Docker Compose | 0.5 | ⏳ |

### Deployment

| ID | Task | Hours | Status |
|----|------|-------|--------|
| DEP-004 | Deploy frontend to Vercel with environment variables | 1.0 | ⏳ |
| DEP-005 | Configure custom domain + SSL on Vercel | 0.5 | ⏳ |
| DEP-006 | Deploy backend to Render (web service) | 1.0 | ⏳ |
| DEP-007 | Set up Neon PostgreSQL (connection pooling, backups) | 0.5 | ⏳ |
| DEP-008 | Configure ChromaDB cloud or self-hosted | 0.5 | ⏳ |
| DEP-009 | Set up environment variables in production | 0.5 | ⏳ |

### CI/CD

| ID | Task | Hours | Status |
|----|------|-------|--------|
| DEP-010 | Finalize GitHub Actions CI/CD (test + deploy) | 1.0 | ⏳ |
| DEP-011 | Add deployment automation scripts | 0.5 | ⏳ |

### Security

| ID | Task | Hours | Status |
|----|------|-------|--------|
| DEP-012 | Run dependency security audit (pip-audit, npm audit) | 0.5 | ⏳ |
| DEP-013 | Run OWASP dependency check | 1.0 | ⏳ |
| DEP-014 | Verify HIPAA compliance checklist | 0.5 | ⏳ |
| DEP-015 | Verify all secrets are in environment variables | 0.5 | ⏳ |

### Final Testing

| ID | Task | Hours | Status |
|----|------|-------|--------|
| DEP-016 | Full E2E test suite (10 user journeys) | 2.0 | ⏳ |
| DEP-017 | Load test with 100 concurrent users (k6 or Locust) | 2.0 | ⏳ |
| DEP-018 | Full regression test suite | 1.0 | ⏳ |
| DEP-019 | Fix critical bugs found in final testing | Buffer | ⏳ |

### Documentation

| ID | Task | Hours | Status |
|----|------|-------|--------|
| DEP-020 | Write deployment guide (DEPLOYMENT.md) | 1.0 | ⏳ |
| DEP-021 | Finalize API documentation (all endpoints) | 0.5 | ⏳ |
| DEP-022 | Finalize CHANGELOG.md for v1.0.0 | 0.25 | ⏳ |
| DEP-023 | Update README.md with deployment status | 0.25 | ⏳ |

---

## FUTURE / BACKLOG (v1.1+)

| ID | Feature | Est. Hours | Priority |
|----|---------|-----------|----------|
| FTR-001 | Email notifications (SendGrid) | 3.0 | Medium |
| FTR-002 | SMS notifications (Twilio) | 2.0 | Medium |
| FTR-003 | Push notifications (Web Push API) | 2.0 | Low |
| FTR-004 | Password reset flow | 2.0 | High |
| FTR-005 | Rate limiting with Redis | 1.0 | Medium |
| FTR-006 | Error boundary components (frontend) | 2.0 | Medium |
| FTR-007 | Loading skeletons for all pages | 1.0 | Low |
| FTR-008 | Database index optimization | 1.0 | Medium |
| FTR-009 | Refresh token cleanup job | 0.5 | Medium |
| FTR-010 | Pagination for reports, chat, appointments | 2.0 | Medium |
| FTR-011 | Remove old Python prompt files | 0.5 | Low |
| FTR-012 | Admin dashboard | 6.0 | Low |
| FTR-013 | Multi-language support (i18n) | 4.0 | Low |
| FTR-014 | WhatsApp chatbot | 4.0 | Low |
| FTR-015 | EHR integration (FHIR) | 12.0 | Low |
| FTR-016 | Mobile apps (React Native) | 20.0 | Low |
| FTR-017 | Video consultation (WebRTC) | 8.0 | Low |
| FTR-018 | Offline mode (Service Worker) | 4.0 | Low |
| FTR-019 | Wearable device integration | 8.0 | Low |
| FTR-020 | Predictive readmission analytics | 6.0 | Low |

---

## SUMMARY STATISTICS

| Metric | Value |
|--------|-------|
| Total Tasks | 195 |
| Completed (v0.1 – v0.7) | 90 |
| In Progress | 0 |
| Pending (Sprints 3D–4E) | 105 |
| Future / Backlog | 20 |
| Completion Rate | 46% |
| Completed Versions | 0.1.0 – 0.7.0 (7 versions) |
| Target | 1.0.0 (MVP) |
| Phases to v1.0 | 7 sprints (~7 weeks) |
| Est. Remaining Hours | 158 |

### Version History

```
v0.1.0 — Foundation (Phase 1)                           ✅ Jul 03
v0.2.0 — Authentication (Phase 2)                       ✅ Jul 11
v0.3.0 — Production Hardening (Sprint 3A)                ✅ Jul 11
v0.4.0 — Production Data Layer (Sprint 3B)               ✅ Jul 14
v0.5.0 — Prompt Library (Sprint 3C)                      ✅ Jul 14
v0.6.0 — AI Architecture Design                           ✅ Jul 14
v0.7.0 — Document Pipeline + Medical Safety Design        ✅ Jul 14
──────────────────────────────────────────────────────────────────
v0.8.0 — Observable Infrastructure (Sprint 3D)            ⏳ Jul 21
v0.9.0 — Document Pipeline Impl (Sprint 3E)               ⏳ Jul 28
v0.10.0 — Medical Report Agent (Sprint 4A)                ⏳ Aug 04
v0.11.0 — Patient Chat Agent + RAG (Sprint 4B)            ⏳ Aug 11
v0.12.0 — Emergency + Reminder Agents (Sprint 4C)         ⏳ Aug 18
v0.13.0 — Doctor Dashboard + Summary (Sprint 4D)          ⏳ Aug 25
v1.0.0  — Deployment + Ship (Sprint 4E)                   ⏳ Sep 01
```

*Last updated: 2026-07-14*
