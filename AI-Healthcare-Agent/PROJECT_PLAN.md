# AI Healthcare Follow-up Assistant — Project Plan

**Version:** 0.2.0
**Last Updated:** 2026-07-11
**Status:** Phase 2 — Authentication Production Complete

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

## Goals

- Build a production-ready SaaS platform for post-discharge patient monitoring
- Implement 5 AI agents using LangGraph for automated medical reasoning
- Provide real-time medicine reminders and adherence tracking
- Detect emergency symptoms and classify urgency (LOW / MEDIUM / HIGH)
- Generate AI-powered patient summaries for doctors
- Support RAG-based patient chat over uploaded medical reports
- Achieve clean architecture with SOLID principles throughout
- Enable dark mode, responsive design, and professional SaaS UI

## Non-Goals

- Not a replacement for emergency services (always recommends contacting a professional)
- Not a diagnostic tool (agents explicitly avoid diagnosing diseases)
- No real-time video or audio consultation
- No integration with hospital EHR systems (future scope)
- No mobile native apps (responsive web only for MVP)
- No multi-language support (English only for MVP)
- No admin dashboard (MVP focuses on Patient and Doctor roles)
- No HIPAA compliance certification (MVP uses security best practices but is not certified)

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

---

## Complete Feature List

### 1. Authentication
- Patient registration (email + password)
- Doctor registration (email + password + specialization)
- JWT-based login with access and refresh tokens
- Token refresh mechanism
- Password hashing with bcrypt
- Role-based access control (patient vs doctor routes)
- Auth state persistence via Zustand (frontend)
- Auth middleware for route protection (frontend + backend)

### 2. Patient Dashboard
- Welcome card with patient name
- Summary statistics cards (active medicines, reports, appointments, adherence)
- Today's medicine schedule view
- Recent alerts summary
- Quick action buttons (chat, upload, check symptoms)

### 3. Doctor Dashboard
- Total patients count
- Pending alerts count
- Upcoming appointments
- Average adherence rate across patients
- Recent patient activity feed
- Pending alerts list with risk levels

### 4. Prescription Upload
- Drag-and-drop file upload
- PDF, JPG, PNG file support
- File size validation (max 10MB)
- Automatic file type detection
- Upload progress indication
- Multiple file upload support (future)

### 5. OCR (Optical Character Recognition)
- Google Cloud Vision API integration
- PDF-to-image conversion for OCR processing
- Image preprocessing (contrast enhancement, deskew)
- Text extraction from uploaded reports
- Error handling for unreadable documents
- Fallback to Tesseract OCR (offline mode — future)

### 6. Medical Report Understanding Agent
- LangGraph-powered extraction pipeline
- Extracts: disease name, medicines list, dosage, frequency, duration, route, follow-up date, doctor instructions
- Validates extracted data for completeness and confidence
- Stores structured data to PostgreSQL
- Handles partial extraction gracefully
- Reports extraction status (pending → processing → completed / failed)

### 7. Patient Chat Agent
- LangGraph-powered conversational agent
- RAG over patient's uploaded reports
- Answers questions about medications, dosage, and instructions
- Explains medical terms in simple language
- Maintains conversation history within session
- Cites sources from patient's reports
- Falls back gracefully when information is unavailable
- Context window management (last N messages)

### 8. Medicine Reminder Agent
- Generates reminder schedule based on extracted medicine data
- Tracks adherence (taken / missed / skipped)
- Daily adherence rate calculation
- Weekly and monthly adherence statistics
- Missed dose detection and logging
- In-app reminder notifications

### 9. Emergency Detection Agent
- LangGraph-powered symptom analysis
- Classifies urgency as LOW / MEDIUM / HIGH
- Never diagnoses diseases
- Generates actionable recommendations
- Includes medical disclaimer
- Stores alerts in database with patient reference
- Doctor acknowledgment workflow
- Alert prioritization (HIGH risk shown first)

