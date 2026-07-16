# AI Workflow Documentation

> Documents all AI components, LangGraph agents, RAG pipeline, Prompt Library,
> Retrieval Layer, Context Builder, and LLM configuration.
> Update whenever AI workflows change.

---

**Last Updated:** 2026-07-16
**Current Version:** 0.17.0
**Current AI Phase:** Phase M — Clinical Validation, Dataset Management & AI Optimization (Complete)

---

## LangGraph Runtime

**Status:** v1.0.0 — Production integrated (2026-07-16)

The LangGraph Runtime (`app/langgraph/`) provides a reusable orchestration layer that
coordinates all existing subsystems (Agent, Memory, Tool, RAG) without moving business
logic into LangGraph.

### Design Principles

| Principle | Implementation |
|-----------|----------------|
| LangGraph is ONLY orchestration | All business logic stays in existing frameworks |
| Single responsibility nodes | No database logic, no provider-specific code, no SQLAlchemy |
| Strongly typed state | `GraphState` dataclass with all pipeline fields |
| Injected services | Services wired via `state.services` dict from `GraphContext` |
| Idempotent nodes | All node functions accept and return `GraphState` |
| Event-driven observability | `EventBus` with typed `GraphEvent` for graph/node lifecycle |

### Module Structure

| Module | Description |
|--------|-------------|
| `config.py` | `LangGraphConfig` — graph name, timeouts, retries, feature flags |
| `exceptions.py` | 8 exception classes rooted at `LangGraphError` |
| `graph_state.py` | `GraphState` dataclass, `GraphPhase`/`GraphStatus` enums |
| `graph_context.py` | `GraphContext` with DI for MemoryService, AgentExecutor, etc. |
| `graph_events.py` | `EventBus` with subscribe/emit, 10 `GraphEventType` values |
| `graph_checkpoint.py` | `BaseCheckpointStore` ABC + `InMemoryCheckpointStore` |
| `graph_metrics.py` | `MetricsCollector` with per-node timing, latency, token tracking |
| `graph_registry.py` | `GraphRegistry` with global singleton |
| `graph_factory.py` | `GraphFactory.create()` / `create_or_none()` |
| `graph_executor.py` | `GraphExecutor` with retry, timeout, event emission, trace recording |
| `graph_runtime.py` | `BaseGraph` ABC with `execute()`/`resume()`/`checkpoint()`/`shutdown()` |
| `bootstrap.py` | `GraphBootstrap` — registration, dependency validation, diagnostics |
| `graphs/medical_qa_graph.py` | `MedicalQAGraph` — 8-node pipeline |
| `nodes/*.py` | 8 single-responsibility node functions |
| `edges/*.py` | 2 conditional routing edges |

### MedicalQAGraph Pipeline

```
START
  │
  ▼
load_memory_node ─── loads MemoryService entries into state.memory_entries
  │
  ▼
medical_qa_node ─── executes AgentExecutor(MedicalQAAgent) → state.agent_response
  │
  ▼
tool_selector_node ─── keyword analysis → state.need_tool
  │
  ├──need_tool?──YES──→ tool_executor_node ─── ToolService.run_from_query()
  │                                              │
  │                                              ▼
  │                                         (fall through)
  │                                              │
  └──NO_tool─────────────────────────────────────┘
  │
  ▼
need_retrieval?
  │
  ├──YES──→ retriever_node ─── RAGEngine.answer()
  │            │
  │            ▼
  │       context_builder_node ─── ContextBuilder.build_from_fragments()
  │            │
  └────────────┘
  │
  ▼
response_generator_node ─── picks best answer (agent > rag > tool > fallback)
  │
  ▼
persist_memory_node ─── MemoryService.extract_from_chat()
  │
  ▼
END
```

### Production Startup Sequence

```
FastAPI Lifespan (app/main.py)
  └─ GraphBootstrap.run_full_bootstrap()
       ├─ register_graphs()
       │    └─ GraphRegistry.register("medical_qa", MedicalQAGraph)
       └─ validate_dependencies()
            ├─ AI provider (gemini)
            ├─ RAG engine
            ├─ Memory service
            ├─ Tool service (9 tools)
            ├─ MedicalQAAgent
            ├─ Retriever service
            ├─ Context builder
            ├─ Embedding service
            ├─ Vector store
            └─ Prompt manager
```

