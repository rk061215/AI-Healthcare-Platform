# AI Healthcare Follow-up Assistant — Project Overview

**Version:** 0.19.0
**Last Updated:** 2026-07-16
**Status:** MVP Complete — Production-Ready

---

## Vision

To build an intelligent, agentic AI platform that transforms post-discharge patient care by automating medication tracking, follow-up compliance, symptom triage, and doctor-patient communication — reducing hospital readmission rates and improving patient outcomes through proactive AI-driven monitoring.

## Problem Statement

Patients discharged from hospitals face several challenges:

1. **Medication non-adherence** — Up to 50% of patients do not take medications as prescribed after discharge.
2. **Missed follow-ups** — Patients forget or ignore scheduled follow-up appointments.
3. **Prescription confusion** — Complex medication schedules and medical terminology confuse patients.
4. **Delayed emergency response** — Patients cannot differentiate between normal side effects and emergency symptoms.
5. **Doctor information gaps** — Doctors lack visibility into patient adherence and symptoms between visits.

Hospitals need an automated system that bridges the gap between discharge and recovery.

## Objectives

- Build a production-ready SaaS platform for post-discharge patient monitoring
- Implement 5 AI agents using LangGraph for automated medical reasoning
- Provide real-time medicine reminders and adherence tracking
- Detect emergency symptoms and classify urgency (LOW / MEDIUM / HIGH)
- Generate AI-powered patient summaries for doctors
- Support RAG-based patient chat over uploaded medical reports
- Achieve clean architecture with SOLID principles throughout
- Enable dark mode, responsive design, and professional SaaS UI

## Target Users

- **Primary:** Hospitals and clinics seeking to improve post-discharge outcomes
- **Secondary:** Individual patients managing chronic conditions at home
- **Tertiary:** Independent doctors monitoring their patients between visits

## User Roles

### Patient
- Register and login to the platform
- Upload prescriptions and medical reports (PDF / Image)
- View extracted medicines with dosage, frequency, and instructions
- Chat with AI assistant about medications and health concerns
- Receive medicine reminders (in-app)
- View medicine adherence history and statistics
- View upcoming and past appointments
- Check symptoms for urgency classification
- View uploaded reports and extracted data

### Doctor
- Login to the platform
- View assigned patients list
- View AI-generated patient summaries
- Review patient medicine adherence data
- Review uploaded patient reports
- View and acknowledge emergency alerts
- Manage appointments

### Admin (Future)
- Manage users (patients and doctors)
- View system-wide analytics
- Configure system settings
- Manage roles and permissions
- Monitor AI agent performance

## Core Features

| Feature | Status | Description |
|---------|--------|-------------|
| Authentication | ✅ Complete | JWT auth, register, login, logout, refresh, role-based access |
| Patient Dashboard | ✅ Complete | Stats, schedule, alerts, quick actions |
| Doctor Dashboard | ✅ Complete | Patient stats, pending alerts, adherence overview |
| Prompt Management | ✅ Complete | 18 versioned prompts, caching, registry (Phase A) |
| Embedding Layer | ✅ Complete | Provider-independent Gemini embeddings (Phase B) |
| Document Pipeline | ✅ Complete | Clean → classify → sections → 5 chunkers → enrich (Phase B) |
| Vector Store | ✅ Complete | ChromaDB, provider-independent (Phase C) |
| Retrieval Layer | ✅ Complete | Semantic search, patient/report/doc-type filtering (Phase D) |
| Context Builder | ✅ Complete | Dedup → rank → compress → budget → citations → assemble (Phase D) |
| RAG Engine | ✅ Complete | Context → LLM orchestration with citations + guardrails (Phase E) |
| Medical QA Agent | ✅ Complete | Session-based Q&A over medical documents (Phase F) |
| Conversation Memory | ⏳ Pending | Chat history management, session windowing |
| Medical Report Agent | ⏳ Pending | LangGraph extraction pipeline |
| Patient Chat Agent (LangGraph) | ⏳ Pending | LangGraph-powered Q&A with memory |
| Medicine Reminder Agent | ⏳ Pending | Schedule generation, adherence tracking |
| Emergency Detection Agent | ⏳ Pending | Symptom triage, alert management |
| Doctor Summary Agent | ⏳ Pending | AI patient summaries |
| OCR Processing | 🔄 Skeleton | Google Vision + Tesseract fallback |
| Appointments | 🔄 Skeleton | Create, manage, view appointments |