### 10. Doctor Summary Agent
- LangGraph-powered patient summarization
- Aggregates: adherence data, symptoms, chat history, report data
- Generates concise clinical summary
- Highlights concerning patterns
- Recommends follow-up actions
- Periodic auto-generation (future)

### 11. RAG (Retrieval-Augmented Generation)
- ChromaDB vector store for report embeddings
- OpenAI text-embedding-3-small for embeddings
- Document chunking and ingestion pipeline
- Semantic search over patient reports
- Source citation in chat responses
- Patient-specific document isolation

### 12. Notifications (In-App)
- Medicine reminder notifications
- Emergency alert notifications
- Appointment reminders
- Report processing completion notifications

### 13. Deployment
- Docker containerization (backend + frontend + PostgreSQL + ChromaDB)
- Vercel deployment (frontend)
- Render deployment (backend)
- Neon PostgreSQL (managed database)
- CI/CD via GitHub Actions
- Environment-based configuration

### 14. Future Enhancements
- Email and SMS notifications (Twilio)
- Push notifications (Web Push API)
- WhatsApp chatbot integration
- Real-time video consultation
- EHR system integration (FHIR)
- Multi-language support
- Admin dashboard with analytics
- Mobile native apps (React Native)
- Offline mode
- HIPAA compliance certification
- Wearable device integration (Apple Health, Fitbit)

---

## System Architecture

```
┌────────────────────────────────────────────────────────┐
│                    FRONTEND TIER                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Next.js 15 (App Router)              │  │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────────────┐  │  │
│  │  │  Pages  │ │Components│ │  Zustand Stores   │  │  │
│  │  └─────────┘ └──────────┘ └──────────────────┘  │  │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────────────┐  │  │
│  │  │ Services│ │  Hooks   │ │  API Client      │  │  │
│  │  └─────────┘ └──────────┘ └──────────────────┘  │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────┬───────────────────────────────┘
                         │ HTTP / JSON
                         ▼
┌────────────────────────────────────────────────────────┐
│                     API TIER                            │
│  ┌──────────────────────────────────────────────────┐  │
│  │              FastAPI (Uvicorn)                     │  │
│  │  ┌──────────┐ ┌───────────┐ ┌────────────────┐  │  │
│  │  │  Routes  │ │Middleware │ │  Dependencies  │  │  │
│  │  └──────────┘ └───────────┘ └────────────────┘  │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────┬───────────────────────────────┘
                         ▼
┌────────────────────────────────────────────────────────┐
│                   SERVICE TIER                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Business Logic / Use Cases                │  │
│  │  AuthService  │  PatientService  │  ReportService  │  │
│  │  ChatService  │  MedicineService │  AdherenceSvc   │  │
│  │  EmergencySvc │  SummaryService  │  AppointmentSvc │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────┬───────────────────────────────┘
                         │
          ┌──────────────┼──────────────────┐
          ▼              ▼                  ▼
┌─────────────────┐ ┌──────────┐ ┌──────────────────┐
│   AGENT TIER    │ │   DATA   │ │   EXTERNAL       │
│   (LangGraph)   │ │   TIER   │ │   SERVICES       │
│                 │ │          │ │                  │
│ Medical Agent   │ │  SQLAlch │ │  OpenAI API      │
│ Chat Agent      │ │  Models  │ │  Google Vision   │
│ Reminder Agent  │ │          │ │                  │
│ Emergency Agent │ │  Repos   │ │  ChromaDB        │
│ Summary Agent   │ │          │ │                  │
│ Orchestrator    │ │  Alembic │ │                  │
└─────────────────┘ └──────────┘ └──────────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  PostgreSQL  │
                  │   (Neon)     │
                  └──────────────┘
```

## Folder Structure