### Chat Request Execution Path

```
POST /api/v1/chat/message
  │
  ├─ Auth check (JWT)
  ├─ Save to DB (ChatService.save_message)
  │
  └─ GraphChatService.ask()
       │
       └─ MedicalQAGraph.execute(state)
            └─ _run_pipeline()
                 ├─ load_memory
                 ├─ medical_qa (AgentExecutor wrapping MedicalQAAgent)
                 ├─ tool_selector
                 ├─ tool_executor (conditional)
                 ├─ retriever (conditional)
                 ├─ context_builder (conditional)
                 ├─ response_generator
                 └─ persist_memory
       │
       └─ Convert GraphState → ChatResponse
            ├─ answer from agent/rag/tool
            ├─ confidence from retrieved evidence
            ├─ suggested_questions (unchanged)
            ├─ session_id (preserved)
            └─ processing_time_ms
```

---

## Prompt Library

**Status:** v1.0.0 — all prompts migrated to standalone Markdown files (2026-07-14)

[Full Prompt Library section unchanged from previous version]

---

## AI Provider Layer

**Status:** v1.0.0 — Implemented (2026-07-14)

[AI Provider Layer section unchanged from previous version]

---

## Embedding Layer

**Status:** v1.0.0 — Implemented (2026-07-15)

[Embedding Layer section unchanged from previous version]

---

## Document Processing Pipeline

**Status:** v1.0.0 — Implemented (2026-07-15)

[Document Processing Pipeline section unchanged from previous version]

---

## Vector Store Layer

**Status:** v1.0.0 — Implemented (2026-07-15)

[Vector Store Layer section unchanged from previous version]

---

## Retrieval Layer

**Status:** v1.0.0 — Implemented (2026-07-15)

[Retrieval Layer section unchanged from previous version]

---

## Context Builder

**Status:** v1.0.0 — Implemented (2026-07-15)

[Context Builder section unchanged from previous version]

---

## RAG Engine

**Status:** v1.0.0 — Implemented (2026-07-15)

[RAG Engine section unchanged from previous version]

---

## Medical Document QA Agent

**Status:** v1.1.0 — Updated for LangGraph integration (2026-07-16)

### Changes in v1.1.0

The `ChatService` now supports two execution paths:

1. **Graph path** (default when graph is available): Routes through `MedicalQAGraph`, which orchestrates memory loading, agent execution (via `AgentExecutor`/`MedicalQAAgent`), tool calling (conditional), retrieval (conditional), context building, response generation, and memory persistence.

2. **Direct path** (fallback): Original RAG-only path — calls `RAGEngine.answer()` directly.

Both paths produce identical `ChatResponse` contracts. The graph path adds:
- Memory loading before agent execution
- Tool execution when the query contains scheduling/keyword patterns
- Memory persistence after response generation
- Full execution trace and metrics collection
- Event emission for observability

### Architectural Change

```
Before:  ChatService → RAGEngine.answer() → ChatResponse

After:   ChatService → MedicalQAGraph.execute()
           ├─ load_memory (if memory_service available)
           ├─ medical_qa (via AgentExecutor → MedicalQAAgent)
           ├─ tool_selector → tool_executor (conditional)
           ├─ retriever → context_builder (conditional)
           ├─ response_generator
           └─ persist_memory (if memory_service available)
           └─ ChatResponse
```

MedicalQAAgent is now only executed via the graph node `medical_qa_node`, not called directly by `ChatService`.

---

## AI Evaluation & Benchmarking Framework

**Status:** v1.0.0 — Complete (2026-07-15)

[AI Evaluation section unchanged from previous version]

---

## Current Implementation Status