## Why Provider Abstraction Exists

Every AI infrastructure layer (AI providers, embeddings, vector store, retrieval) follows the same architecture:

```
BaseABC → Registry → Factory → Provider → Service
```

This exists because:
1. **No vendor lock-in** — Switch Gemini ↔ OpenAI ↔ local models by changing config, not code
2. **Free-tier first** — Start with free APIs (Gemini, ChromaDB), upgrade when needed
3. **Testability** — Mock providers enable deterministic unit tests without API calls
4. **Future-proof** — Add new providers without touching existing code
5. **Consistency** — Every layer follows the same pattern, reducing cognitive overhead

## Why Vector Database Abstraction Exists

The `BaseVectorStore` ABC abstracts ChromaDB (active), Qdrant, Weaviate, and Pinecone because:

1. **ChromaDB is free and self-hosted** — Perfect for MVP; runs in Docker alongside the app
2. **Migration path** — When scale demands it, switch to Qdrant (self-hosted) or Pinecone (managed)
3. **Test isolation** — In-memory mock stores for testing without ChromaDB running
4. **Future pgvector** — PostgreSQL-native vectors eliminate a separate infrastructure dependency

## Why Context Builder Exists

The Context Builder (`app/context/`) is a separate layer independent of any LLM because:

1. **Token budget management** — LLM context windows are limited; intelligent compression is essential for quality
2. **Citation accuracy** — Source attribution must happen before the LLM sees the text to prevent hallucinated citations
3. **Retrieval quality** — Deduplication, ranking, and compression improve LLM output quality regardless of the model
4. **Reusability** — The same context pipeline serves Chat Agent, Summary Agent, and any future LLM consumer
5. **Testability** — Pure data transformations are easy to test without LLM calls or stochastic results

## Technology Stack

### Frontend

| Dependency | Version | Purpose |
|-----------|---------|---------|
| Next.js | 15.1+ | React framework with App Router |
| React | 19.0+ | UI library |
| TypeScript | 5.7+ | Type safety |
| Tailwind CSS | 3.4+ | Utility-first CSS |
| shadcn/ui | latest | Component primitives |
| Zustand | 5.0+ | State management |
| TanStack Query | 5.62+ | Server state management |
| React Hook Form | 7.54+ | Form handling |
| Zod | 3.24+ | Schema validation |
| Axios | 1.7+ | HTTP client |
| Recharts | 2.15+ | Charts and graphs |
| Lucide React | 0.460+ | Icons |
| date-fns | 4.1+ | Date utilities |
| Sonner | 1.7+ | Toast notifications |
| next-themes | 0.4+ | Dark mode |

### Backend

| Dependency | Version | Purpose |
|-----------|---------|---------|
| Python | 3.12+ | Runtime |
| FastAPI | 0.115+ | Web framework |
| Uvicorn | 0.34+ | ASGI server |
| SQLAlchemy | 2.0+ | ORM |
| Alembic | 1.14+ | Migrations |
| Pydantic | 2.10+ | Data validation |
| Pydantic Settings | 2.7+ | Configuration |
| psycopg2-binary | 2.9+ | PostgreSQL driver |
| asyncpg | 0.30+ | Async PostgreSQL driver |
| python-jose | 3.3+ | JWT tokens |
| passlib | 1.7+ | Password hashing |
| bcrypt | 4.2+ | Cryptography |

### AI / ML