```
AI-Healthcare-Agent/
│
├── frontend/                          # Next.js 15 Application
│   ├── public/                        # Static assets
│   ├── src/
│   │   ├── app/                       # App Router pages
│   │   │   ├── (auth)/                # Login, Register
│   │   │   ├── patient/               # Patient pages (7 routes)
│   │   │   └── doctor/                # Doctor pages (4 routes)
│   │   ├── components/
│   │   │   ├── ui/                    # shadcn/ui primitives
│   │   │   ├── shared/                # Theme, Loading, Empty states
│   │   │   ├── patient/               # Patient-specific components
│   │   │   ├── doctor/                # Doctor-specific components
│   │   │   ├── layout/                # Layout components
│   │   │   └── forms/                 # Form components
│   │   ├── services/                  # API client layer
│   │   ├── lib/
│   │   │   ├── store/                 # Zustand stores
│   │   │   └── utils.ts               # Utility functions
│   │   ├── hooks/                     # Custom React hooks
│   │   ├── types/                     # TypeScript type definitions
│   │   ├── styles/                    # Additional styles
│   │   └── middleware.ts              # Auth route guard
│   ├── Dockerfile
│   └── package.json
│
├── backend/                           # FastAPI Application
│   ├── app/
│   │   ├── api/                       # Route handlers
│   │   │   └── v1/                    # API version 1
│   │   ├── core/                      # Config, security, logging
│   │   ├── database/                  # DB engine, session, base
│   │   ├── models/                    # SQLAlchemy models (9 tables)
│   │   ├── schemas/                   # Pydantic schemas
│   │   ├── repositories/              # Data access layer (8 repos)
│   │   ├── services/                  # Business logic (10 services)
│   │   ├── agents/                    # LangGraph agents
│   │   │   ├── medical_agent/         # Report extraction
│   │   │   ├── chat_agent/            # Patient Q&A
│   │   │   ├── reminder_agent/        # Medicine reminders
│   │   │   ├── emergency_agent/       # Symptom triage
│   │   │   ├── summary_agent/         # Doctor summaries
│   │   │   └── orchestrator.py        # Agent router
│   │   ├── langgraph/                 # Shared graph components
│   │   ├── middleare/                 # CORS, error handlers
│   │   ├── ocr/                       # Google Vision OCR
│   │   ├── rag/                       # ChromaDB RAG system
│   │   ├── prompts/                   # LLM prompt templates
│   │   ├── tasks/                     # Background tasks
│   │   └── utils/                     # Utility functions
│   ├── tests/                         # Test suite
│   │   ├── test_api/                  # API integration tests
│   │   ├── test_services/             # Service unit tests
│   │   ├── test_agents/               # Agent tests
│   │   └── test_rag/                  # RAG tests
│   ├── alembic/                       # DB migrations
│   ├── Dockerfile
│   └── requirements.txt
│
├── docker/                            # Docker Compose files
│   ├── docker-compose.yml
│   ├── docker-compose.dev.yml
│   └── postgres/init.sql
│
├── scripts/                           # Setup and migration scripts
├── .github/workflows/                 # CI/CD pipelines
├── docs/                              # Documentation
├── ARCHITECTURE.md                    # Architecture reference
├── PROJECT_PLAN.md                    # This file
├── TASKS.md                           # Task tracking
├── CHANGELOG.md                       # Version history
└── README.md                          # Project overview
```

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
| class-variance-authority | 0.7+ | Component variants |
| tailwind-merge | 2.6+ | Tailwind class merging |

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
| LangGraph | 0.2+ | Agent orchestration |
| LangChain | 0.3+ | LLM framework |
| LangChain OpenAI | 0.2+ | OpenAI integration |
| OpenAI | 1.56+ | GPT-4o-mini API |
| ChromaDB | 0.5+ | Vector store |
| tiktoken | 0.8+ | Token counting |

### OCR

| Dependency | Version | Purpose |
|-----------|---------|---------|
| google-cloud-vision | 3.8+ | Cloud OCR |
| Pillow | 11.1+ | Image processing |
| pytesseract | 0.3+ | Tesseract fallback |
| pdf2image | 1.17+ | PDF conversion |
| pypdf | 5.1+ | PDF parsing |

### Infrastructure