| AI Component | Status | Module | Tests | Dependencies |
|-------------|--------|--------|-------|-------------|
| Provider Layer | ✅ Implemented | `app/ai/` | — | None |
| Prompt System | ✅ Implemented | `app/prompts/` | 38 | Prompt files |
| Embedding Layer | ✅ Implemented | `app/embeddings/` | 57 | AI Provider |
| Document Pipeline | ✅ Implemented | `app/document_pipeline/` | 88 | Embedding Layer |
| Vector Store | ✅ Implemented | `app/vector_store/` | 94 | Embedding Layer |
| Retrieval Layer | ✅ Implemented | `app/retrieval/` | 57 | Vector Store |
| Context Builder | ✅ Implemented | `app/context/` | 67 | Retrieval Layer |
| RAG Engine | ✅ Implemented | `app/rag/` | 74 | Retrieval + Context + AI Provider + Prompts |
| Medical QA Agent | ✅ Implemented | `app/chat/` | 62 | RAG Engine + AI Provider |
| AI Evaluation | ✅ Implemented | `app/evaluation/` | 190 | None |
| Memory Framework | ✅ Implemented | `app/memory/` | 133 | None |
| Agent Framework | ✅ Implemented | `app/agents/` | 76 | All above |
| Tool Calling Framework | ✅ Implemented | `app/tools/` | 116 | Agent Framework |
| LangGraph Runtime | ✅ Implemented | `app/langgraph/` | 101 | All above |
| Integration Tests | ✅ Passing | `tests/test_integration/` | 182 | All above |
| Clinical Validation (Phase M) | ✅ Implemented | `app/validation/` | 110 | All above |
| Conversation Memory | ⏳ Not Started | — | — | RAG Engine |
| Chat Agent (LangGraph) | ✅ Runtime Ready | `app/langgraph/` | — | RAG Engine + Memory |
| Medical Agent | ⏳ Not Started | — | — | RAG Engine |
| Emergency Agent | ⏳ Not Started | — | — | Chat Agent |
| Summary Agent | ⏳ Not Started | — | — | All agents |
| Reminder Agent | ⏳ Not Started | — | — | Medical Agent |
| Orchestrator | ⏳ Not Started | — | — | All agents |

**Total Tests:** ~1754 passing (all modules + integration)

---

## Clinical Validation Pipeline (Phase M)

**Status:** ✅ Implemented (v0.17.0 — 2026-07-16)

The Clinical Validation Pipeline (`app/validation/`) provides dataset management, benchmarking, optimization, and evaluation capabilities without adding new AI infrastructure.

### Dataset Management

- 10 document types with structured extraction, ground truth, and expected QA pairs
- JSON/JSONL load/save with format versioning
- CRUD operations, import/export, stats, caching
- Validation (structural integrity) + train/val/test splitting

### Benchmark System

- 12 standard metrics: Retrieval Recall, Precision@K, MRR, NDCG, Citation P/R/F1, Groundedness, Answer Relevance, Hallucination Rate, Latency, Memory, Tokens
- Warmup + multi-run execution with statistical aggregation (P50/P95/P99)
- Persistent history with regression comparison

### Optimization Module

- Chunk optimization: grid search over size (128-2048), overlap (0-128), 4 strategies
- Prompt optimization: variant registration, weighted scoring
- Retrieval optimization: grid search over top_k, threshold, rerank, hybrid, MMR
- Reranking optimization: 5 strategies with configurable penalties

### Evaluation Suite

- Clinical test runner with per-question answer matching, citation scoring, difficulty/category breakdown
- Regression suite with configurable quality thresholds (latency, recall, hallucination, citations, groundedness, relevance, tokens)
- Report generator with 4 report types + performance dashboard JSON
- Statistics: confusion matrix, precision/recall/F1, McNemar test, confidence intervals

### 110 Validation Tests — All Passing, Zero Regressions

## Future Improvements

- Persistent checkpoint store (Redis/PostgreSQL) for production resilience
- Hybrid search (semantic + keyword BM25)
- Cross-encoder re-ranking for improved relevance
- Multi-query generation for complex questions
- Streaming context assembly for real-time responses
- Citation source highlighting in frontend
- Feedback loop for retrieval quality
- A/B prompt testing via LangSmith Hub