| Dependency | Version | Purpose |
|-----------|---------|---------|
| LangGraph | 0.2+ | Agent orchestration (planned) |
| LangChain | 0.3+ | LLM framework (planned usage) |
| google.generativeai | latest | Gemini API (embeddings + LLM) |
| ChromaDB | 0.5+ | Vector store |
| Tesseract OCR | latest | Local OCR fallback |
| Pillow | latest | Image processing |

### Infrastructure

| Tool | Purpose |
|------|---------|
| Docker | Containerization |
| Docker Compose | Multi-service orchestration |
| Vercel | Frontend hosting (planned) |
| Render | Backend hosting (planned) |
| Neon | Managed PostgreSQL (planned) |
| GitHub Actions | CI/CD |

## Current Architecture

```
                    ┌──────────────────────────────────────────────┐
                    │              CLIENT LAYER                     │
                    │  Next.js Frontend (Port 3000)                 │
                    │  Auth pages, Patient UI, Doctor UI            │
                    └──────────────────┬───────────────────────────┘
                                       │ HTTP/JSON + Bearer Token
                                       ▼
                    ┌──────────────────────────────────────────────┐
                    │              API GATEWAY                      │
                    │  FastAPI (Port 8000)                          │
                    │  Middleware → Routes → Services → Repos      │
                    └──────────────────┬───────────────────────────┘
                                       │
                    ┌──────────────────┴───────────────────────────┐
                    │           AI / RAG LAYER                      │
                    │                                              │
                    │  ┌────────────────────────────────────────┐  │
                    │  │    Document Ingestion Pipeline          │  │
                    │  │    Upload → OCR → Clean → Classify →    │  │
                    │  │    Sections → Chunk → Enrich → Embed    │  │
                    │  └────────────────────────────────────────┘  │
                    │  ┌────────────────────────────────────────┐  │
                    │  │    Retrieval Layer (VectorRetriever)    │  │
                    │  │    Query → Embed → Vector Search → Filter│  │
                    │  └────────────────────────────────────────┘  │
                    │  ┌────────────────────────────────────────┐  │
                    │  │    Context Builder                     │  │
                    │  │    Dedup → Rank → Compress → Budget    │  │
                    │  │    → Citations → Assemble              │  │
                    │  └────────────────────────────────────────┘  │
                    │  ┌────────────────────────────────────────┐  │
                    │  │    RAG Engine + Medical QA Agent       │  │
│  │    (✅ Complete)                       │  │
                    │  └────────────────────────────────────────┘  │
                    └──────────────────┬───────────────────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────┐
        │                              │                          │
        ▼                              ▼                          ▼
┌──────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│   PostgreSQL     │  │      ChromaDB        │  │  Google Vision OCR   │
│   (Port 5432)    │  │   (Vector DB, 8001)  │  │  + Tesseract         │
│   Relational     │  │   Embeddings +       │  │                      │
│   data, users,   │  │   metadata for       │  │  Image → Text        │
│   medical records│  │   semantic search    │  │  extraction          │
└──────────────────┘  └──────────────────────┘  └──────────────────────┘
```

## Architecture Rules

Every AI infrastructure layer follows these rules:

1. **ABC → Registry → Factory → Provider → Service** pattern throughout
2. **Provider-independent** — switching providers requires config change, not code change
3. **Constructor injection** — all dependencies injected, never created internally
4. **No LLM coupling** — pre-LLM layers (retrieval, context builder) are pure data transformations
5. **Config-driven** — behavior controlled by dataclass config objects, not hardcoded constants
6. **Testable in isolation** — mock providers for deterministic unit tests
7. **Future provider skeletons** — `NotImplementedError` for planned but unbuilt providers
8. **Free-tier first** — all dependencies are free/open-source; no paid subscriptions

## Folder Structure

