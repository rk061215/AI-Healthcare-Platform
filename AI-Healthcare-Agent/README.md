# AI Healthcare Platform

**Intelligent post-discharge patient monitoring with AI-powered conversation, medical document analysis, and multi-agent orchestration.**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-000000?logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?logo=typescript&logoColor=white)](https://typescriptlang.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-1C3C3C?logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?logo=opensourceinitiative&logoColor=white)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-1100%2B-brightgreen)](#testing)
[![Status](https://img.shields.io/badge/Status-MVP%20Complete-success)](https://github.com/rk061215/AI-Healthcare-Platform)
[![Code style: black](https://img.shields.io/badge/Code%20Style-Black-000000)](https://github.com/psf/black)

---

<p align="center">
  <img src="assets/architecture.png" alt="AI Healthcare Platform Architecture" width="800">
  <br>
  <em>High-level system architecture — Frontend (Next.js) → Backend (FastAPI) → AI Layer (LangGraph + RAG) → Data Layer (PostgreSQL + ChromaDB)</em>
</p>

## Features

### AI-Powered Medical Document Analysis
- Upload prescriptions, lab reports, and discharge summaries (PDF / image)
- OCR extraction with structured medicine data (name, dosage, frequency, duration)
- Medical report parsing with confidence scoring and validation
- Semantic search across all uploaded documents

### Intelligent Conversational Agent
- RAG-powered medical Q&A over patient documents
- Inline citations with source document references
- Confidence scoring per response
- Suggested follow-up questions for guided conversations
- Multi-turn conversation with context retention

### Multi-Agent Orchestration (LangGraph)
- 6-node LangGraph runtime: Memory Load → Context Builder → QA → Response Generator → Tool Executor → Memory Persist
- Conditional routing with intelligent edge decisions
- Tool calling framework with 5 domain-specific tools
- Persistent memory for conversation, preferences, and document context

### Clinical Validation Framework
- 9 real medical document datasets with authentic clinical data
- Benchmark suite with 12 metrics (retrieval recall, precision@K, MRR, NDCG, citation P/R/F1, groundedness, hallucination rate, answer relevance)
- Dataset management with train/val/test splitting
- Regression testing with automated quality gates
- Optimization grid search (chunking, retrieval, reranking, prompt variants)

### Doctor & Patient Dashboards
- **Patient Portal**: Chat, reports, medicines, appointments, emergency triage
- **Doctor Dashboard**: Patient lists, AI summaries, adherence analytics, alert management
- Role-based access control with JWT authentication

### Production-Grade Infrastructure
- Structured logging with request correlation IDs
- Prometheus-format metrics endpoint
- Rate limiting, CSRF protection, security headers
- Docker Compose for dev and production
- OpenTelemetry tracing support

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 15, TypeScript, Tailwind CSS, shadcn/ui | Modern React SPA with App Router |
| **State** | Zustand, TanStack Query | Client + server state management |
| **Backend** | FastAPI, Python 3.12, Pydantic v2 | High-performance async API |
| **Database** | PostgreSQL 16, SQLAlchemy 2.0, Alembic | Relational data storage & migrations |
| **AI Orchestration** | LangGraph 0.2, LangChain | Graph-based agent workflow |
| **AI Providers** | Gemini 1.5 Pro, GPT-4o-mini (future) | LLM inference |
| **Vector Store** | ChromaDB (Pinecone/Qdrant/Weaviate adapters) | Semantic search for RAG |
| **Embeddings** | Gemini Embedding (OpenAI/Sentence Transformers future) | Document vectorization |
| **OCR** | Tesseract, Google Cloud Vision | Document text extraction |
| **Memory** | In-memory (Redis/Postgres adapters) | Conversation & context persistence |
| **Observability** | Prometheus, OpenTelemetry, Loguru | Metrics, tracing, structured logging |
| **Infrastructure** | Docker, Docker Compose, Nginx | Containerization & reverse proxy |

## Architecture

### System Layers

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                     │
│  Patient Portal: Chat │ Reports │ Medicines │ Emergency  │
│  Doctor Dashboard: Patients │ Summaries │ Alerts        │
│  Demo Mode: Guided Walkthrough │ Scenario Selector     │
└──────────────────────┬──────────────────────────────────┘
                       │ REST API (HTTP/JSON)
┌──────────────────────▼──────────────────────────────────┐
│                    BACKEND (FastAPI)                      │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              LangGraph Runtime                     │   │
│  │  [Memory Load] → [Context Builder] → [QA Node]   │   │
│  │       ↕                              ↕            │   │
│  │  [Tool Executor] ← [Tool Selector]  [Retriever]  │   │
│  │       ↕                                           │   │
│  │  [Memory Persist]                                 │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────┐  ┌────────────┐  ┌────────────────┐  │
│  │  RAG Engine   │  │   Tools    │  │  Validation    │  │
│  │  · Retrieval  │  │Appointment │  │  · Benchmarks  │  │
│  │  · Guardrails │  │Medication  │  │  · Metrics     │  │
│  │  · Citations  │  │ Report     │  │  · Optimizers  │  │
│  │  · Confidence │  │ Patient    │  │  · Test Runner │  │
│  └──────────────┘  │ Doctor     │  └────────────────┘  │
│                    └────────────┘                       │
│  ┌──────────────┐  ┌────────────┐  ┌────────────────┐  │
│  │ Document      │  │  Memory    │  │  Security      │  │
│  │ Pipeline      │  │  Service   │  │  · Rate Limit  │  │
│  │  · Chunking   │  │  · Types   │  │  · CSRF        │  │
│  │  · Embedding  │  │  · Policies│  │  · Headers     │  │
│  │  · Storage    │  │  · Process │  │  · Validation  │  │
│  └──────────────┘  └────────────┘  └────────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                    DATA LAYER                            │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────┐  │
│  │ PostgreSQL  │  │  ChromaDB  │  │  File Storage    │  │
│  │ · Users     │  │ · Vectors  │  │ · Documents     │  │
│  │ · Reports   │  │ · Metadata │  │ · Uploads       │  │
│  │ · Appts     │  │            │  │ · Reports       │  │
│  │ · Chat      │  │            │  │                  │  │
│  └────────────┘  └────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### LangGraph Pipeline

The core AI workflow is orchestrated by a LangGraph state machine:

| Node | Description |
|------|-------------|
| **Load Memory** | Retrieves conversation history, patient context, and preferences |
| **Context Builder** | Compresses, deduplicates, ranks, and budgets retrieved context |
| **Medical QA** | LLM-powered question answering with medical domain knowledge |
| **Retriever** | Semantic search over vector store for relevant documents |
| **Tool Executor** | Executes domain tools (appointments, medications, reports, etc.) |
| **Response Generator** | Formats final response with citations and confidence scores |
| **Persist Memory** | Stores conversation turns and extracted context |

Edges are conditionally routed based on query intent, retrieval necessity, and tool requirements.

## Project Structure

```
AI-Healthcare-Agent/
├── frontend/                          # Next.js 15 SPA
│   ├── src/
│   │   ├── app/                       # App Router pages
│   │   │   ├── patient/               # Patient portal
│   │   │   │   ├── chat/              # AI conversation
│   │   │   │   ├── reports/           # Medical document management
│   │   │   │   ├── medicines/         # Medication adherence
│   │   │   │   ├── appointments/      # Visit scheduling
│   │   │   │   └── emergency/         # Symptom triage
│   │   │   ├── doctor/                # Doctor dashboard
│   │   │   │   ├── dashboard/         # Patient overview
│   │   │   │   ├── patients/          # Patient management
│   │   │   │   └── alerts/            # Emergency alerts
│   │   │   └── (auth)/                # Login, register, demo
│   │   ├── components/                # Shared UI components
│   │   └── services/                  # API client layer
│   ├── Dockerfile
│   └── package.json
│
├── backend/                           # FastAPI application
│   ├── app/
│   │   ├── api/v1/                    # 12 REST endpoint modules
│   │   ├── langgraph/                 # Graph runtime, state, events
│   │   ├── agents/                    # Agent definitions & nodes
│   │   ├── rag/                       # RAG engine, guardrails
│   │   ├── memory/                    # Memory service & stores
│   │   ├── tools/                     # Tool framework & domain tools
│   │   ├── services/                  # Business logic (16 services)
│   │   ├── repositories/              # Data access layer
│   │   ├── models/                    # SQLAlchemy ORM models
│   │   ├── schemas/                   # Pydantic schemas
│   │   ├── ocr/                       # OCR engine & providers
│   │   ├── document_pipeline/         # Document processing
│   │   ├── embeddings/                # Embedding providers
│   │   ├── retrieval/                 # Retrieval service
│   │   ├── context/                   # Context builder
│   │   ├── validation/                # Benchmarks & datasets
│   │   ├── evaluation/                # Metrics & reporting
│   │   ├── core/                      # Config, security, logging
│   │   ├── middleware/                # CORS, CSRF, rate limiting
│   │   ├── ai/                        # AI provider abstraction
│   │   ├── medical_parser/            # Medical text parsing
│   │   ├── prompts/                   # Prompt management
│   │   ├── database/                  # DB session & queries
│   │   ├── vector_store/              # Vector store abstraction
│   │   ├── chat/                      # Chat service
│   │   └── tasks/                     # Background tasks
│   ├── tests/                         # 1100+ tests
│   ├── datasets/                      # 9 medical datasets
│   └── scripts/                       # Utility scripts
│
├── docker/                            # Docker Compose files
├── docs/                              # Documentation
├── assets/                            # Screenshots & media
├── scripts/                           # Setup & migration scripts
├── .github/                           # CI/CD & templates
├── project_memory/                    # Development tracking
│
├── ARCHITECTURE.md                    # Detailed architecture
├── CHANGELOG.md                       # Version history
├── CONTRIBUTING.md                    # Contribution guide
├── SECURITY.md                        # Security policy
├── CODE_OF_CONDUCT.md                 # Code of conduct
├── ROADMAP.md                         # Future plans
├── SUPPORT.md                         # Support information
└── .env.example                       # Environment template
```

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose (optional, for PostgreSQL)
- Gemini API key (or OpenAI API key)

### Installation

```bash
# Clone the repository
git clone https://github.com/rk061215/AI-Healthcare-Platform.git
cd AI-Healthcare-Platform

# Run setup script (PowerShell)
.\scripts\setup.ps1

# Or set up manually:

# Backend
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### Configuration

```bash
# Backend environment
cp backend/.env.example backend/.env

# Frontend environment
cp frontend/.env.local.example frontend/.env.local
```

Edit `.env` files with your credentials:

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes (or OpenAI key) |
| `JWT_SECRET_KEY` | JWT signing secret | Yes |
| `POSTGRES_*` | Database configuration | Yes |
| `OPENAI_API_KEY` | OpenAI API key (optional) | For GPT models |

### Running with Docker

```bash
docker compose -f docker/docker-compose.yml up -d
```

This starts: PostgreSQL, ChromaDB, Backend (port 8000), Frontend (port 3000).

### Running Manually

```bash
# Terminal 1: Backend
cd backend
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000) for the app and [http://localhost:8000/docs](http://localhost:8000/docs) for API docs.

### Demo Mode

Try the platform without creating an account:

```bash
# Seed demo data
curl -X POST http://localhost:8000/api/demo/seed

# Login as demo patient
curl -X POST http://localhost:8000/api/demo/login
```

Or click **"Try Demo"** on the login page.

## Testing

```bash
# Backend — all tests
cd backend
pytest -v --cov=app

# Specific test suite
pytest -v tests/test_langgraph/
pytest -v tests/test_rag/
pytest -v tests/test_validation/

# Frontend
cd frontend
npm run test:run
```

**Test Coverage:** 1100+ unit and integration tests across 26 test modules.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/auth/*` | Register, login, refresh, logout |
| `GET /api/v1/patients/me` | Patient profile |
| `GET /api/v1/dashboard` | Patient dashboard stats |
| `POST /api/v1/chat` | AI conversation |
| `POST /api/v1/reports/upload` | Upload medical document |
| `GET /api/v1/reports` | List patient reports |
| `GET /api/v1/medicines` | Patient medicines & adherence |
| `GET /api/v1/appointments` | Patient appointments |
| `GET /api/v1/doctor-dashboard` | Doctor overview |
| `POST /api/v1/demo/*` | Demo mode endpoints |
| `GET /health` | Health check |
| `GET /metrics` | Prometheus metrics |

## Project Statistics

| Metric | Value |
|--------|-------|
| **Python Backend** | 26,267 lines of code |
| **Frontend (TSX)** | 3,445 lines of code |
| **TypeScript Services** | 586 lines of code |
| **Backend Modules** | 28 Python packages |
| **Unit/Integration Tests** | 1100+ (111 test files) |
| **API Endpoints** | 12 route modules |
| **Documentation** | 20+ Markdown files |
| **Architecture Layers** | 6 (Frontend, API, LangGraph, AI, Data, Infra) |
| **LangGraph Nodes** | 7 graph nodes |
| **Supported Document Types** | 9 (Prescription, CBC, Lipid, Thyroid, KFT, LFT, Diabetes, Radiology, Discharge) |
| **AI Providers** | 2 implemented (Gemini, OpenAI) + 3 future |
| **OCR Providers** | 2 (Tesseract, Google Vision) |
| **Vector Stores** | 1 implemented (ChromaDB) + 3 adapters |
| **Retrievers** | 1 implemented (Vector) + 2 future |
| **Docker Services** | 5 (PostgreSQL, ChromaDB, Backend, Frontend, Redis) |
| **Monitoring** | Prometheus, OpenTelemetry, Loguru, Sentry |

## Screenshots

<p align="center">
  <em>Screenshots coming soon — see <a href="assets/README.md">assets/README.md</a> for capture instructions.</em>
</p>

<!--
## Screenshots

| | | |
|---|---|---|
| <img src="assets/dashboard-patient.png" width="250"> | <img src="assets/chat-interface.png" width="250"> | <img src="assets/report-upload.png" width="250">
| <b>Patient Dashboard</b> | <b>AI Chat</b> | <b>Report Upload</b>
| <img src="assets/medicines-grid.png" width="250"> | <img src="assets/dashboard-doctor.png" width="250"> | <img src="assets/demo-mode.png" width="250">
| <b>Medicine Adherence</b> | <b>Doctor Dashboard</b> | <b>Demo Mode</b>
-->

## Known Limitations

- **In-memory memory store** — Conversation memory uses in-memory storage; production deployments should enable Redis or Postgres adapters
- **Future providers** — OpenAI, Anthropic, and local (Ollama/vLLM) AI providers are scaffolded but not yet wired
- **OCR in development** — Tesseract and Google Vision adapters exist; production OCR pipeline needs API key configuration
- **Mobile responsive** — UI is desktop-first; mobile optimization is planned
- **Multi-tenancy** — Hospital-level isolation is not yet implemented (single-tenant MVP)
- **HIPAA compliance** — Security model follows best practices but has not undergone formal HIPAA audit

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Author

**Ronak Kumar Sahu** — [@rk061215](https://github.com/rk061215)

Project Link: [https://github.com/rk061215/AI-Healthcare-Platform](https://github.com/rk061215/AI-Healthcare-Platform)

## Acknowledgements

- [LangGraph](https://langchain-ai.github.io/langgraph/) — Agent orchestration framework
- [FastAPI](https://fastapi.tiangolo.com/) — Backend framework
- [Next.js](https://nextjs.org/) — React framework
- [shadcn/ui](https://ui.shadcn.com/) — UI component library
- [ChromaDB](https://www.trychroma.com/) — Vector database
- [Google Gemini](https://deepmind.google/technologies/gemini/) — AI provider