| Tool | Purpose |
|------|---------|
| Docker | Containerization |
| Docker Compose | Multi-service orchestration |
| Vercel | Frontend hosting |
| Render | Backend hosting |
| Neon | Managed PostgreSQL |
| GitHub Actions | CI/CD |

## Database Schema

### Entity Relationship

```
patients ──< patient_doctors >── doctors
patients ──< reports
patients ──< medicines
patients ──< chat_history
patients ──< adherence_logs
patients ──< emergency_alerts
patients ──< appointments >── doctors
reports   ──< medicines
```

### Tables

#### patients
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default gen_random_uuid() |
| email | VARCHAR(255) | UNIQUE, NOT NULL, INDEX |
| password_hash | VARCHAR(255) | NOT NULL |
| full_name | VARCHAR(255) | NOT NULL |
| phone | VARCHAR(50) | NULLABLE |
| date_of_birth | DATE | NULLABLE |
| gender | VARCHAR(20) | NULLABLE |
| blood_group | VARCHAR(10) | NULLABLE |
| address | TEXT | NULLABLE |
| emergency_contact | VARCHAR(255) | NULLABLE |
| emergency_phone | VARCHAR(50) | NULLABLE |
| is_active | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() |

#### doctors
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| email | VARCHAR(255) | UNIQUE, NOT NULL, INDEX |
| password_hash | VARCHAR(255) | NOT NULL |
| full_name | VARCHAR(255) | NOT NULL |
| specialization | VARCHAR(255) | NULLABLE |
| license_number | VARCHAR(100) | NULLABLE |
| phone | VARCHAR(50) | NULLABLE |
| is_active | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() |

#### patient_doctors
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| patient_id | UUID | FK → patients.id, CASCADE |
| doctor_id | UUID | FK → doctors.id, CASCADE |
| is_active | BOOLEAN | DEFAULT TRUE |
| assigned_at | TIMESTAMPTZ | DEFAULT NOW() |
| UNIQUE | (patient_id, doctor_id) | |

#### reports
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| patient_id | UUID | FK → patients.id, CASCADE, INDEX |
| doctor_id | UUID | FK → doctors.id, NULLABLE |
| title | VARCHAR(255) | NULLABLE |
| file_path | VARCHAR(500) | NOT NULL |
| file_type | VARCHAR(50) | NULLABLE |
| ocr_text | TEXT | NULLABLE |
| extracted_data | JSONB | NULLABLE |
| status | VARCHAR(50) | DEFAULT 'pending' |
| error_message | TEXT | NULLABLE |
| uploaded_at | TIMESTAMPTZ | NOT NULL |
| processed_at | TIMESTAMPTZ | NULLABLE |

#### medicines
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| report_id | UUID | FK → reports.id, CASCADE |
| patient_id | UUID | FK → patients.id, CASCADE, INDEX |
| name | VARCHAR(255) | NOT NULL |
| dosage | VARCHAR(100) | NULLABLE |
| frequency | VARCHAR(255) | NULLABLE |
| duration | VARCHAR(100) | NULLABLE |
| route | VARCHAR(50) | NULLABLE |
| instructions | TEXT | NULLABLE |
| start_date | DATE | NULLABLE |
| end_date | DATE | NULLABLE |
| is_active | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMPTZ | NOT NULL |
| INDEX | (patient_id, is_active) | |

#### appointments
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| patient_id | UUID | FK → patients.id, CASCADE, INDEX |
| doctor_id | UUID | FK → doctors.id, CASCADE, INDEX |
| title | VARCHAR(255) | NULLABLE |
| description | TEXT | NULLABLE |
| scheduled_at | TIMESTAMPTZ | NOT NULL |
| status | VARCHAR(50) | DEFAULT 'scheduled' |
| follow_up_notes | TEXT | NULLABLE |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() |

#### chat_history
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| patient_id | UUID | FK → patients.id, CASCADE, INDEX |
| role | VARCHAR(20) | NOT NULL ('user' | 'assistant') |
| message | TEXT | NOT NULL |
| metadata | JSONB | NULLABLE |
| created_at | TIMESTAMPTZ | NOT NULL |