```
AI-Healthcare-Agent/
├── frontend/                          # Next.js 15 Application
├── backend/                           # FastAPI Application
│   ├── app/
│   │   ├── api/v1/                    # Route handlers
│   │   ├── core/                      # Config, security, logging
│   │   ├── database/                  # DB engine, session, base
│   │   ├── models/                    # SQLAlchemy models (10 tables)
│   │   ├── schemas/                   # Pydantic schemas
│   │   ├── repositories/              # Data access layer (10 repos)
│   │   ├── services/                  # Business logic (10 services)
│   │   ├── ai/                        # AI Provider Layer (ABC → Registry → Factory → Service → Providers)
│   │   ├── prompts/                   # Prompt Management System (cache, loader, manager)
│   │   ├── embeddings/                # Embedding Layer (ABC → Registry → Factory → Service → Providers)
│   │   ├── document_pipeline/         # Document Processing Pipeline (clean, chunk, classify, etc.)
│   │   ├── vector_store/              # Vector Store Layer (ABC → Registry → Factory → Service → Providers)
│   │   ├── retrieval/                 # Retrieval Layer (ABC → Registry → Factory → Service → Providers)
│   │   ├── context/                   # Context Builder (dedup → rank → compress → budget → citations → assemble)
│   │   ├── agents/                    # LangGraph agents (skeletons)
│   │   ├── langgraph/                 # Shared graph components (empty)
│   │   ├── middleware/                # CORS, error handlers
│   │   ├── ocr/                       # OCR abstraction (skeleton)
│   │   ├── rag/                       # Legacy RAG module (deprecated)
│   │   ├── medical_parser/            # Medical extraction (frozen at MVP)
│   │   └── utils/                     # Utility functions
│   ├── tests/
│   │   ├── test_retrieval/            # 57 tests — retrieval layer
│   │   ├── test_context/              # 67 tests — context builder
│   │   ├── test_vector_store/         # 94 tests — vector store
│   │   ├── test_document_pipeline/    # 88 tests — document pipeline
│   │   ├── test_embeddings/           # 57 tests — embedding layer
│   │   ├── test_prompts/              # 38 tests — prompt management
│   │   └── ...                        # 95 other tests
│   ├── prompts/                       # 18 Markdown prompt files
│   └── alembic/                       # DB migrations
├── docker/                            # Docker Compose files
├── project_memory/                    # Persistent project memory
└── docs/                              # Documentation
```

## Development Roadmap

### Current Status (v0.14.0)

**RAG + Memory + Agent Framework Complete:**
- ✅ Prompt Management System (Phase A)
- ✅ Provider-Independent Embedding Layer (Phase B)
- ✅ Document Processing Pipeline (Phase B)
- ✅ Vector Store Layer (Phase C)
- ✅ Retrieval Layer (Phase D)
- ✅ Context Builder (Phase D)
- ✅ RAG Engine (Phase E)
- ✅ Medical QA Agent (Phase F)
- ✅ AI Evaluation & Benchmarking (Phase G)
- ✅ Memory Framework (Phase H) — 5 types, 4 processors, 3 policies, 133 tests
- ✅ Agent Framework (Phase I) — BaseAgent, Registry, Factory, Executor, Service, 22 files, 76 tests
- ✅ Tool Calling Framework (Phase J) — BaseTool, Registry, Factory, Executor, Selector, Service, 5 domain tools + 4 skeletons, 28 files, 116 tests

**Next Up:** LangGraph Runtime

### Phase Breakdown

