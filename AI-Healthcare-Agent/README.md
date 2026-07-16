# AI Healthcare Follow-up Assistant

An agentic AI platform that helps hospitals monitor patients after discharge. Features AI-powered conversation with citations, medical report OCR extraction, medication adherence tracking, emergency symptom detection, appointment scheduling, and AI-generated patient summaries — all orchestrated by a LangGraph runtime with persistent memory and tool execution.

## Architecture

```
Frontend (Next.js 15 + TypeScript + Tailwind)
    │
    ├── Patient Portal (Chat, Reports, Medicines, Appointments, Emergency)
    └── Doctor Dashboard (Patient Lists, AI Summaries, Analytics)
    │
    ▼
FastAPI Backend
    │
    ├── LangGraph Runtime (Graph-based agent orchestration)
    │   ├── Graph Nodes: Memory Load → Context Builder → QA → Response Gen → Memory Persist
    │   ├── Conditional Edges: Need Retrieval, Need Tool
    │   └── Tool Executor (Appointment, Medication, Report, Patient, Doctor)
    │
    ├── AI Layer
    │   ├── RAG Engine (Retrieval-Augmented Generation w/ citations)
    │   ├── Medical Report Agent (Structured extraction from OCR text)
    │   ├── QA Agent (Medical question answering with confidence scoring)
    │   └── Guardrails (Hallucination detection, PII filtering, content safety)
    │
    ├── Data Layer
    │   ├── PostgreSQL — Primary database (patients, doctors, reports, chat history)
    │   ├── ChromaDB — Vector store for semantic search & RAG
    │   └── Memory Service — Stores conversation context, preferences, document references
    │
    └── Services
        ├── OCR Pipeline (Tesseract / Google Vision with preprocessing)
        ├── Document Pipeline (Chunking, cleaning, metadata extraction)
        ├── Embedding Service (Multi-provider: Gemini, OpenAI, Sentence Transformers)
        ├── Medical Parser (Prescriptions, lab reports, discharge summaries)
        └── Validation Framework (Benchmarking, clinical test runner, dataset management)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 15, TypeScript, Tailwind CSS, shadcn/ui, Zustand, TanStack Query, React Hook Form, Zod |
| **Backend** | FastAPI, Python 3.12+, SQLAlchemy 2.0, Alembic, Pydantic v2 |
| **AI/Orchestration** | LangGraph, LangChain, Gemini AI, GPT-4o-mini |
| **Vector Store** | ChromaDB (with Pinecone/Qdrant/Weaviate adapters) |
| **OCR** | Tesseract, Google Cloud Vision |
| **Memory** | In-memory store with Postgres/Redis adapters |
| **Database** | PostgreSQL 16 |
| **Infra** | Docker, Docker Compose, Prometheus metrics, OpenTelemetry tracing |

## Project Structure

```
AI-Healthcare-Agent/
├── frontend/                       # Next.js 15 application
│   ├── src/
│   │   ├── app/                   # App Router pages (chat, reports, medicines, appointments, emergency, dashboard)
│   │   ├── components/            # React components (ui, shared, forms)
│   │   ├── services/              # API client layer
│   │   ├── lib/                   # Zustand stores, utilities
│   │   └── types/                 # TypeScript interfaces
│   └── Dockerfile
│
├── backend/                        # FastAPI application
│   ├── app/
│   │   ├── api/v1/                # REST endpoints (auth, chat, reports, appointments, dashboard, demo)
│   │   ├── agents/                # LangGraph agent definitions & graph nodes
│   │   ├── langgraph/             # Graph runtime, state, events, metrics, bootstrap
│   │   ├── rag/                   # RAG engine, guardrails, citation management
│   │   ├── memory/                # Memory service (stores, processors, types, policies)
│   │   ├── tools/                 # Tool framework (executor, selector, registry, domain tools)
│   │   ├── services/              # Business logic layer
│   │   ├── repositories/          # Data access layer
│   │   ├── models/                # SQLAlchemy ORM models
│   │   ├── schemas/               # Pydantic request/response schemas
│   │   ├── core/                  # Config, security, logging, metrics, health
│   │   ├── middleware/            # CORS, CSRF, rate limiting, security headers, tracing
│   │   ├── ocr/                   # OCR engine, preprocessors, structured extraction
│   │   ├── document_pipeline/     # Chunking, cleaning, metadata extraction
│   │   ├── embeddings/            # Embedding providers & service
│   │   ├── retrieval/             # Retrieval service & vector/providers
│   │   ├── context/               # Context builder, citation, compressor, ranker
│   │   ├── validation/            # Benchmarking, dataset management, clinical test runner
│   │   ├── evaluation/            # Metrics, latency, hallucination, report generation
│   │   ├── prompts/               # Prompt management & caching
│   │   ├── ai/                    # AI provider abstraction layer
│   │   ├── medical_parser/        # Prescription/lab report parsing
│   │   ├── database/              # Session management, enums, query optimization
│   │   └── vector_store/          # Vector store abstraction & ChromaDB adapter
│   ├── tests/                     # 1550+ unit & integration tests
│   ├── datasets/                  # Sample medical datasets
│   ├── scripts/                   # Utility scripts (import, benchmark, demo, deployment check)
│   ├── alembic/                   # Database migrations
│   └── Dockerfile
│
├── docker/                        # Docker Compose files (dev & production)
├── scripts/                       # Setup scripts
├── docs/                          # Additional documentation
├── project_memory/                # Session notes, status tracking
└── .github/                       # CI/CD workflows
```

## Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose (optional, for PostgreSQL)
- OpenAI API key
- Google Cloud Vision API key (optional, for OCR)

## Quick Start

### 1. Clone and setup

```bash
# PowerShell (Windows)
.\scripts\setup.ps1