#### adherence_logs
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| medicine_id | UUID | FK → medicines.id, CASCADE, INDEX |
| patient_id | UUID | FK → patients.id, CASCADE, INDEX |
| scheduled_time | TIMESTAMPTZ | NOT NULL |
| taken_at | TIMESTAMPTZ | NULLABLE |
| status | VARCHAR(20) | DEFAULT 'pending' |
| notes | TEXT | NULLABLE |
| created_at | TIMESTAMPTZ | NOT NULL |
| INDEX | (patient_id, status) | |

#### emergency_alerts
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| patient_id | UUID | FK → patients.id, CASCADE, INDEX |
| risk_level | VARCHAR(20) | NOT NULL, INDEX |
| symptoms | TEXT | NOT NULL |
| analysis | TEXT | NULLABLE |
| is_acknowledged | BOOLEAN | DEFAULT FALSE |
| acknowledged_by | UUID | FK → doctors.id, NULLABLE |
| created_at | TIMESTAMPTZ | NOT NULL |
| resolved_at | TIMESTAMPTZ | NULLABLE |

## API Endpoints

### Authentication (`/api/v1/auth`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /register/patient | No | Register new patient |
| POST | /register/doctor | No | Register new doctor |
| POST | /login | No | Unified login (role-based) |
| POST | /logout | Yes | Logout and revoke refresh token |
| POST | /refresh | No | Refresh JWT tokens with rotation |
| GET | /me | Yes | Get current user profile |

### Patients (`/api/v1/patients`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /me | Patient | Get current patient profile |
| PATCH | /me | Patient | Update profile |
| GET | /me/doctors | Patient | List assigned doctors |

### Doctors (`/api/v1/doctors`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /me | Doctor | Get current doctor profile |
| GET | /me/patients | Doctor | List assigned patients |
| POST | /me/patients/{id}/assign | Doctor | Assign patient |

### Reports (`/api/v1/reports`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /upload | Patient | Upload report file |
| GET | / | Patient | List patient's reports |
| GET | /{id} | Patient | Get report details |
| DELETE | /{id} | Patient | Delete report |

### Chat (`/api/v1/chat`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /message | Patient | Send message, get AI response |
| GET | /history | Patient | Get chat history |
| DELETE | /history | Patient | Clear chat history |

### Appointments (`/api/v1/appointments`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | / | Patient | Create appointment |
| GET | / | Patient | List patient appointments |
| GET | /doctor | Doctor | List doctor appointments |
| PATCH | /{id} | Both | Update appointment |
| DELETE | /{id} | Both | Delete appointment |

### Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /health | No | Health check |
| GET | / | No | API root info |

## AI Agents

### 1. Medical Report Agent
**Purpose:** Extract structured medical data from prescription/report text.
**State:** `{ raw_text, extracted_data, validation_status, error }`
**Nodes:**
- `extract_entities` — Parses raw OCR text using LLM to extract disease, medicines, dosage, frequency, dates
- `validate_extraction` — Validates completeness and confidence of extracted data
- `store_results` — Persists extracted medicines to database and updates report status
**Output:** Structured medicine data stored in `medicines` and `reports.extracted_data`

### 2. Patient Chat Agent
**Purpose:** Answer patient questions using their uploaded reports and history.
**State:** `{ question, context_docs, chat_history, response, sources }`
**Nodes:**
- `retrieve_context` — Queries ChromaDB for relevant document chunks based on question
- `generate_response` — Feeds context + history to LLM and generates patient-friendly answer
**Output:** Natural language response with source citations

### 3. Reminder Agent
**Purpose:** Generate medicine reminders and track adherence.
**State:** `{ medicines, schedule, reminders, adherence_status }`
**Nodes:**
- `check_schedule` — Queries active medicines and computes upcoming dose schedule
- `generate_reminders` — Creates reminder notifications for each scheduled dose
- `track_adherence` — Monitors adherence logs and computes statistics
**Output:** Adherence data and reminders

