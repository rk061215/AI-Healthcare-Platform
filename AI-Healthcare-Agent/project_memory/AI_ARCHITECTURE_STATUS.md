# AI Architecture Status

> Master reference document for all AI development in the AI Healthcare Follow-up Assistant.
> This document is the single source of truth for AI component status, pipeline architecture,
> risk analysis, and readiness assessment.
>
> **Last Updated:** 2026-07-15
> **Current Phase:** Phase J — Tool Calling Framework (Complete)
> **Next Phase:** LangGraph Runtime (StateGraph, checkpointing, error recovery)

---

## Table of Contents

1. [AI Component Inventory](#1-ai-component-inventory)
2. [Current AI Pipeline](#2-current-ai-pipeline)
3. [Future AI Pipeline](#3-future-ai-pipeline)
4. [Risk Analysis](#4-risk-analysis)
5. [Readiness Assessment](#5-readiness-assessment)
6. [Dependency Graph](#6-dependency-graph)

---

## 1. AI Component Inventory

### Status Definitions

| Status | Meaning |
|--------|---------|
| 🔴 Not Started | No implementation begun |
| 🟡 Skeleton | ABC/interface defined; providers raise `NotImplementedError` |
| 🟢 Implemented | Fully functional with at least one active provider |
| ✅ Production Ready | Implementation, tests, docs complete; ready for use |
| N/A | Not applicable to this component |

### Component Inventory

| # | Component | Module | Status | Test Coverage | Dependencies | Notes |
|---|-----------|--------|--------|---------------|--------------|-------|
| 1 | **AI Provider Layer** | `app/ai/` | 🟢 Implemented | — | None | ABC → Registry → Factory → Service → GeminiProvider, OpenAI/Anthropic skeletons |
| 2 | **OCR System** | `app/ocr/` | 🟡 Skeleton | — | Tesseract, Google Vision | Interface defined; not yet wired to document pipeline |
| 3 | **Medical Parser** | `app/medical_parser/` | 🟢 Implemented | — | None | Frozen at MVP (extractor + validator only) |
| 4 | **Prompt System** | `app/prompts/` + `backend/prompts/` | ✅ Production Ready | 38 | 18 Markdown files | PromptManager with TTL+LRU cache, versioning, registry |
| 5 | **Embedding Layer** | `app/embeddings/` | ✅ Production Ready | 57 | AI Provider (Gemini) | ABC → Registry → Factory → Service → GeminiEmbedding, 3 future skeletons |
| 6 | **Document Pipeline** | `app/document_pipeline/` | ✅ Production Ready | 88 | Embedding Layer | 6-stage pipeline, 5 chunkers, metadata enrichment, version tracking |
| 7 | **Vector Store** | `app/vector_store/` | ✅ Production Ready | 94 | Embedding Layer | ABC → Registry → Factory → Service → ChromaDBStore, 3 future skeletons |
| 8 | **Retrieval Layer** | `app/retrieval/` | ✅ Production Ready | 57 | Vector Store | ABC → Registry → Factory → Service → VectorRetriever, 2 future skeletons |
| 9 | **Context Builder** | `app/context/` | ✅ Production Ready | 67 | Retrieval Layer | 6-stage pipeline, 3 budget strategies, citation generation |
| 10 | **RAG Engine** | `app/rag/` | ✅ Production Ready | 74 | Retrieval + Context + LLM | Full pipeline: process → classify → rewrite → orchestrate → pre-grds → generate → post-grds → citations → disclaimer. 12 files, 11 exceptions, 5 models. |
| 11 | **Memory Framework** | `app/memory/` | ✅ Production Ready | 133 | RAG Engine | Provider-independent memory system: 5 types, 4 processors, 3 policies, InMemoryStore, registry/factory, MemoryService. 26 files, 133 tests. |
| 12 | **Medical QA Agent** | `app/chat/` + `app/agents/agents/medical_qa_agent.py` | ✅ Production Ready | 62 | RAG Engine + Agent Framework | Refactored to inherit BaseAgent. Wraps ChatService, zero regressions. |
| 13 | **Evaluation & Benchmarking** | `app/evaluation/` | ✅ Production Ready | 190 | None | AI quality measurement framework. 16 files: retrieval/RAG/hallucination/citation/medical QA metrics, dataset loader, ground truth, benchmark runner, report generator. |
| 14 | **Agent Framework** | `app/agents/` | ✅ Production Ready | 76 | Memory + RAG | BaseAgent ABC, AgentRegistry, AgentFactory, AgentExecutor, AgentService, AgentContext/State/Response, MedicalQAAgent, 5 future skeletons. 22 files. |
| 15 | **Medical Report Agent** | `app/agents/medical_agent/` | 🟡 Skeleton | — | Agent Framework | LangGraph: extract → validate → store |
| 16 | **Reminder Agent** | `app/agents/future/reminder_agent.py` | 🟡 Skeleton | — | Agent Framework | Inherits BaseAgent |
| 17 | **Emergency Agent** | `app/agents/future/emergency_agent.py` | 🟡 Skeleton | — | Agent Framework | Inherits BaseAgent |
| 18 | **Doctor Summary Agent** | `app/agents/future/doctor_summary_agent.py` | 🟡 Skeleton | — | Agent Framework | Inherits BaseAgent |
| 19 | **FollowUp Agent** | `app/agents/future/followup_agent.py` | 🟡 Skeleton | — | Agent Framework | Inherits BaseAgent |
| 20 | **Appointment Agent** | `app/agents/future/appointment_agent.py` | 🟡 Skeleton | — | Agent Framework | Inherits BaseAgent |
| 21 | **Tool Calling Framework** | `app/tools/` | ✅ Production Ready | 116 | Agent Framework | BaseTool ABC, Registry, Factory, Executor, Selector, Service. 5 domain tools (appointment, patient, doctor, report, medication) + 4 future skeletons. 28 files, 116 tests. |
| 22 | **LangGraph Runtime** | (Pending) | 🔴 Not Started | — | Agent Framework | StateGraph, checkpointing, error recovery |
| 23 | **Multi-Agent System** | (Pending) | 🔴 Not Started | — | Orchestrator + all agents | Cross-agent handoffs, parallel execution |

---

## 2. Current AI Pipeline

### Visual Diagram

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                      CURRENT AI PIPELINE (v0.15.0)                                │
│                                                                                   │
│  Document Ingestion Path:                                                         │
│  ┌────────┐  ┌────────┐  ┌─────────────┐  ┌────────┐  ┌────────┐               │
│  │ Upload │─▶│  OCR   │─▶│   Document   │─▶│ Embed  │─▶│ Vector │               │
│  │ Report │  │(Future)│  │  Pipeline    │  │  (Gemini)│  │ Store  │               │
│  └────────┘  └────────┘  └─────────────┘  └────────┘  └────────┘               │
│                          5 chunkers        57 tests     94 tests                 │
│                          88 tests                                                │
│                                                                                   │
│  Retrieval Path:                                                                  │
│  ┌────────┐  ┌────────┐  ┌─────────────┐  ┌───────────────┐                    │
│  │ Query  │─▶│ Embed  │─▶│  Retrieval  │─▶│    Context    │                    │
│  │        │  │(Gemini)│  │   Layer     │  │   Builder     │                    │
│  └────────┘  └────────┘  └─────────────┘  └───────────────┘                    │
│                           57 tests         67 tests                             │
│                                                                                   │
│  RAG Path:                                                                        │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────────┐                         │
│  │ Query → Proc │─▶│  RAG Engine │─▶│  RAG Response  │                         │
│  │ → Classify → │  │  Orchestrate│  │  Answer +      │                         │
│  │ → Rewrite →  │  │  → Gen →    │  │  Citations +   │                         │
│  │ Retrieve     │  │ Guardrails  │  │  GuardrailRes  │                         │
│  └──────────────┘  └─────────────┘  └────────────────┘                         │
│                 74 tests                                                         │
│                                                                                   │
│  QA Path:                                                                         │
│  ┌────────┐  ┌───────────────┐  ┌────────────────┐  ┌──────────────────┐      │
│  │ User   │─▶│  ChatService  │─▶│  RAGEngine.     │─▶│  ChatResponse    │      │
│  │ Ques.  │  │  (Session +   │  │  answer()       │  │  Answer +        │      │
│  │        │  │   Confidence  │  │                 │  │  Citations +     │      │
│  │        │  │   + Suggester │  │                 │  │  Confidence +    │      │
│  │        │  │   + Format)   │  │                 │  │  Suggestions     │      │
│  └────────┘  └───────────────┘  └────────────────┘  └──────────────────┘      │
│                 62 tests                                                         │
│  Result: User-facing ChatResponse with answer + citations + confidence score +   │
│           suggested follow-up questions                                          │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Pipeline Responsibilities

| Stage | Component | Input | Output | Responsibility |
|-------|-----------|-------|--------|----------------|
| 1 | OCR | Report file (PDF/Image) | Raw text | Extract text from documents (skeleton) |
| 2 | Document Pipeline | Raw OCR text | Clean, chunked documents with metadata | Clean text, classify, detect sections, chunk, enrich metadata |
| 3 | Embedding Layer | Document chunks | Vector embeddings | Convert text to numerical vectors via Gemini |
| 4 | Vector Store | Embeddings + metadata | Indexed documents | Store vectors in ChromaDB, enable semantic search |
| 5 | Retrieval Layer | Query text | Retrieved documents | Embed query, search ChromaDB, filter by patient/report/type |
| 6 | Context Builder | Retrieved documents | Optimized context string | Dedup, rank, compress, apply token budget, generate citations |
| 7 | RAG Engine | Query + Context | RAGResponse (answer + citations + guardrails) | Process → classify → (rewrite) → orchestrate → pre-guardrails → generate → post-guardrails → citations → disclaimer |

### Inputs & Outputs

| Component | Input | Output |
|-----------|-------|--------|
| Document Pipeline | `raw_text: str`, `patient_id`, `report_id`, `source`, `language`, `provider`, `page_count` | `list[DocumentChunk]` with full metadata |
| Embedding Layer | `text: str` or `list[str]` | `list[float]` (single) or `list[list[float]]` (batch) |
| Vector Store | `documents: list[str]`, `embeddings`, `metadatas` | Collection with indexed vectors |
| Retrieval Layer | `query: str`, optional `patient_id`, `report_id`, `document_type`, `top_k`, `threshold` | `RetrievalResult` with `list[RetrievedDocument]` + metrics |
| Context Builder | `list[RetrievedDocument]`, `query: str` | `BuildContextResult` with `context: str`, `citations`, `fragments`, `token_usage` |

---

## 3. Future AI Pipeline

### Planned Pipeline (Phases E+)

```
┌────────┐   ┌───────────────┐   ┌───────────────┐   ┌──────────────┐
│ Query  │──▶│  Retriever    │──▶│  Context      │──▶│   RAG Engine │
│        │   │  (search +    │   │  Builder      │   │  (DONE)      │
│        │   │   filter)     │   │  (dedup, rank, │   │  LLM call +  │
│        │   │               │   │   compress,    │   │  guardrails  │
│        │   │               │   │   budget,      │   │  + citations │
│        │   │               │   │   citations)   │   │              │
│        │   │               │   │               │   │              │
│        │   │   57 tests    │   │   67 tests    │   │   74 tests   │
│        │   │   ✅ Done     │   │   ✅ Done     │   │   ✅ Done    │
└────────┘   └───────────────┘   └───────────────┘   └──────┬───────┘
                                                             │
                                                             ▼
                                                    ┌──────────────┐
                                                    │ Conversation │
                                                    │   Memory     │
                                                    │  (NEW)       │
                                                    │  history +   │
                                                    │  summariz.   │
                                                    └──────┬───────┘
                                                             │
                                                             ▼
┌────────────────────────────────────────────────────────────┐
│                   CHAT AGENT (LangGraph)                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │ Retrieve   │  │  Generate  │  │  Guardrails│           │
│  │ Context    │──▶  Response  │──▶  + Format  │           │
│  └────────────┘  └────────────┘  └────────────┘           │
└────────────────────────────────────────────────────────────┘
                                                             │
                                                             ▼
┌────────────────────────────────────────────────────────────┐
│              MEDICAL AGENTS (LangGraph)                     │
│                                                             │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────┐     │
│  │  Medical   │  │   Emergency  │  │   Summary      │     │
│  │  Report    │  │   Detection  │  │   Agent        │     │
│  │  Agent     │  │   Agent      │  │   (Doctor)     │     │
│  └──────┬─────┘  └──────┬───────┘  └───────┬────────┘     │
│         │               │                  │              │
│         ▼               ▼                  ▼              │
│  ┌────────────┐  ┌──────────────┐                         │
│  │  Reminder  │  │  Reminder    │                         │
│  │  Agent     │  │  Agent       │                         │
│  └────────────┘  └──────────────┘                         │
└────────────────────────────────────────────────────────────┘
                                                             │
                                                             ▼
┌────────────────────────────────────────────────────────────┐
│              MULTI-AGENT ORCHESTRATOR                       │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────┐     │
│  │  Router    │  │  Cross-agent  │  │   Response     │     │
│  │  Node      │──▶  Handoff     │──▶  Aggregator    │     │
│  └────────────┘  └──────────────┘  └────────────────┘     │
└────────────────────────────────────────────────────────────┘
```

### Pipeline Stage Details (Future)

| Stage | Component | Status | Input | Output | Key Design Decisions |
|-------|-----------|--------|-------|--------|---------------------|
| 1 | Retrieval Layer | ✅ Complete | Query text, filters | Retrieved documents | Provider-independent, vector search |
| 2 | Context Builder | ✅ Complete | Retrieved documents | Optimized context | Pre-LLM dedup/rank/budget/citations |
| 3 | RAG Engine | ✅ Complete | Context + query | LLM response + citations | Orchestrate retrieval → context → LLM → guardrails |
| 4 | Medical QA Agent | ✅ Complete | Patient question + document context | Answer + citations + confidence + suggestions | Session-based, no LangGraph; rule-based confidence + suggestions |
| 5 | Conversation Memory | 🔴 Pending | Chat history | Windowed/summarized context | 20-message window + summarization |
| 6 | Medical Report Agent | 🟡 Skeleton | OCR text | Structured data | LangGraph: 5 nodes |
| 7 | Emergency Agent | 🟡 Skeleton | Symptoms | Risk level + alert | LangGraph: 5 nodes |
| 8 | Summary Agent | 🟡 Skeleton | Patient data | Clinical summary | LangGraph: 4 nodes |
| 9 | Reminder Agent | 🟡 Skeleton | Medicines | Schedule + reminders | Rule-based + LLM messages |
| 10 | Orchestrator | 🟡 Skeleton | Request type | Routed to agent | LangGraph parent graph |

---

## 4. Risk Analysis

### Potential Architectural Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|------------|--------|------------|
| R1 | ChromaDB does not scale beyond 100K chunks | Medium | High | Provider-independent vector store (DEC-026) enables migration to Qdrant/Pinecone without code changes |
| R2 | Gemini free tier rate limits (60 req/min) block production use | Medium | Medium | Provider-independent AI layer (DEC-027); add queue/batch processing |
| R3 | Token estimation heuristic (~3 chars/token) is inaccurate for non-English | Low | Medium | Switch to tiktoken-based estimation for production; heuristic sufficient for MVP |
| R4 | Context Builder section_preserve strategy drops relevant non-priority content | Low | Medium | Strategy is configurable; default to priority_truncation for general use |
| R5 | LangGraph API instability during agent development | Medium | High | Pin LangGraph version; wrap in adapter layer if needed |
| R6 | Retriever/Context Builder provider abstraction not needed for single-provider MVP | Low | Low | Abstraction adds minimal overhead (4 files per layer); enables testing without ChromaDB |
| R7 | Document Pipeline chunker choice significantly impacts retrieval quality | Medium | Medium | 5 chunking strategies available; configuration-driven; test to find optimal strategy |

### Scalability Concerns

| Concern | Current State | Future State | Trigger for Action |
|---------|--------------|--------------|-------------------|
| Vector search latency | Sub-100ms for <10K chunks | Target <500ms p95 at 1M chunks | p95 latency >500ms |
| Embedding throughput | Single-batch Gemini calls | Batch processing with queue | >1000 chunks/day |
| Context assembly time | Sub-50ms for 20 fragments | Target <200ms for 100 fragments | Assembly time >200ms |
| Token budget compliance | Heuristic estimation | tiktoken-based estimation | Budget misses >10% |
| Multi-tenant isolation | Patient-scoped filtering | Row-level security + collection per patient | >1000 patients |

### Performance Bottlenecks

| Bottleneck | Component | Current Performance | Improvement Path |
|------------|-----------|-------------------|-----------------|
| Embedding generation | EmbeddingService | ~500ms per chunk | Batch embedding, caching |
| Vector search | ChromaDBStore | ~50ms per query | HNSW index tuning, quantization |
| Context dedup | Deduplicator | ~10ms for 20 docs | Hash-based dedup, index by chunk_id |
| Token budgeting | TokenBudgetManager | ~5ms per run | Pre-compute token counts at index time |
| Citation formatting | CitationGenerator | ~2ms per run | Template-based formatting |

### Future Migration Considerations

| Migration | From | To | Complexity | Prerequisites |
|-----------|------|----|------------|---------------|
| Vector store | ChromaDB | Qdrant | Low (DEC-026) | Implement QdrantStore ABC |
| Vector store | ChromaDB | pgvector | Medium | Schema migration, hybrid query support |
| Vector store | ChromaDB | Pinecone | Low (DEC-026) | Implement PineconeStore ABC |
| Embedding | Gemini | OpenAI | Low (DEC-022) | Implement OpenAI embedding skeleton |
| Embedding | Gemini | Local (sentence-transformers) | Low (DEC-022) | Implement SentenceTransformers provider |
| LLM | Gemini | OpenAI | Low (DEC-027) | Implement OpenAI provider |
| Token estimation | Heuristic | tiktoken | Low | Add tiktoken dependency |
| RAG Engine | Standalone RAG Engine | LangGraph Agent RAG | Medium | Phase F agent integration |

---

## 5. Readiness Assessment

### Scoring Rubric

| Score | Meaning |
|-------|---------|
| 0-2 | Not started / Skeleton only |
| 3-4 | Implemented but limited |
| 5-7 | Functional, tests pass, production-ready |
| 8-10 | Battle-tested, comprehensive tests, documentation |

### Subsystem Readiness Scores

| Subsystem | Score | Notes |
|-----------|-------|-------|
| **Provider Layer** (`app/ai/`) | 6/10 | ABC + Registry + Factory + Service + GeminiProvider. Skeletons for OpenAI/Anthropic. No integration tests. |
| **OCR System** (`app/ocr/`) | 2/10 | Interface defined. GoogleVisionOCR skeleton. No active implementation. |
| **Prompt System** (`app/prompts/` + `backend/prompts/`) | 9/10 | 18 prompts, 6 categories, versioned, cached, registered. PromptManager API. 38 tests. |
| **Embedding Layer** (`app/embeddings/`) | 9/10 | ABC + Registry + Factory + Service + GeminiEmbedding. 3 skeletons. 57 tests. Metadata tracking. ReEmbeddingService ABC. |
| **Document Pipeline** (`app/document_pipeline/`) | 9/10 | 6 ABCs, 6 implementations, 5 chunkers. 11 exceptions. 88 tests. Version tracking. |
| **Vector Store** (`app/vector_store/`) | 9/10 | ABC + Registry + Factory + Service + ChromaDBStore. 3 skeletons. 94 tests. Collection lifecycle management. |
| **Retrieval Layer** (`app/retrieval/`) | 9/10 | ABC + Registry + Factory + Service + VectorRetriever. 2 skeletons. 57 tests. Patient/report/doc-type filtering. |
| **Context Builder** (`app/context/`) | 9/10 | 6-stage pipeline. 3 budget strategies. Citation generation. 67 tests. All stages independently disableable. |
| **RAG Engine** (`app/rag/`) | 8/10 | 12 files, full pipeline (process→classify→rewrite→orchestrate→gen→guardrails→citations→disclaimer). 74 tests. Query classifier (7 categories), guardrails (pre/post), citation manager (hallucination detection). |
| **Medical QA Agent** (`app/chat/`) | 8/10 | 9 files, 62 tests. Full session-based QA: ChatService, SessionManager, ConfidenceCalculator, QuestionSuggester, ResponseFormatter. No LangGraph. |
| **Evaluation & Benchmarking** (`app/evaluation/`) | 8/10 | 16 files, 190 tests. Full metric suite (retrieval, RAG, hallucination, citation, medical QA, performance, token usage). Dataset loader, ground truth, benchmark runner, report generator. |
| **Conversation Memory** | 0/10 | Not started. |
| **Medical Report Agent** | 2/10 | Skeleton nodes + state + graph defined. Prompts in Markdown. No implementation. |
| **Emergency Agent** | 2/10 | Skeleton nodes + state + graph defined. Prompts in Markdown. No implementation. |
| **Summary Agent** | 2/10 | Skeleton nodes + state + graph defined. Prompts in Markdown. No implementation. |
| **Reminder Agent** | 1/10 | Skeleton defined. No implementation. |
| **Orchestrator** | 1/10 | Skeleton defined. No implementation. |
| **Tool Calling** | 0/10 | Not started. |
| **LangGraph Runtime** | 0/10 | Not started. |
| **Multi-Agent System** | 0/10 | Not started. |

### Overall AI Readiness Score

| Category | Score | Interpretation |
|----------|-------|----------------|
| AI Infrastructure (Provider, Prompts, Embeddings, Document Pipeline) | 8.5/10 | Production-ready, test-covered, provider-independent |
| RAG Foundation (Vector Store, Retrieval, Context Builder) | 9/10 | Production-ready, comprehensive tests, provider-independent |
| AI Evaluation (Metrics, Benchmarking, Dataset, Report) | 8/10 | Comprehensive metric suite, 190 tests, independent of any component |
| AI Agents (Medical QA, RAG Engine, Chat, Medical, Emergency, Summary, Reminder) | 4.5/10 | Medical QA Agent complete (8/10); RAG Engine complete (8/10); Medical, Emergency, Summary, Reminder are skeletons |
| Integration & Orchestration (Memory, Tool Calling, LangGraph, Multi-Agent) | 0.5/10 | Not started; architecture designed but no code |
| **Overall AI Readiness** | **6.5/10** | Infrastructure is solid; RAG Engine + Medical QA Agent connect everything; Evaluation framework measures quality; agents are next |

### Readiness Heatmap

```
                  │ Not Started  Skeleton  Implemented  Production Ready
──────────────────┼────────────────────────────────────────────────────
Provider Layer    │                            ██
OCR               │       ██
Prompt System     │                                              ██
Embedding Layer   │                                              ██
Doc Pipeline      │                                              ██
Vector Store      │                                              ██
Retrieval Layer   │                                              ██
Context Builder   │                                              ██
Medical QA Agent  │                                              ██
RAG Engine        │                                              ██
Evaluation & BM   │                                              ██
Conversation Mem  │  ██
Chat Agent        │  ██
Medical Agent     │            ██
Emergency Agent   │            ██
Summary Agent     │            ██
Reminder Agent    │            ██
Orchestrator      │            ██
Tool Calling      │  ██
LangGraph Runtime │  ██
Multi-Agent       │  ██
──────────────────┼────────────────────────────────────────────────────
```

---

## 6. Dependency Graph

```
                    ┌─────────────────────────┐
                    │    Medical Prompts       │
                    │    (3 files)             │
                    └──────────┬──────────────┘
                               │
                    ┌──────────▼──────────────┐
                    │    Medical Report Agent  │
                    │    (Pending)             │
                    └──────────┬──────────────┘
                               │
                    ┌──────────▼──────────────┐
                    │    Reminder Agent        │
                    │    (Pending)             │
                    └─────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                       CORE AI INFRASTRUCTURE                      │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    Independent Layers                        │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐             │  │
│  │  │  Prompts │  │   AI     │  │  Embeddings  │             │  │
│  │  │  System  │  │ Provider │  │  (Gemini)    │             │  │
│  │  └──────────┘  └──────────┘  └──────┬───────┘             │  │
│  │                                      │                      │  │
│  │  ┌───────────────────────────────────┴──────────────────┐  │  │
│  │  │                 Document Pipeline                     │  │  │
│  │  │  Clean → Classify → Sections → Chunk → Enrich        │  │  │
│  │  └───────────────────────────────────┬──────────────────┘  │  │
│  │                                      │                      │  │
│  │  ┌───────────────────────────────────┴──────────────────┐  │  │
│  │  │                 Vector Store (ChromaDB)               │  │  │
│  │  │  Store embeddings + metadata for semantic search      │  │  │
│  │  └───────────────────────────────────┬──────────────────┘  │  │
│  │                                      │                      │  │
│  │  ┌───────────────────────────────────┴──────────────────┐  │  │
│  │  │                Retrieval Layer                        │  │  │
│  │  │  Semantic search + patient/report/document filtering   │  │  │
│  │  └───────────────────────────────────┬──────────────────┘  │  │
│  │                                      │                      │  │
│  │  ┌───────────────────────────────────┴──────────────────┐  │  │
│  │  │              Context Builder                          │  │  │
│  │  │  Dedup → Rank → Compress → Budget → Citations →      │  │  │
│  │  │  → Assemble                                           │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                     ┌──────────────────────┐
                     │    RAG Engine         │
                     │    ✅ Complete        │
                     └──────────┬───────────┘
                                │
                     ┌──────────▼───────────┐
                     │  Medical QA Agent    │
                     │    ✅ Complete        │
                     └──────────┬───────────┘
                                │
                     ┌──────────▼───────────┐
                     │  Conversation Memory  │
                     │  (Pending)            │
                     └──────────┬───────────┘
                                │
                     ┌──────────▼───────────┐
                     │    Chat Agent         │
                     │  (Pending - LangGraph)│
                    └──────────┬───────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
           ▼                   ▼                   ▼
    ┌─────────────┐   ┌────────────────┐   ┌──────────────┐
    │  Emergency  │   │   Summary     │   │   Medical    │
    │  Agent      │   │   Agent       │   │   Report     │
    │  (Pending)  │   │   (Pending)   │   │   Agent      │
    └─────────────┘   └────────────────┘   └──────────────┘
                                                │
                                                ▼
                                         ┌──────────────┐
                                         │   Reminder   │
                                         │   Agent      │
                                         │   (Pending)  │
                                         └──────────────┘
```

### Dependency Table

| Component | Depends On | Needed By |
|-----------|-----------|-----------|
| Prompt System | None | All agents |
| AI Provider | None | Embeddings, Agents |
| Embeddings | AI Provider | Document Pipeline, Retrieval |
| Document Pipeline | Embeddings | Vector Store |
| Vector Store | Embeddings, Document Pipeline | Retrieval Layer |
| Retrieval Layer | Vector Store, Embeddings | Context Builder, RAG Engine |
| Context Builder | Retrieval Layer | RAG Engine |
| RAG Engine | Retrieval, Context, AI Provider, Prompts | Medical QA Agent, Chat Agent, all agents |
| Memory Framework | None (InMemory) | Agent Framework, all agents |
| Agent Framework | Memory Framework, RAG Engine | Medical QA Agent, all future agents |
| Medical QA Agent | Agent Framework, RAG Engine | Chat Agent (future) |
| Chat Agent | Agent Framework, Memory | Emergency Agent |
| Medical Agent | Agent Framework | Reminder Agent |
| Emergency Agent | Agent Framework | Summary Agent |
| Summary Agent | Agent Framework, AI Provider | Doctor Dashboard |
| Reminder Agent | Agent Framework | Notification system |
| Appointment Agent | Agent Framework | Calendar system |
| FollowUp Agent | Agent Framework | Notification system |
| Orchestrator | All agents | API Gateway |
| Multi-Agent System | Orchestrator | All routes |