# OR manually:
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
cd ../frontend
npm install
```

### 2. Configure environment

```bash
# Backend
cp backend/.env.example backend/.env

# Frontend
cp frontend/.env.local.example frontend/.env.local
```

Edit the `.env` files with your credentials (OpenAI API key, database URL, etc.)

### 3. Start services with Docker

```bash
docker compose -f docker/docker-compose.yml up -d
```

This starts:
- PostgreSQL on port 5432
- ChromaDB on port 8001
- Backend API on port 8000
- Frontend on port 3000

### 4. Run database migrations

```bash
cd backend
alembic upgrade head
```

### 5. Start development servers

```bash
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

Visit `http://localhost:3000` for the frontend and `http://localhost:8000/docs` for the API documentation.

## API Documentation

Once the backend is running:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/health`

## Testing

```bash
# Backend tests
cd backend
pytest -v --cov=app

# Frontend tests
cd frontend
npm run test:run
```

## Development Status

MVP architecture is complete. Current progress: ~99% with 9.2/10 system health.

### Completed Modules

| Module | Status | Tests |
|--------|--------|-------|
| Authentication (JWT + refresh tokens) | ✅ | 25+ |
| OCR Pipeline (Tesseract + Google Vision) | ✅ | 30+ |
| Medical Parser (prescriptions, lab reports) | ✅ | 15+ |
| Prompt Management & Caching | ✅ | 15+ |
| Embedding Service (multi-provider) | ✅ | 20+ |
| Document Pipeline (chunking, cleaning) | ✅ | 25+ |
| Vector Store (ChromaDB + adapters) | ✅ | 20+ |
| Retrieval Service | ✅ | 20+ |
| Context Builder (citation, compression) | ✅ | 25+ |
| RAG Engine (guardrails, confidence) | ✅ | 30+ |
| Medical QA Agent | ✅ | 25+ |
| Evaluation Framework (metrics, benchmarks) | ✅ | 100+ |
| Memory Framework (stores, policies) | ✅ | 60+ |
| Agent Framework (factory, registry, executor) | ✅ | 60+ |
| Tool Framework (selector, executor, 5 domain tools) | ✅ | 60+ |
| LangGraph Runtime (graph nodes, edges, state, events) | ✅ | 80+ |
| Validation Framework (datasets, clinical tests) | ✅ | 110+ |
| Observability (logging, metrics, monitoring) | ✅ | 20+ |
| Security (rate limiting, CSRF, headers, audit) | ✅ | 15+ |
| Demo Mode & Demo Scenarios | ✅ | - |
| Frontend UI (chat, reports, medicines) | ✅ | - |
| Deployment (Docker Compose, guide, readiness) | ✅ | - |

### Next Phase

Clinical validation, production hardening, real-world deployment with partner hospitals.

## License

MIT