| Phase | Module | Status |
|-------|--------|--------|
| 1 | Foundation (FastAPI, Next.js, Docker, CI/CD) | ✅ Complete |
| 2 | Authentication (JWT, Register, Login, RBAC) | ✅ Complete |
| 3 | Production Hardening (Rate Limit, CSRF, Migrations) | ✅ Complete |
| A | Prompt Management System | ✅ Complete |
| B | Embedding Layer + Document Pipeline | ✅ Complete |
| C | Vector Store (ChromaDB) | ✅ Complete |
| D | Retrieval Layer + Context Builder | ✅ Complete |
| E | RAG Engine (Context → LLM) | ✅ Complete |
| F | Medical QA Agent (Session-based QA) | ✅ Complete |
| G | AI Evaluation & Benchmarking | ✅ Complete |
| H | Memory Framework | ✅ Complete |
| I | Agent Framework | ✅ Complete |
| J | Tool Calling Framework | ✅ Complete |
| K | LangGraph Runtime | ⏳ Pending |
| 4 | Medical Report Agent | ⏳ Pending |
| 5 | Patient Chat Agent (LangGraph) | ⏳ Pending |
| 6 | Medicine Reminder Agent | ⏳ Pending |
| 7 | Emergency Detection Agent | ⏳ Pending |
| 8 | Doctor Summary Agent + Orchestrator | ⏳ Pending |
| 9 | Deployment (Docker, CI/CD, Cloud Hosting) | ⏳ Pending |
| 10 | Admin Dashboard & Analytics | ⏳ Future |

## AI Agent Overview

| Agent/Component | LangGraph Nodes | Purpose | Status |
|----------------|----------------|---------|--------|
| Tool Calling Framework | N/A (standalone) | 5 domain tools wrapping backend services | ✅ Complete |
| Medical QA Agent | (Refactored into Agent Framework) | Session-based Q&A over medical documents | ✅ Complete |
| Medical Report Agent | extract_entities → validate → store | Extract structured data from prescriptions | ⏳ Pending |
| Patient Chat Agent | retrieve_context → compress → generate | Answer patient questions using RAG | ⏳ Pending |
| Reminder Agent | check_schedule → generate → track | Generate and track medicine reminders | ⏳ Pending |
| Emergency Agent | analyze → classify → recommend | Triage symptom urgency | ⏳ Pending |
| Summary Agent | aggregate_data → generate_summary | Generate clinical summaries for doctors | ⏳ Pending |

## Deployment Plan

1. Containerize all services with Docker (multi-stage builds)
2. Deploy frontend to Vercel
3. Deploy backend to Render (or Railway)
4. Use Neon for managed PostgreSQL
5. GitHub Actions for CI/CD (lint → test → build → deploy)
6. Environment-based configuration via `.env` files
7. Health monitoring endpoints
8. Performance optimization before production launch

## Coding Standards

### Naming Conventions
| Category | Convention | Example |
|----------|-----------|---------|
| Python files | snake_case | `vector_retriever.py` |
| Python classes | PascalCase | `VectorRetriever` |
| Python functions | snake_case | `search_by_patient` |
| TypeScript files | kebab-case | `auth-store.ts` |
| React components | PascalCase | `LoginForm` |
| Database tables | snake_case | `refresh_tokens` |
| API endpoints | kebab-case | `/register/patient` |

### Architecture Rules
1. API Layer validates, routes to services — never contains business logic
2. Service Layer orchestrates operations — never handles HTTP
3. Repository Layer handles data access — never contains business logic
4. AI Infrastructure Layer (ABC → Registry → Factory → Provider → Service) — always provider-independent
5. Pre-LLM layers (retrieval, context builder) are pure data transformations — no LLM coupling
6. Type annotations required on all Python functions and TypeScript interfaces
7. Error handling via custom exception hierarchy

## Design Principles

- **Minimalist** — Less is more. Every element serves a purpose.
- **Consistent** — Reuse components, spacings, and patterns.
- **Accessible** — WCAG 2.1 AA minimum contrast ratios.
- **Responsive** — Mobile-first, adapts from 320px to 4K.
- **Feedback-rich** — Loading states, toasts, confirmations.
- **Error-tolerant** — Clear messages, form validation, recovery paths.
- **Dark mode** — Full CSS variable-based theming with system preference detection.
- **Free-tier first** — All dependencies are free/open-source; no paid subscriptions.
- **Provider-independent** — Every AI layer supports multiple providers via config.