### 4. Emergency Detection Agent
**Purpose:** Analyze symptoms and classify urgency.
**State:** `{ symptoms, risk_level, analysis, recommendations }`
**Nodes:**
- `analyze_symptoms` — Sends symptoms to LLM for analysis
- `classify_risk` — Classifies as LOW / MEDIUM / HIGH urgency
- `generate_recommendations` — Produces actionable advice and disclaimer
**Rules:** Never diagnoses diseases. Only classifies urgency. Always includes medical disclaimer.

### 5. Doctor Summary Agent
**Purpose:** Generate concise patient summaries for doctors.
**State:** `{ patient_data, summary }`
**Nodes:**
- `aggregate_data` — Pulls adherence stats, symptoms, chat history, report data from DB
- `generate_summary` — Feeds aggregated data to LLM for clinical summary generation
**Output:** Structured JSON summary with adherence rates, concerns, and recommendations

## LangGraph Workflow

### Orchestrator Flow

```
User Request
    │
    ▼
Router Node (classifies intent)
    │
    ├── "report"    → Medical Report Agent
    ├── "chat"      → Patient Chat Agent
    ├── "emergency" → Emergency Detection Agent
    └── "summary"   → Doctor Summary Agent
    │
    ▼
Response Aggregator
    │
    ▼
Response
```

### Medical Report Agent Nodes

```
extract_entities
    │ (raw_text available)
    ▼
validate_extraction
    │ (extracted_data valid)
    ▼
store_results ──→ END
```

### Patient Chat Agent Nodes

```
retrieve_context (ChromaDB query)
    │
    ▼
generate_response (LLM call)
    │
    ▼
END (return response + sources)
```

### Emergency Detection Agent Nodes

```
analyze_symptoms (LLM classification)
    │
    ▼
classify_risk (LOW/MEDIUM/HIGH)
    │
    ▼
generate_recommendations
    │
    ▼
END (store alert, return result)
```

### Reminder Agent Nodes

```
check_schedule (DB query)
    │
    ▼
generate_reminders (schedule computation)
    │
    ▼
track_adherence (log monitoring)
    │
    ▼
END
```

### Doctor Summary Agent Nodes

```
aggregate_data (multi-source DB query)
    │
    ▼
generate_summary (LLM summarization)
    │
    ▼
END (return summary JSON)
```

## Development Phases

### Phase 1: Foundation ✓ (COMPLETED)
- Initialize Next.js project with Tailwind + shadcn/ui
- Initialize FastAPI project with SQLAlchemy + Alembic
- Set up Docker Compose (PostgreSQL + ChromaDB)
- Create complete folder structure
- Configure environment variables
- Set up code quality tools (Black, isort, flake8, pre-commit)
- Write architecture documentation (ARCHITECTURE.md)
- Create PROJECT_PLAN.md, TASKS.md, CHANGELOG.md

### Phase 2: Authentication ✅ (COMPLETED)
**Backend:**
- Implement JWT token creation and validation (access + refresh) with HS256
- Build unified login endpoint with role parameter (patient/doctor)
- Build patient registration with full profile fields (DOB, gender, phone, terms_accepted)
- Build doctor registration with license, hospital, specialization, experience fields
- Add strong password validation (8+ chars, uppercase, lowercase, number, special)
- Add phone validation (E.164 format), email validation, DOB validation
- Implement token refresh mechanism with rotation (revokes old, issues new)
- Build logout endpoint with server-side refresh token revocation
- Build /me endpoint returning full user profile by role
- Create RefreshToken model and repository for DB-backed token management
- Add role-based access control with reusable FastAPI dependencies
- Implement remember_me (30-day refresh tokens) vs standard (7-day)
- Token pair generation with jti, token hashing for secure storage
- 18 comprehensive unit tests covering all auth flows

