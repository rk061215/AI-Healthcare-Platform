# Changelog

> Semantic versioning following [Keep a Changelog](https://keepachangelog.com/).
> Never overwrite previous versions.

---

## [1.0.0] — 2026-07-19

### Added

#### Phase U.9 — Render CLI Integration & Developer Workflow

- `Makefile` — cross-platform developer targets: `deploy`, `logs`, `verify`, `env-check`, `health`, `ready`, `live`, `status`, `restart`, `redeploy`, `dashboard`
- `scripts/render.ps1` — PowerShell equivalent for Windows developers
- `RENDER_CLI_GUIDE.md` — Full documentation covering installation (Win/Linux/macOS), authentication, project configuration, deployment workflow, health verification, environment validation, logging & troubleshooting, CI/CD integration, rollback, and FAQ
- `project_memory/RENDER_CLI_INTEGRATION_REPORT.md` — Audit report confirming zero vendor lock-in

### Changed
- Render CLI is strictly optional — application has zero runtime dependency on Render
- Blueprint deployment (`render.yaml`) remains the sole deployment mechanism — unchanged

## [1.0.0] — 2026-07-18

### Added

#### Phase U — Free Tier Compatibility & Startup Vector Recovery

##### U.7 — Free Tier Render Compatibility
- Removed `disk:` block from `render.yaml` (Free tier doesn't support persistent disks)
- Removed orphaned env vars: `UPLOAD_DIR`, `DOCUMENT_STORAGE_DIR`, `CHROMA_PERSIST_DIR`
- All three directories use code defaults (`./uploads`, `./documents`, `./chromadb_data`) resolving to WORKDIR `/app/`
- Known gap documented: `RecoveryManager` does not compare actual `document_count` vs `indexed_reports`

##### U.8 — Automatic Startup Vector Recovery
- Added `actual_document_count` field to `VectorHealth` dataclass (`app/vector_recovery/health.py`)
- Modified `check_health()` to extract `document_count` from store health, compare against `indexed_reports`, set status to "degraded" when `indexed > actual_document_count` and `total > 0`
- Added `rebuild_in_progress` check — status set to "rebuilding" when `in_progress` is `True`
- Added `_mark_all_indexed_as_stale()` method to `RecoveryManager` — resets INDEXED→STALE via single UPDATE query with rollback on error
- Modified `run_startup_recovery()` — detects `indexed_reports > actual_document_count`, calls `_mark_all_indexed_as_stale()` before `rebuild_all()`
- Updated `/ready` endpoint to handle "rebuilding" status
- Updated monitoring endpoint to include `actual_document_count` in response details
- 44 tests passing for vector recovery (all existing + 7 new U.8 tests)

### Changed
- `recovery_manager.py::rebuild_all()` — `finally` block now preserves `total`/`completed`/`failed` counts in progress state

### Fixed
- Ephemeral storage gap: redeploy with existing PostgreSQL data no longer silently reports "healthy" with empty ChromaDB — system now detects mismatch and auto-rebuilds
- Removed invalid `sqlalchemy-asyncpg==0.0.1a1` dependency — SQLAlchemy 2.0+ has native async support via `sqlalchemy.ext.asyncio`; only `SQLAlchemy` + `asyncpg` are required

## [0.17.0] — 2026-07-16

### Added

#### Phase M — Clinical Validation, Dataset Management & AI Optimization (`app/validation/`)

##### Dataset Management (`app/validation/dataset/`)
- `ground_truth.py` — `GroundTruth`, `GroundTruthEntry`, `GroundTruthSet` with 10 document types, 4 difficulty levels, 10 question categories, and full stats
- `dataset_loader.py` — `DatasetLoader` — JSON/JSONL load/save, directory batch loading
- `dataset_manager.py` — `DatasetManager` — CRUD operations, import/export, caching
- `dataset_validator.py` — `DatasetValidator`, `ValidationResult` — structural integrity checks
- `dataset_splitter.py` — `DatasetSplitter` — entry-level and document-level train/val/test splits
- `fixtures/sample_golden_qa.json` — sample benchmark dataset (CBC, Lipid, Prescription)

##### Benchmark System (`app/validation/benchmark/`)
- `benchmark_config.py` — `BenchmarkConfig` — configurable top_k, k_values, warmup/benchmark runs
- `benchmark_metrics.py` — `BenchmarkMetrics` — 12 metrics: retrieval_recall, precision@K, MRR, NDCG, citation P/R/F1, groundedness, hallucination_rate, answer_relevance, plus statistical utilities
- `benchmark_runner.py` — `BenchmarkRunner` — warmup + multi-run with latency/memory/token tracking
- `benchmark_suite.py` — `BenchmarkSuite`, `BenchmarkResult` — result aggregation
- `benchmark_history.py` — `BenchmarkHistory` — persistent storage, comparison, regression detection

##### Optimization Module (`app/validation/optimization/`)
- `chunk_optimizer.py` — `ChunkOptimizer` — grid search over chunk_size, chunk_overlap, 4 strategies
- `prompt_optimizer.py` — `PromptOptimizer` — variant registration with weighted scoring
- `retrieval_optimizer.py` — `RetrievalOptimizer` — grid search over top_k, threshold, rerank, hybrid, MMR
- `reranking_optimizer.py` — `RerankingOptimizer` — 5 reranking strategies with configurable penalties

##### Evaluation Suite (`app/validation/evaluation/`)
- `clinical_test_runner.py` — `ClinicalTestRunner` — per-question answer matching, citation scoring, difficulty/category breakdown
- `regression_suite.py` — `RegressionSuite` — automated quality gates (latency, recall, hallucination, citations, groundedness, relevance, tokens)
- `report_generator.py` — `ReportGenerator` — 4 report types + performance dashboard JSON
- `statistics.py` — `Statistics` — confusion matrix, accuracy, precision/recall/F1, McNemar test, confidence intervals

##### 110 Validation Tests — All Passing
- Dataset loader (7), manager (10), splitter (6), validator (9), ground truth (14)
- Benchmark metrics (12), runner (7), suite (6), history (7)
- Clinical test runner (8), optimizers (13)

##### Documentation
- ARCHITECTURE.md — added Clinical Validation Pipeline section (16)
- AI_WORKFLOW.md — added Clinical Validation Pipeline status and details
- CURRENT_STATUS.md — v0.17.0, Phase M, 1754 total tests
- PROJECT_OVERVIEW.md — v0.17.0
- CHANGELOG.md — Phase M entry
- SESSION_NOTES.md — Phase M session
- VALIDATION_REPORT.md — generated validation report
- BENCHMARK_SUMMARY.md — generated benchmark summary
- SYSTEM_READINESS.md — system readiness assessment

## [0.15.0] — 2026-07-15

### Added

#### Phase J — Tool Calling Framework (`app/tools/`)
- `BaseTool` ABC — 6 lifecycle methods: validate, authorize, execute, verify, audit, cleanup
- `ToolRegistry` + global singleton, `ToolFactory.create()`, `ToolExecutor` (validate→authorize→execute→verify→audit→cleanup with retry)
- `ToolSelector` — rule-based intent→tool mapping (15+ patterns, replaceable by AI)
- `ToolService.run()` / `run_with_tool()` / `run_from_query()` / `list_tools()`
- 5 domain tools: AppointmentTool, PatientTool, DoctorTool, ReportTool, MedicationTool (wrap existing services)
- 4 future skeletons: NotificationTool, CalendarTool, EmailTool, SMSTool
- 13 exception classes, auto-registration of all 9 tools at import
- 116 tests — all pass

## [0.14.0] — 2026-07-15

### Added

#### Phase I — Agent Framework (`app/agents/`)
- `BaseAgent` ABC — 10 lifecycle methods
- `AgentContext`, `AgentState` (12 phases, component traces), `AgentResponse` (ok/error factories)
- `AgentRegistry` + global singleton, `AgentFactory.create()`, `AgentExecutor` (retry, timing), `AgentService` (run API)
- `MedicalQAAgent` — inherits BaseAgent, wraps ChatService, zero regressions
- 5 future skeleton agents: Reminder, Emergency, DoctorSummary, FollowUp, Appointment
- 14 exception classes, registration auto-import
- 76 tests — all pass

### Fixed
- Executor now propagates `response.success=False` from invoke_rag to final AgentResponse

## [0.13.0] — 2026-07-15

### Added

#### Phase H — Memory Framework (`app/memory/`)
- `BaseMemoryStore` ABC + `InMemoryStore` (dict-based with search filtering)
- `MemoryService` — remembers/recalls/forgets/clears/prunes/extracts/summarizes
- 5 memory types: Conversation, DocumentContext, PatientContext, Preference, Tool
- 4 processors: Extractor, Retriever, Summarizer, Pruner
- 3 policies: Retention, Privacy (strict mode sanitization), Expiry (per-type TTL)
- `MemoryConfig`, 15 exceptions, 8 Pydantic models, registry + factory
- Redis/Postgres store skeletons
- 133 tests — all pass

## [0.12.0] — 2026-07-15

### Added

#### Phase G — AI Evaluation & Benchmarking (`app/evaluation/`)
- `EvaluationConfig`— provider, model, top_k, k_values, per-metric enable flags, dataset/report paths, num_runs, warmup_runs, timeout
- 12 exception classes — `EvaluationError`, `ConfigurationError`, `MetricError`, `UnsupportedMetricError`, `DatasetError`, `DatasetNotFoundError`, `GroundTruthError`, `BenchmarkError`, `BenchmarkTimeoutError`, `LatencyError`, `ReportError`, `TokenUsageError`
- `Metric` ABC + `MetricResult` + `MetricRegistry` + `BenchmarkResults` — pluggable architecture
- `BenchmarkRunner` — full benchmark lifecycle: load dataset → execute (with warmup, multi-run) → aggregate → generate report
- `ReportGenerator` — JSON report output + text summary
- Retrieval metrics: `recall_at_k`, `precision_at_k`, `reciprocal_rank`, `mean_reciprocal_rank` (MRR), `dcg_at_k`, `ndcg_at_k`; Metric classes: `RecallAtK`, `PrecisionAtK`, `MRR`, `NDCG`
- RAG metrics: `groundedness`, `citation_accuracy`, `context_precision`, `context_recall`, `answer_relevance`; Medical QA: `medication_extraction_accuracy`, `diagnosis_accuracy`, `lab_result_accuracy`, `follow_up_extraction_accuracy`
- Hallucination detection: `detect_hallucinated_claims`, `hallucination_rate`, pattern matching (15 hallucination patterns, 6 support phrases, 7 unsupported claim patterns)
- Citation metrics: `citation_precision`, `citation_recall`, `citation_f1`, `citation_coverage`, `citation_redundancy`
- Performance: `LatencyTracker` (context manager, p95/p99), `PerformanceAnalyzer` (throughput), `TokenUsageTracker` (prompt/completion tracking)
- `DatasetLoader` — JSON/JSONL from `datasets/` (6 categories), `BenchmarkSample` with full ground truth
- `GroundTruthSet` / `GroundTruthValidator` — ground truth management and validation
- 6 dataset directories: `datasets/prescriptions/`, `lab_reports/`, `blood_tests/`, `radiology/`, `discharge/`, `insurance/`
- 190 tests — all pass
- Sample evaluation report generated at `evaluation_reports/sample_evaluation_*.json`

### Fixed
- Circular import between `benchmark_runner.py` and `report_generator.py` — extracted `BenchmarkResults` into `models.py`
- `PerformanceReport`/`TokenUsageReport` now wrapped in `Metric` classes before aggregation

### Changed
- Bumped version to 0.12.0
- Total test count: 714 (was 598)

### Documentation
- ARCHITECTURE.md — updated AI pipeline with Evaluation & Benchmarking layer
- AI_WORKFLOW.md — added full Evaluation Framework section with metric reference table
- CURRENT_STATUS.md — v0.12.0, Phase G complete, 714 test total, updated pending modules
- CHANGELOG.md (root) — v0.12.0 entry
- SESSION_NOTES.md — Phase G session notes
- AI_ARCHITECTURE_STATUS.md — Evaluation Framework status: 🔴→✅, updated component inventory, readiness scores

---

## [0.11.0] — 2026-07-15

### Added

#### Phase F — Medical Document QA Agent (`app/chat/`)
- `ChatConfig` dataclass — session_timeout_minutes, max_questions_per_session, max_suggested_questions, confidence thresholds, enable flags
- 6 exception classes — `ChatError`, `SessionNotFoundError`, `SessionExpiredError`, `EmptyQuestionError`, `MaxQuestionsExceededError`, `NoDocumentInSessionError`, `QuestionGenerationError`
- 7 Pydantic models + 2 enums — `ChatRequest`, `ChatResponse`, `ChatSession`, `QAPair`, `ConfidenceScore`, `SuggestedQuestion`, `DocumentSummary`, `QuestionType`, `ConfidenceLevel`
- `SessionManager` — in-memory session store with TTL expiry, document section tracking, Q&A history, follow-up detection
- `ConfidenceCalculator` — retrieval-based scoring: average retrieval score, chunk count, citation coverage ratio, guardrail validation, insufficient-evidence phrase detection
- `QuestionSuggester` — rule-based: 16 templates across 6 categories, priority-ordered, deduplication against recent questions
- `ResponseFormatter` — confidence prefix, unknown-answer template, citation dedup by chunk_id, report summary
- `ChatService` — main orchestrator: validate → RAG Engine → confidence → suggestions → format
- Full `__init__.py` — public exports for all classes and exceptions
- 62 tests — all pass (unit + integration + multi-turn + edge cases)

### Fixed
- `ConfidenceScore.insufficient_evidence` default changed from `True` to `False`
- `QuestionSuggester` section detection — bool flags no longer incorrectly matched as `is not None`
- `ResponseFormatter._format_citations()` — handles both `dict` and `CitationEntry` objects via `_get_attr()`

### Changed
- Bumped version to 0.11.0
- All documentation updated to reflect Phase F completion
- Total test count: 598 (was 536)

### Documentation
- ARCHITECTURE.md — updated AI pipeline with Medical QA Agent
- AI_WORKFLOW.md — added full Medical QA Agent section with query flow, code examples, file table, test summary
- CURRENT_STATUS.md — v0.11.0, Phase F complete, 598 test total, updated pending modules
- CHANGELOG.md (root) — v0.11.0 entry
- SESSION_NOTES.md — Phase F session notes
- AI_ARCHITECTURE_STATUS.md — Medical QA Agent status: 🔴→✅, updated pipeline diagrams, component inventory, readiness scores

---

## [0.10.0] — 2026-07-15

### Added

#### Phase E — RAG Engine (`app/rag/`)
- `RAGEngineConfig` dataclass — provider, model, temperature, top_k, min_score, guardrails/citations/rewriting enable flags
- 11 exception classes — `RAGError`, `ConfigurationError`, `QueryError`, `EmptyQueryError`, `QueryClassificationError`, `UnsupportedQueryError`, `RetrievalError`, `ContextBuildError`, `InsufficientContextError`, `ResponseGenerationError`, `GuardrailError`, `UnsafeContentError`, `CitationError`
- 10 Pydantic models — `RAGRequest`, `RAGResponse`, `RAGContext`, `ProcessedQuery`, `QueryClassification`, `RewrittenQuery`, `CitationEntry`, `CitationBlock`, `GuardrailResult`, `RAGMetrics`
- `QueryProcessor` — normalization, cleaning, medical term detection, entity extraction
- `QueryClassifier` — 7 categories via regex, confidence scoring, section/top_k suggestions
- `BaseQueryRewriter` ABC + `DefaultQueryRewriter` — abbreviation expansion (22 abbreviations), synonym insertion (7 terms)
- `RetrievalOrchestrator` — wires `RetrieverService` + `ContextBuilder` together
- `ResponseGenerator` — uses `BaseProvider` via `AIProviderFactory`, `RESPONSE_SYSTEM_PROMPT`, supports `generate_text()` and `generate_structured_output()`
- `CitationManager` — extract unique citations, format inline markers, detect hallucinated citations, validate response grounding
- `Guardrails` — pre-generation (insufficient context, query safety) and post-generation (unsupported claims, medical uncertainty, citation hallucination, context grounding) checks
- `RAGEngine` — full pipeline: `answer()` method orchestrating process → classify → rewrite → orchestrate → pre-guardrails → generate → post-guardrails → citations → safety disclaimer
- 74 tests — all pass

### Changed
- Bumped version to 0.10.0
- Fixed `ResponseGenerator` provider creation — `AIProviderFactory.create()` now passes `config` keyword argument
- Fixed `RAGEngine.answer()` — removed stray `from None` syntax error

### Documentation
- ARCHITECTURE.md — updated AI pipeline with RAG Engine
- AI_WORKFLOW.md — added full RAG Engine section with query flow, code examples, file table, test summary
- CURRENT_STATUS.md — v0.10.0, Phase E complete, 536 test total, updated pending modules
- CHANGELOG.md (root) — v0.10.0 entry
- SESSION_NOTES.md — Phase E session notes
- PROJECT_OVERVIEW.md — updated architecture description
- AI_ARCHITECTURE_STATUS.md — RAG Engine status: 🔴 → ✅, updated pipeline diagrams, component inventory
- DECISIONS.md — added RAG Engine architecture decisions

---

## [0.9.0] — 2026-07-15

### Added

#### Phase C — Vector Store Layer (`app/vector_store/`)
- `BaseVectorStore` ABC — create_collection, add_documents, search, delete, list, health_check, close
- `VectorStoreRegistry` — provider registration with JSON save/restore persistence
- `VectorStoreFactory.create(config)` — configuration-driven instantiation
- `VectorService` — high-level API with error handling, collection/document lifecycle management
- `ChromaDBStore` — full ChromaDB implementation (active provider)
- `QdrantStore`, `WeaviateStore`, `PineconeStore` — future provider skeletons
- `VectorStoreConfig`, `SearchResult` model, 8 exception classes
- 94 tests covering registry, factory, service, ChromaDB, mock, future providers, edge cases

#### Phase D — Retrieval Layer (`app/retrieval/`)
- `BaseRetriever` ABC — retrieve, retrieve_by_patient, retrieve_by_report, retrieve_with_scores, health_check, close
- `RetrieverRegistry` — provider registration with persistence
- `RetrieverFactory.create(config)` — configuration-driven instantiation
- `RetrieverService` — search/search_by_patient/search_by_report/search_by_document_type/health_check
- `VectorRetriever` — wraps VectorService, translates SearchResult → RetrievalResult
- `HybridRetriever`, `KeywordRetriever` — future provider skeletons
- `RetrieverConfig`, `RetrievalQuery`, `RetrievalResult`, `RetrievedDocument`, `RetrievalMetrics`
- 8 exception classes
- 57 tests

#### Phase D — Context Builder (`app/context/`)
- `ContextBuilder` — orchestrates 6-stage pipeline: dedup → rank → compress → budget → citations → assemble
- `Deduplicator` — exact text match, chunk ID match, overlap detection
- `Ranker` — priority sections + score descending
- `Compressor` — adjacent/overlap merging from same report/section
- `CitationGenerator` — citation block + fragment source annotation
- `TokenBudgetManager` — 3 strategies: fixed_max, priority_truncation, section_preserve
- `ContextConfig`, `ContextFragment`, `CitationInfo`, `TokenUsageInfo`, `BuildContextInput`, `BuildContextResult`
- 7 exception classes
- 67 tests

### Changed
- Bumped version to 0.9.0

### Documentation
- ARCHITECTURE.md — full AI pipeline diagram, all layer responsibilities, provider DI pattern
- AI_WORKFLOW.md — retrieval flow, context assembly, implementation status table
- CURRENT_STATUS.md — 14 completed modules, 496 test summary, architecture health score
- CHANGELOG.md (root) — v0.9.0 entry with Phases C + D
- SESSION_NOTES.md — Phase D session notes
- PROJECT_OVERVIEW.md — new architecture, AI capabilities, provider/vector/context rationale
- DECISIONS.md — added DEC-024 through DEC-027
- Created AI_ARCHITECTURE_STATUS.md — master reference with component inventory, risk analysis, readiness assessment

---

## [0.8.0] — 2026-07-15

### Added

#### Phase A — Prompt Management System

- `app/prompts/cache.py` — `PromptCache` with TTL+LRU eviction, per-key TTL, hit/miss stats
- `app/prompts/loader.py` — `RAGPromptLoader` wrapping `CorePromptLoader`, `RAGPrompt` with
  `PromptVersion` (semver comparisons, content hashing)
- `app/prompts/manager.py` — `PromptManager` registry: `list_categories()`, `list_prompts()`,
  `get_prompt()`, `render()`, `get_version()`, `preload_all()`, `invalidate_cache()`
- YAML frontmatter fix: replaced hand-rolled parser with `yaml.safe_load`, quoted 18 values
  across all prompt files (16 dates, 2 guardrail lines with colons)
- 38 prompt management tests — all pass

#### Phase B — Provider-Independent Embedding Layer

- `app/embeddings/base_embedding.py` — `BaseEmbedding` ABC with 7 methods
- `app/embeddings/embedding_registry.py` — `EmbeddingRegistry` global registry
- `app/embeddings/embedding_factory.py` — `EmbeddingFactory.create()` config-driven instantiation
- `app/embeddings/schemas.py` — `EmbeddingMetadata`, `OutdatedEmbedding`, `ReEmbeddingResult`,
  `EmbeddingVersionInfo`, `MigrationResult`
- `app/embeddings/embedding_service.py` — `EmbeddingService` high-level API + `ReEmbeddingService` ABC
- `app/embeddings/config.py` — `EmbeddingConfig` dataclass
- `app/embeddings/exceptions.py` — 8 exception classes
- `app/embeddings/providers/gemini_embedding.py` — Full Gemini implementation
- `app/embeddings/providers/future/` — OpenAI, SentenceTransformers, Voyage skeletons
- `EMBEDDING_PROVIDER` config setting added to `app/core/config.py`
- 57 embedding tests — all pass

### Changed
- Medical parser frozen at MVP (extractor + validator only)
- Bumped version to 0.8.0

### Documentation
- ARCHITECTURE.md — updated AI workflow section with `app/prompts/` and `app/embeddings/`
- AI_WORKFLOW.md — updated RAG pipeline status and embedding strategy
- DECISIONS.md — added DEC-021 (Medical Parser Freeze), DEC-022 (Embedding Layer),
  DEC-023 (Prompt Management System)
- CURRENT_STATUS.md — new version, phases, progress
- CHANGELOG.md (root) — v0.8.0 entry
- SESSION_NOTES.md — current session update
- PROMPT_INDEX.md — previously updated with RAG prompt management docs

---

## [0.7.0] — 2026-07-14

### Added

#### Document Processing Pipeline Architecture (pre-implementation)
- `project_memory/DOCUMENT_PIPELINE.md` — Complete pipeline architecture covering 20 design areas:
  - **Pipeline Overview** — End-to-end flow diagram, 4-stage pipeline (Ingest → OCR → Extract → Index), status state machine with 7 states and valid transitions
  - **Upload** — Endpoint design (`POST /api/v1/reports/upload`), handler logic, response schema, concurrent upload limits (5/patient, 100MB/day), quarantine directory
  - **Validation** — 4-layer file validation (HTTP → extension → magic bytes → application), 9 validation rules with exact error responses, magic byte signature table
  - **Virus Scan** — ClamAV integration, scan flow with `ScanResult`, threat response matrix (clean/infected/unavailable/timeout), `security_scan_log` table schema
  - **Storage** — Directory structure (`quarantine/`, `originals/`, `processed/`, `thumbnails/`), S3 abstraction via `FileStorage` ABC with `LocalFileStorage` and `S3FileStorage` implementations, 5 storage security rules
  - **OCR** — 3-provider strategy (Google Vision primary, Tesseract fallback, direct PDF), selection logic, `GoogleVisionOCR` with `document_text_detection`, per-page result merging, Tesseract fallback with image preprocessing, direct PDF extraction with pypdf, OCR quality thresholds (≥0.9/0.7/0.5/<0.5)
  - **Preprocessing** — 7-step image pipeline (orientation → grayscale → denoise → CLAHE contrast → binarize → deskew → DPI normalize), cost-benefit table per step, `ImagePreprocessor` implementation
  - **Chunking** — Recursive character splitting with header-based pre-splitting, configurable parameters (500 token target, 50 token overlap), `DocumentChunker` with `DocumentChunk`/`ChunkMetadata` schemas, per-document-type chunking rules
  - **Medical Entity Extraction** — 5-step extraction pipeline, `DocumentClassifier` (prescription/lab/discharge via keyword scoring), `MedicalExtractor` with per-type extraction methods, `ExtractionResult` schema, 5 validation rules
  - **Medicine Parsing** — `MedicineNormalizer` with route/frequency alias expansion (po→oral, bid→twice daily, etc.), deduplication logic against existing active medicines, 6 medicine validation rules
  - **JSON Validation** — 4-step validation pipeline (extract → schema → repair → business), `SchemaLoader`, `JSONRepair` with enum/type coercion, `ValidationResult` schema
  - **Database Storage** — Atomic transaction flow (update report → create medicines → return), `store_extraction_results()` implementation, 5 error scenarios, 4 post-storage side effects
  - **Embedding Creation** — `text-embedding-3-small` (1536d), batch size 20, `EmbeddingService`, 4 quality checks, cost tracking
  - **Vector Database** — ChromaDB dev/prod config, collection schema with HNSW cosine, vector ID format `{report_id}_chunk_{index}`, 7 filterable metadata fields, 7 operations, GDPR deletion policy
  - **RAG** — 6-step pipeline (query generation → vector search → merge → compress → respond → cite), `Retriever` with deduplication and context compression, 4 filtering rules, 4 RAG quality metrics
  - **Failure Recovery** — 10-entry failure taxonomy per stage, `PipelineRecovery` with checkpoints and resume-from logic, graceful degradation table
  - **Background Processing** — Async worker model, `DocumentPipelineWorker`, priority queue (HIGH/NORMAL/LOW), 5 worker configuration parameters
  - **Retry Logic** — Per-stage retry table (0-3 retries, exponential backoff), retry state machine (PENDING→RUNNING→SUCCESS/FAILED→RETRY/EXHAUSTED), `RetryQueue` with dead-letter handling, `DeadLetterQueue` for manual recovery
  - **Queue Architecture** — Abstract `PipelineQueue` with in-memory (dev) and Redis (prod) implementations, `PipelineJob`/`PipelineResult` schemas, `QueueMonitor` with 8 metrics, periodic cleanup and orphan recovery
  - **9 Architecture Decision Records** (ADR-015 through ADR-023)

---

## [0.6.0] — 2026-07-14

### Added

#### AI Architecture Design (pre-implementation)
- `project_memory/AI_ARCHITECTURE.md` — Complete architecture document covering all 18 design areas:
  - Agent Responsibilities (6 agents with boundaries, ownership, forbidden cross-flows)
  - LangGraph State Design (base + 5 agent-specific TypedDict schemas, immutability rules)
  - Node Design (6 categories, complete node inventory for all agents, interface contract)
  - Edges & Routing (4 edge types, per-agent edge maps, conditional router functions, multi-agent orchestration)
  - Memory Architecture (6 memory types, conversation window strategy, context loaders)
  - Checkpointing & Persistence (`PostgresSaver`, thread ID strategy, TTL cleanup)
  - Error Recovery (6-category taxonomy, `safe_llm_call` handler, state-level accumulation, error router)
  - Retry Strategy (exponential backoff with jitter, 15s budget, `@with_retry` decorator)
  - Fallback LLM (4-tier model hierarchy, per-agent model priorities, `_rule_based_fallback`)
  - Tool Calling (8 approved tools, `ToolExecutor`, forbidden tool patterns)
  - Structured Outputs & JSON Schemas (per-agent schemas, `SchemaValidator`, repair strategies)
  - Hallucination Prevention (5-layer defense, specific rules per agent, hallucination risk score)
  - Medical Safety (4-layer architecture, 7 forbidden output types, disclaimer protocol, escalation rules, human-in-the-loop, audit trail schema)
  - Cost Optimization (model selection table, 7 cost-saving strategies, cost tracker, budget alerts)
  - Latency Optimization (target p50/p95/deadline, 8 techniques, parallel execution, timeout config)
  - Streaming Strategy (when to stream, SSE protocol, edge case handling)
  - Prompt Versioning (semver scheme, VERSIONS.json manifest, checksum verification, rollback, review workflow, test directory structure)
  - Evaluation Strategy (7 dimensions, 3-tier pipeline, LLM-as-Judge, A/B testing framework, monitoring dashboards, evaluation cadence)
  - 6 Architecture Decision Records (ADR-009 through ADR-014)

---

## [0.5.0] — 2026-07-14

### Added

#### Prompt Library
- 18 prompt templates across 6 categories (`medical/`, `chat/`, `emergency/`, `summary/`, `rag/`, `system/`) as standalone Markdown files in `backend/prompts/`
- Every prompt includes: Purpose, Input Variables, Output Schema, Guardrails, Examples, Version, Last Updated, Author, Future Improvements
- `PROMPT_INDEX.md` — central registry listing all 18 prompts with metadata
- `PromptLoader` class (`app/core/prompt_loader.py`) — dynamic loading, variable rendering, frontmatter parsing, in-memory caching, category filtering
- `system/system_config.md` — base identity, capabilities, limitations, ethical guidelines (v3)
- `system/guardrails.md` — content safety filter blocking harmful/misleading outputs (v2)
- `system/output_formatter.md` — JSON schema validation and repair for LLM outputs
- `medical/report_analysis.md` — clinical data extraction from OCR text (v1)
- `medical/medicine_extraction.md` — individual medicine entry parsing (v1)
- `medical/diagnosis_check.md` — diagnosis consistency verification (v1)
- `chat/patient_chat.md` — patient chat system prompt with context-aware Q&A (v2)
- `chat/medication_qa.md` — focused medication Q&A (v1)
- `chat/follow_up.md` — follow-up question generation (v1)
- `emergency/symptom_triage.md` — symptom urgency classification (v2)
- `emergency/risk_assessment.md` — escalation decision review (v1)
- `emergency/escalation.md` — structured doctor alert generation (v1)
- `summary/doctor_summary.md` — clinical summary for doctors (v2)
- `summary/appointment_summary.md` — pre-appointment brief (v1)
- `summary/weekly_report.md` — weekly care team report (v1)
- `rag/document_retrieval.md` — search query generation for ChromaDB (v1)
- `rag/context_compression.md` — chunk deduplication and prioritization (v1)
- `rag/citation_format.md` — inline citation formatting (v1)

### Changed
- Old Python prompt files (`app/prompts/*.py`) deprecated — marked with migration notice
- Old `app/agents/medical_agent/prompts.py` content migrated to `medical/medicine_extraction.md`
- AI_WORKFLOW.md updated — all agent spec prompt templates replaced with PromptLoader references

### Documentation
- AI_WORKFLOW.md — added Prompt Library architecture section, updated all 5 agent specs with prompt references
- PROMPT_INDEX.md — new central prompt registry
- CHANGELOG.md — v0.5.0 entry

---

## [0.4.0] — 2026-07-14

### Added

#### Production Data Layer (Sprint 3B)
- Alembic migration `0001_initial_schema.py` rewritten to match all 10 models exactly — columns, composite indexes, check constraints, FK `ondelete` actions, soft-delete, auto-update triggers
- `SeedData` class (`app/core/seed.py`) — 3 patients, 3 doctors, 3 reports, 3 medicines, 5 appointments, 6 chat messages, 5 adherence logs, 2 emergency alerts, with idempotent `_get_or_create()` logic
- `DatabaseHealthChecker` (`app/core/health.py`) — `HealthResult`/`DatabaseHealth` dataclasses; connection latency, table verification via `inspect()`, migration revision check, PostgreSQL-only pool/index queries
- Enhanced health API — `GET /api/v1/health` (table health, migration revision), `GET /api/v1/health/details` (per-table metadata, PostgreSQL version)
- `BackupManager` (`app/core/backup.py`) — `pg_dump` backup, `verify_backup()` (SQL header/size validation), `list_backups()` (human-readable sizes), `_cleanup_old_backups()` (`BACKUP_RETENTION_DAYS=30`), timeout/error handling
- `DatabaseReset` (`app/core/database_reset.py`) — `reset_schema()`, `truncate_all()` (dialect-aware DELETE vs TRUNCATE), `verify_schema()` via `inspect()`, `seed_data()` delegating to `SeedData`
- `QueryOptimizer` (`app/database/query_optimizer.py`) — eager-loading strategies per model, `paginate_with_optimization()` combining pagination with `selectinload` for N+1 prevention
- 44 integration tests (`tests/test_api/test_database_integration.py`) — model verification (4), relationship cascades (3), constraints (4), pagination (3), filtering (5), sorting (4), N+1/query optimization (2), seed data (6), health checks (5), database reset (5), soft delete (3)
- Updated `test_database_reset.py` (5 tests) and `test_health.py` (4 tests) for new APIs
- All 124 tests pass (121 passed, 3 skipped — PostgreSQL-specific)

### Changed
- Migration from stale auto-generated to hand-crafted single-revision target matching current SQLAlchemy models
- Database reset now uses `inspect()` for schema verification (works on SQLite + PostgreSQL)
- Seed data split from inline `seed_data()` function to dedicated `SeedData` class with admin doctor email `admin@healthcare.com`

### Documentation
- `DATABASE_DOCUMENTATION.md` fully rewritten: complete schema (all 10 tables), 16 composite indexes, 4 check constraints, auto-update triggers, ER diagram, seed data summary, health/backup/N+1 sections

---

## [0.2.0] — 2026-07-11

### Added

#### Production Authentication System
- 6 backend API endpoints: patient register, doctor register, unified login, logout, token refresh, get current user
- RefreshToken SQLAlchemy model with DB-backed token storage (jti, token_hash, user_id, role, is_revoked)
- Token rotation on every refresh (revoke old pair, issue new pair)
- Token pair generation with UUID v4 jti embedded in JWT payload
- SHA-256 token hashing for secure database storage
- Strong password validation (8+ chars, uppercase, lowercase, number, special character)
- Phone number validation (E.164 international format)
- Email validation via Pydantic EmailStr
- Date of birth validation (ISO format, must be past)
- Gender validation (restricted to allowed values)
- Terms acceptance enforcement for patient registration
- Confirm password matching validation
- Doctor fields: hospital_name, years_of_experience
- Patient fields: terms_accepted, terms_accepted_at
- Remember Me: 30-day refresh tokens vs 7-day default
- `require_role()` FastAPI dependency factory
- `MeResponse` and `RefreshResponse` Pydantic models for precise API contracts
- 18 comprehensive unit tests covering all auth flows

#### Frontend Auth Enhancements
- Unified login page with role toggle, remember me checkbox, forgot password link
- 2-step registration wizard (role selection → full form with validation)
- Strong client-side password validation via Zod (matching server rules)
- Axios interceptor with refresh queue pattern (prevents concurrent refresh storms)
- Enhanced Zustand store with rememberMe, isLoading, setTokens, getRole
- Server-side logout API call in patient and doctor layouts
- Middleware with role-based redirects parsing Zustand cookies

#### Project Memory System
- Created `project_memory/` with 10 documentation files
- Persistent project memory for multi-session development
- Architecture Decision Records (ADR-001 through ADR-008)
- Automated API documentation with request/response examples
- Database schema documentation with ER diagram
- AI workflow documentation with LangGraph diagrams

### Changed
- Access token expiry reduced from 30 minutes to 15 minutes
- Login endpoint unified from `/auth/patient/login` + `/auth/doctor/login` to single `/auth/login` with role parameter
- Register endpoint paths: `/auth/patient/register` → `/auth/register/patient`
- Updated PROJECT_PLAN.md with Phase 2 completion
- Updated TASKS.md with 15 new auth tasks, 96 total tasks
- Updated test fixtures with strong password format

### Security
- bcrypt password hashing (never stored in plain text)
- Refresh tokens stored as SHA-256 hashes (never stored as plain JWTs)
- Token rotation prevents replay attacks
- Server-side token revocation for immediate logout
- UUID v4 jti in every refresh token
- Short-lived access tokens (15 min) minimize XSS damage window
- Strong password policy enforced server-side and client-side

---

## [0.1.0] — 2026-07-03

### Added

#### Backend Foundation
- FastAPI application scaffold with modular architecture (API → Service → Repository → Model)
- Core configuration via Pydantic Settings
- JWT token generation (access + refresh) with bcrypt password hashing
- Custom exception hierarchy (AppException, NotFoundException, UnauthorizedException, etc.)
- SQLAlchemy sync + async database sessions
- Base model with UUID primary key and timestamp mixins

#### Database Models (9 tables)
- Patient, Doctor, PatientDoctor, Report, Medicine, Appointment
- ChatHistory, AdherenceLog, EmergencyAlert

#### Pydantic Schemas (10 modules)
- Auth, Patient, Doctor, Medicine, Report, Chat, Adherence, Emergency, Summary, Appointment

#### Repository Layer
- Generic BaseRepository with CRUD operations
- 8 specialized repositories with custom queries

#### Service Layer
- 10 service classes implementing business logic
- AuthService, PatientService, DoctorService, ReportService, MedicineService
- ChatService, AdherenceService, EmergencyService, SummaryService, AppointmentService

#### API Routes (6 routers, 20+ endpoints)
- Full authentication API (register, login, refresh)
- Patient CRUD, Doctor CRUD, Report upload/download, Chat, Appointments

#### LangGraph Agent Skeletons
- Medical Report Agent (3 nodes)
- Patient Chat Agent (2 nodes)
- Reminder Agent (3 nodes)
- Emergency Detection Agent (3 nodes)
- Doctor Summary Agent (2 nodes)
- Agent Orchestrator

#### RAG System Skeletons
- EmbeddingService, VectorStore (ChromaDB), Retriever

#### OCR System Skeletons
- GoogleVisionOCR, ImagePreprocessor

#### Frontend Foundation
- Next.js 15 with App Router, TypeScript, Tailwind CSS
- shadcn/ui primitives (7 components)
- Shared components (ThemeProvider, ThemeToggle, LoadingState, EmptyState)
- Complete type system (User, Patient, Doctor, Medicine, etc.)
- Zustand auth + UI stores with persist middleware
- Axios API client with JWT interceptor
- 7 service modules (auth, patients, medicines, reports, chat, doctor)
- 12 pages across login, register, patient, doctor routes
- 3 layouts (auth centered, patient sidebar, doctor sidebar)
- Auth middleware for route protection
- Full dark mode support with CSS variable theming

#### Infrastructure
- Docker Compose (PostgreSQL 16 + ChromaDB + Backend + Frontend)
- Multi-stage Dockerfiles (backend + frontend)
- PostgreSQL init script with uuid-ossp and pgcrypto
- GitHub Actions CI/CD (lint, test, build)
- Code quality tools (Black, isort, flake8, mypy, pre-commit)
- Setup scripts (PowerShell + Bash)

#### Documentation
- README.md, ARCHITECTURE.md, PROJECT_PLAN.md, TASKS.md, CHANGELOG.md
- 32 completed Phase 1 tasks documented

---

## [0.0.0] — 2026-07-03

### Added
- Project initialization
- Repository created
- Architecture planning