**Frontend:**
- Build login page with role toggle, remember me checkbox, forgot password link
- Build multi-step registration (role selection → full form) with patient/doctor fields
- Implement auth store with Zustand + localStorage persistence (rememberMe support)
- Build API client with JWT interceptor, auto-refresh queue, and retry logic
- Add route protection middleware with role-based redirects
- Implement auto-redirect based on role after login/register
- Server-side logout via API before clearing local state

### Phase 3: Database (PENDING)
- Run initial Alembic migration (all 9 tables)
- Add seed data scripts
- Implement database session management
- Add database health check endpoint
- Test all model relationships

### Phase 4: OCR (PENDING)
**Backend:**
- Integrate Google Cloud Vision API
- Build image preprocessing pipeline
- Implement PDF to image conversion
- Create OCR service with fallback
- Add text extraction endpoint
- Implement file upload validation

**Frontend:**
- Build drag-and-drop file upload component
- Add upload progress indicator
- Implement file type validation
- Display uploaded reports list

### Phase 5: Medical Report Agent (PENDING)
- Implement LangGraph agent for data extraction
- Create LLM prompt for medical entity extraction
- Build validation pipeline for extracted data
- Store structured data in medicines table
- Update report status through pipeline
- Test with sample prescriptions

### Phase 6: Patient Chat Agent (PENDING)
- Set up ChromaDB with embeddings
- Build document ingestion pipeline for reports
- Implement RAG retriever service
- Build LangGraph chat agent
- Create chat UI with message history
- Add source citation display

### Phase 7: Medicine Reminder Agent (PENDING)
- Implement reminder schedule generation
- Build adherence logging endpoint
- Create daily schedule view
- Implement adherence statistics computation
- Build adherence chart (frontend)
- Add missed dose detection

### Phase 8: Emergency Detection Agent (PENDING)
- Implement LangGraph emergency agent
- Build symptom check UI
- Create risk level display with color coding
- Implement alert storage and retrieval
- Build doctor alert management view
- Add alert acknowledgment workflow

### Phase 9: Doctor Dashboard (PENDING)
- Build patient list with search/filter
- Implement patient detail view
- Build AI summary generation and display
- Create adherence overview component
- Add medicine adherence per patient
- Implement report review for doctors

### Phase 10: Deployment (PENDING)
- Optimize Docker images (multi-stage builds)
- Set up Vercel deployment for frontend
- Set up Render deployment for backend
- Configure Neon PostgreSQL
- Set up GitHub Actions CI/CD
- Add health monitoring
- Performance optimization
- Final testing and bug fixes

---

## Coding Standards

### Naming Conventions

| Category | Convention | Example |
|----------|-----------|---------|
| Python files | snake_case | `auth_service.py` |
| Python classes | PascalCase | `AuthService` |
| Python functions | snake_case | `create_access_token` |
| Python variables | snake_case | `db_session` |
| TypeScript files | kebab-case | `auth-store.ts` |
| TypeScript interfaces | PascalCase | `AuthResponse` |
| TypeScript types | PascalCase | `UserRole` |
| TypeScript functions | camelCase | `loginPatient` |
| TypeScript variables | camelCase | `accessToken` |
| React components | PascalCase | `LoginForm` |
| React files | PascalCase | `LoginForm.tsx` |
| CSS classes | kebab-case | `bg-primary` |
| Database tables | snake_case | `adherence_logs` |
| Database columns | snake_case | `patient_id` |
| API endpoints | kebab-case | `/patient/login` |
| Environment variables | UPPER_SNAKE | `JWT_SECRET_KEY` |
| Git branches | kebab-case | `feature/auth` |

### Folder Conventions

- Every module gets its own folder
- Every folder has `__init__.py` (Python) or `index.ts` (TypeScript)
- UI components co-located with their styles
- Tests mirror source structure
- Shared code goes in `shared/` or `lib/`
- No deep nesting beyond 3 levels

### Architecture Rules

1. **API Layer** → validates requests, calls services, returns responses. Never contains business logic.
2. **Service Layer** → orchestrates operations, calls agents, repositories, and external services. Never directly handles HTTP requests.
3. **Repository Layer** → data access only. Never contains business logic.
4. **Agent Layer** → LangGraph workflows. Never directly accesses database (uses services).
5. **Dependency Injection** → always inject dependencies via constructor or FastAPI `Depends`.
6. **Type Annotations** → all Python functions must have type hints. All TypeScript must be strictly typed.
7. **Error Handling** → use custom `AppException` hierarchy with HTTP status codes.
8. **No Circular Dependencies** → services can depend on repositories and agents, but not vice versa.

### Dependency Rules

```
Core (config, security) → No dependencies
Database (base, session) → Core
Models → Database
Repositories → Models
Services → Repositories, Agents, OCR, RAG
Agents → Services, RAG, OpenAI
RAG → ChromaDB, OpenAI embeddings
API Routes → Services (via DI)
Frontend → API Routes (HTTP only)
```

### SOLID Principles

- **S**ingle Responsibility: Each class has exactly one reason to change.
- **O**pen/Closed: Services are open for extension via DI, closed for modification.
- **L**iskov Substitution: Derived classes are substitutable for base classes.
- **I**nterface Segregation: Small, focused interfaces over monolithic ones.
- **D**ependency Inversion: High-level modules depend on abstractions, not concretions.

### DRY (Don't Repeat Yourself)

- Generic `BaseRepository` for CRUD operations (no repetition across repositories)
- Shared utility functions in `utils/`
- Reusable UI components in `components/ui/`
- Shared types in `types/`
- Common error handling via `AppException`

### Clean Architecture Layers

```
┌──────────────────────┐
│   API (Controllers)  │  ← FastAPI routes
├──────────────────────┤
│   Services (Use Cases)│  ← Business logic
├──────────────────────┤
│   Repositories (Data) │  ← Database access
├──────────────────────┤
│   Models (Entities)   │  ← SQLAlchemy models
└──────────────────────┘
```

---

## Design Guidelines

### Color Palette

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| --background | White (#FFF) | Slate 950 | Page background |
| --foreground | Slate 900 | Slate 50 | Primary text |
| --primary | Blue 600 | Blue 400 | Buttons, links, active states |
| --secondary | Slate 100 | Slate 800 | Secondary elements |
| --muted | Slate 100 | Slate 800 | Subtle backgrounds |
| --accent | Slate 100 | Slate 800 | Hover states |
| --destructive | Red 600 | Red 400 | Errors, deletion |
| --border | Slate 200 | Slate 800 | Borders |
| --sidebar | Slate 900 | Slate 950 | Sidebar background |

### Typography

- **Font:** Inter (system font stack fallback)
- **Headings:** Font-weight 600-700
- **Body:** Font-weight 400, size 14-16px
- **Small text:** Font-weight 400, size 12-13px
- **Line height:** 1.5 (body), 1.2 (headings)

### UI Principles

1. **Minimalist** — Less is more. Every element must serve a purpose.
2. **Consistent** — Reuse components, spacings, and patterns.
3. **Accessible** — WCAG 2.1 AA minimum contrast ratios.
4. **Responsive** — Mobile-first, adapts from 320px to 4K.
5. **Feedback-rich** — Loading states, toasts, confirmations for all actions.
6. **Error-tolerant** — Clear error messages, form validation, recovery paths.

### Accessibility

- Semantic HTML throughout
- ARIA labels on interactive elements
- Keyboard navigation support
- Focus indicators visible
- Color not the only indicator (text + icon + color)
- Minimum touch target 44×44px on mobile
- Reduced motion support via `prefers-reduced-motion`

### Dark Mode

- CSS variables for all colors (swap between light/dark)
- System preference detection via `prefers-color-scheme`
- Manual toggle persisted in Zustand
- Images with dark mode variants where needed
- Smooth transition between modes (300ms)

---

*This document is the authoritative source for project decisions. Update it whenever architecture, features, or standards change.*
