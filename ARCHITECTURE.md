# AI Healthcare Follow-up Assistant — Architecture Plan

---

## 1. FOLDER STRUCTURE

```
healthcare-assistant/
│
├── frontend/                          # Next.js Application
│   ├── public/
│   │   ├── images/
│   │   └── icons/
│   ├── src/
│   │   ├── app/                       # Next.js App Router (pages)
│   │   │   ├── (auth)/
│   │   │   │   ├── login/
│   │   │   │   ├── register/
│   │   │   │   └── layout.tsx
│   │   │   ├── (patient)/
│   │   │   │   ├── dashboard/
│   │   │   │   ├── chat/
│   │   │   │   ├── medicines/
│   │   │   │   ├── reports/
│   │   │   │   ├── appointments/
│   │   │   │   └── layout.tsx
│   │   │   ├── (doctor)/
│   │   │   │   ├── dashboard/
│   │   │   │   ├── patients/
│   │   │   │   │   └── [id]/
│   │   │   │   ├── summaries/
│   │   │   │   └── layout.tsx
│   │   │   ├── layout.tsx             # Root layout
│   │   │   └── page.tsx               # Landing/redirect
│   │   ├── components/
│   │   │   ├── ui/                    # shadcn/ui primitives
│   │   │   ├── auth/
│   │   │   │   ├── LoginForm.tsx
│   │   │   │   └── RegisterForm.tsx
│   │   │   ├── patient/
│   │   │   │   ├── MedicineCard.tsx
│   │   │   │   ├── ReportUpload.tsx
│   │   │   │   ├── ChatWindow.tsx
│   │   │   │   └── AdherenceChart.tsx
│   │   │   ├── doctor/
│   │   │   │   ├── PatientList.tsx
│   │   │   │   ├── PatientDetail.tsx
│   │   │   │   ├── SummaryCard.tsx
│   │   │   │   └── AdherenceOverview.tsx
│   │   │   ├── shared/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── ThemeToggle.tsx
│   │   │   │   └── LoadingState.tsx
│   │   │   └── emergency/
│   │   │       └── SymptomChecker.tsx
│   │   ├── lib/
│   │   │   ├── api/                   # API client layer
│   │   │   │   ├── client.ts          # Axios instance + interceptors
│   │   │   │   ├── auth.ts
│   │   │   │   ├── patients.ts
│   │   │   │   ├── medicines.ts
│   │   │   │   ├── reports.ts
│   │   │   │   ├── chat.ts
│   │   │   │   └── doctor.ts
│   │   │   ├── store/                 # Zustand stores
│   │   │   │   ├── authStore.ts
│   │   │   │   ├── patientStore.ts
│   │   │   │   └── uiStore.ts
│   │   │   ├── hooks/
│   │   │   │   ├── useAuth.ts
│   │   │   │   ├── useMedicines.ts
│   │   │   │   └── useChat.ts
│   │   │   ├── schemas/              # Zod validation schemas
│   │   │   │   ├── auth.ts
│   │   │   │   ├── report.ts
│   │   │   │   └── symptom.ts
│   │   │   └── utils/
│   │   │       ├── cn.ts             # Tailwind class merge
│   │   │       └── date.ts
│   │   ├── types/
│   │   │   ├── auth.ts
│   │   │   ├── patient.ts
│   │   │   ├── medicine.ts
│   │   │   ├── report.ts
│   │   │   ├── chat.ts
│   │   │   └── doctor.ts
│   │   └── middleware.ts             # Next.js middleware (auth guard)
│   ├── .env.local
│   ├── tailwind.config.ts
│   ├── next.config.js
│   ├── tsconfig.json
│   ├── components.json               # shadcn/ui config
│   └── package.json
│
├── backend/                           # FastAPI Application
│   ├── alembic/
│   │   ├── versions/
│   │   ├── env.py
│   │   └── alembic.ini
│   ├── app/
│   │   ├── api/                       # API layer (routes)
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py         # Aggregates all routers
│   │   │   │   ├── auth.py
│   │   │   │   ├── patients.py
│   │   │   │   ├── doctors.py
│   │   │   │   ├── medicines.py
│   │   │   │   ├── reports.py
│   │   │   │   ├── chat.py
│   │   │   │   ├── adherence.py
│   │   │   │   ├── emergency.py
│   │   │   │   └── summaries.py
│   │   │   └── deps.py               # Dependency injection
│   │   ├── core/                      # Core config
│   │   │   ├── config.py             # Settings from env
│   │   │   ├── database.py           # SQLAlchemy engine
│   │   │   ├── security.py           # JWT utilities
│   │   │   └── exceptions.py         # Custom exceptions
│   │   ├── models/                    # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── patient.py
│   │   │   ├── doctor.py
│   │   │   ├── medicine.py
│   │   │   ├── report.py
│   │   │   ├── appointment.py
│   │   │   ├── chat_history.py
│   │   │   ├── adherence_log.py
│   │   │   └── emergency_alert.py
│   │   ├── schemas/                   # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── patient.py
│   │   │   ├── doctor.py
│   │   │   ├── medicine.py
│   │   │   ├── report.py
│   │   │   ├── chat.py
│   │   │   ├── adherence.py
│   │   │   ├── emergency.py
│   │   │   └── summary.py
│   │   ├── services/                  # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── patient_service.py
│   │   │   ├── medicine_service.py
│   │   │   ├── report_service.py
│   │   │   ├── chat_service.py
│   │   │   ├── adherence_service.py
│   │   │   ├── emergency_service.py
│   │   │   └── summary_service.py
│   │   ├── agents/                    # LangGraph agents
│   │   │   ├── __init__.py
│   │   │   ├── medical_report_agent/
│   │   │   │   ├── graph.py
│   │   │   │   ├── nodes.py
│   │   │   │   ├── state.py
│   │   │   │   └── prompts.py
│   │   │   ├── patient_chat_agent/
│   │   │   │   ├── graph.py
│   │   │   │   ├── nodes.py
│   │   │   │   ├── state.py
│   │   │   │   └── prompts.py
│   │   │   ├── reminder_agent/
│   │   │   │   ├── graph.py
│   │   │   │   ├── nodes.py
│   │   │   │   ├── state.py
│   │   │   │   └── prompts.py
│   │   │   ├── emergency_agent/
│   │   │   │   ├── graph.py
│   │   │   │   ├── nodes.py
│   │   │   │   ├── state.py
│   │   │   │   └── prompts.py
│   │   │   ├── doctor_summary_agent/
│   │   │   │   ├── graph.py
│   │   │   │   ├── nodes.py
│   │   │   │   ├── state.py
│   │   │   │   └── prompts.py
│   │   │   └── orchestrator.py        # Main LangGraph workflow
│   │   ├── rag/                       # RAG system
│   │   │   ├── __init__.py
│   │   │   ├── embeddings.py
│   │   │   ├── vector_store.py        # ChromaDB integration
│   │   │   └── retriever.py
│   │   ├── ocr/                       # OCR service
│   │   │   ├── __init__.py
│   │   │   ├── google_vision.py
│   │   │   └── preprocessor.py
│   │   ├── tasks/                     # Background tasks (Celery/scheduler)
│   │   │   ├── __init__.py
│   │   │   ├── reminder_scheduler.py
│   │   │   └── adherence_monitor.py
│   │   └── main.py                    # FastAPI entry point
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_api/
│   │   ├── test_services/
│   │   ├── test_agents/
│   │   └── test_ocr/
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env
│   └── pyproject.toml
│
├── docker/
│   ├── docker-compose.yml
│   ├── docker-compose.dev.yml
│   └── postgres/
│       └── init.sql
│
├── .github/
│   └── workflows/
│       ├── frontend-ci.yml
│       └── backend-ci.yml
│
├── .gitignore
├── README.md
└── ARCHITECTURE.md                    # This file
```

---

## 2. DATABASE SCHEMA

```sql
-- ============================================
-- PATIENTS
-- ============================================
CREATE TABLE patients (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    phone           VARCHAR(50),
    date_of_birth   DATE,
    gender          VARCHAR(20),
    blood_group     VARCHAR(10),
    address         TEXT,
    emergency_contact VARCHAR(255),
    emergency_phone VARCHAR(50),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    is_active       BOOLEAN DEFAULT TRUE
);

-- ============================================
-- DOCTORS
-- ============================================
CREATE TABLE doctors (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    specialization  VARCHAR(255),
    license_number  VARCHAR(100),
    phone           VARCHAR(50),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    is_active       BOOLEAN DEFAULT TRUE
);

-- ============================================
-- PATIENT-DOCTOR ASSIGNMENT
-- ============================================
CREATE TABLE patient_doctors (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id       UUID NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    assigned_at     TIMESTAMPTZ DEFAULT NOW(),
    is_active       BOOLEAN DEFAULT TRUE,
    UNIQUE(patient_id, doctor_id)
);

-- ============================================
-- REPORTS (uploaded prescriptions/medical reports)
-- ============================================
CREATE TABLE reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id       UUID REFERENCES doctors(id),
    title           VARCHAR(255),
    file_path       VARCHAR(500) NOT NULL,
    file_type       VARCHAR(50),       -- pdf, jpg, png
    ocr_text        TEXT,              -- raw OCR output
    extracted_data  JSONB,             -- structured extraction from agent
    status          VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed
    error_message   TEXT,
    uploaded_at     TIMESTAMPTZ DEFAULT NOW(),
    processed_at    TIMESTAMPTZ
);

-- ============================================
-- MEDICINES (extracted from reports)
-- ============================================
CREATE TABLE medicines (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id       UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    patient_id      UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    dosage          VARCHAR(100),
    frequency       VARCHAR(255),       -- e.g., "twice daily after meals"
    duration        VARCHAR(100),       -- e.g., "7 days", "30 days"
    route           VARCHAR(50),        -- oral, topical, IV, etc.
    instructions    TEXT,
    start_date      DATE,
    end_date        DATE,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- APPOINTMENTS
-- ============================================
CREATE TABLE appointments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id       UUID NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    title           VARCHAR(255),
    description     TEXT,
    scheduled_at    TIMESTAMPTZ NOT NULL,
    status          VARCHAR(50) DEFAULT 'scheduled',  -- scheduled, completed, cancelled, missed
    follow_up_notes TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- CHAT HISTORY
-- ============================================
CREATE TABLE chat_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL,   -- 'user' or 'assistant'
    message         TEXT NOT NULL,
    metadata        JSONB,                  -- sources, confidence, etc.
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- ADHERENCE LOGS
-- ============================================
CREATE TABLE adherence_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    medicine_id     UUID NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,
    patient_id      UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    scheduled_time  TIMESTAMPTZ NOT NULL,
    taken_at        TIMESTAMPTZ,            -- NULL if not taken
    status          VARCHAR(20) DEFAULT 'pending',  -- pending, taken, missed, skipped
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- EMERGENCY ALERTS
-- ============================================
CREATE TABLE emergency_alerts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    risk_level      VARCHAR(20) NOT NULL,   -- LOW, MEDIUM, HIGH
    symptoms        TEXT NOT NULL,
    analysis        TEXT,
    is_acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by UUID REFERENCES doctors(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    resolved_at     TIMESTAMPTZ
);

-- ============================================
-- INDEXES
-- ============================================
CREATE INDEX idx_reports_patient ON reports(patient_id);
CREATE INDEX idx_medicines_patient ON medicines(patient_id);
CREATE INDEX idx_medicines_active ON medicines(patient_id, is_active);
CREATE INDEX idx_chat_patient ON chat_history(patient_id);
CREATE INDEX idx_adherence_patient ON adherence_logs(patient_id);
CREATE INDEX idx_adherence_medicine ON adherence_logs(medicine_id);
CREATE INDEX idx_adherence_status ON adherence_logs(patient_id, status);
CREATE INDEX idx_emergency_patient ON emergency_alerts(patient_id);
CREATE INDEX idx_emergency_risk ON emergency_alerts(risk_level);
CREATE INDEX idx_appointments_patient ON appointments(patient_id);
CREATE INDEX idx_appointments_doctor ON appointments(doctor_id);
```

### Entity Relationship Summary

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

---

## 3. API ENDPOINTS

### Authentication

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/auth/patient/register` | Register patient | No |
| POST | `/api/v1/auth/patient/login` | Login patient | No |
| POST | `/api/v1/auth/doctor/register` | Register doctor | No |
| POST | `/api/v1/auth/doctor/login` | Login doctor | No |
| POST | `/api/v1/auth/refresh` | Refresh access token | Yes |
| GET | `/api/v1/auth/me` | Get current user | Yes |

### Patients

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/patients/me` | Get patient profile | Patient |
| PATCH | `/api/v1/patients/me` | Update profile | Patient |
| GET | `/api/v1/patients/me/doctors` | List assigned doctors | Patient |

### Doctors

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/doctors/me` | Get doctor profile | Doctor |
| GET | `/api/v1/doctors/me/patients` | List assigned patients | Doctor |
| GET | `/api/v1/doctors/me/patients/{id}` | Get patient detail | Doctor |
| POST | `/api/v1/doctors/me/patients/{id}/assign` | Assign patient | Doctor |

### Reports

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/reports/upload` | Upload report (multipart) | Patient |
| GET | `/api/v1/reports` | List patient's reports | Patient |
| GET | `/api/v1/reports/{id}` | Get report detail | Patient/Doctor |
| DELETE | `/api/v1/reports/{id}` | Delete report | Patient |
| POST | `/api/v1/reports/{id}/process` | Trigger AI processing | Patient |
| GET | `/api/v1/reports/doctor/patients/{id}` | List patient's reports (doctor) | Doctor |

### Medicines

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/medicines` | List patient's medicines | Patient |
| GET | `/api/v1/medicines/active` | List active medicines | Patient |
| GET | `/api/v1/medicines/{id}` | Get medicine detail | Patient/Doctor |
| PATCH | `/api/v1/medicines/{id}` | Update medicine | Patient |
| GET | `/api/v1/medicines/doctor/patients/{id}` | List patient meds (doctor) | Doctor |

### Chat

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/chat/message` | Send message, get AI response | Patient |
| GET | `/api/v1/chat/history` | Get chat history | Patient |
| DELETE | `/api/v1/chat/history` | Clear chat history | Patient |

### Adherence

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/adherence/today` | Today's schedule | Patient |
| POST | `/api/v1/adherence/log` | Log medicine taken | Patient |
| GET | `/api/v1/adherence/stats` | Adherence statistics | Patient |
| GET | `/api/v1/adherence/doctor/patients/{id}` | Patient adherence (doctor) | Doctor |

### Emergency

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/emergency/check` | Analyze symptoms | Patient |
| GET | `/api/v1/emergency/alerts` | Get patient's alerts | Patient |
| GET | `/api/v1/emergency/doctor/alerts` | Get all alerts (doctor) | Doctor |
| POST | `/api/v1/emergency/{id}/acknowledge` | Acknowledge alert | Doctor |

### Summaries (Doctor)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/summaries/patients/{id}` | Get patient AI summary | Doctor |
| GET | `/api/v1/summaries/dashboard` | Doctor dashboard summary | Doctor |

### Appointments

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/appointments` | List appointments | Patient/Doctor |
| POST | `/api/v1/appointments` | Create appointment | Patient/Doctor |
| PATCH | `/api/v1/appointments/{id}` | Update appointment | Patient/Doctor |
| DELETE | `/api/v1/appointments/{id}` | Cancel appointment | Patient/Doctor |

### Health

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/health` | Health check | No |

---

## 4. LANGGRAPH WORKFLOW

### Orchestrator Graph

```
                      ┌──────────────────┐
                      │   User Request   │
                      └────────┬─────────┘
                               │
                               ▼
                      ┌──────────────────┐
                      │   Router Node    │
                      │ (Classify intent)│
                      └──┬───┬───┬───┬──┘
                         │   │   │   │
            ┌────────────┘   │   │   └────────────┐
            ▼                ▼   ▼                 ▼
    ┌───────────────┐ ┌───────────┐ ┌───────────────────┐
    │ Medical Report│ │ Patient   │ │ Emergency         │
    │ Agent         │ │ Chat Agent│ │ Detection Agent   │
    └───────┬───────┘ └─────┬─────┘ └────────┬──────────┘
            │               │                │
            └───────────────┼────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  Doctor       │
                    │  Summary Agent│
                    │  (on demand)  │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  Reminder     │
                    │  Agent        │
                    │  (background) │
                    └───────────────┘
```

### 4.1 Medical Report Agent

```
State: { raw_text, extracted_data, validation_status, error }

         ┌───────────┐
         │  Extract  │  ← LLM: parse disease, medicines, dosage, dates
         │  Entities │
         └─────┬─────┘
               │
               ▼
         ┌───────────┐
         │  Validate │  ← Check completeness, confidence
         │  & Format │
         └─────┬─────┘
               │
               ▼
         ┌───────────┐
         │  Store to │  ← Save medicines + report data to DB
         │  Database │
         └───────────┘
```

### 4.2 Patient Chat Agent

```
State: { question, context_docs, chat_history, response }

         ┌───────────┐
         │ Retrieve  │  ← RAG from ChromaDB (patient's reports)
         │ Context   │
         └─────┬─────┘
               │
               ▼
         ┌───────────┐
         │ Generate  │  ← LLM with context + history
         │ Response  │
         └─────┬─────┘
               │
               ▼
         ┌───────────┐
         │ Store &   │  ← Save to chat_history
         │ Return    │
         └───────────┘
```

### 4.3 Reminder Agent

```
State: { patient_id, medicines, schedule, adherence_status }

         ┌───────────┐
         │ Check     │  ← Query upcoming doses
         │ Schedule  │
         └─────┬─────┘
               │
               ▼
         ┌───────────┐
         │ Generate  │  ← Create reminder notifications
         │ Reminders │
         └─────┬─────┘
               │
               ▼
         ┌───────────┐
         │ Track     │  ← Monitor adherence logs
         │ Adherence │
         └───────────┘
```

### 4.4 Emergency Detection Agent

```
State: { symptoms_text, risk_level, analysis, recommendations }

         ┌───────────┐
         │ Classify  │  ← LLM: analyze urgency level
         │ Risk      │
         └─────┬─────┘
               │
               ▼
         ┌───────────┐
         │ Generate  │  ← Actionable recommendations
         │ Advice    │
         └─────┬─────┘
               │
               ▼
         ┌───────────┐
         │ Store     │  ← Save to emergency_alerts
         │ Alert     │
         └───────────┘
```

### 4.5 Doctor Summary Agent

```
State: { patient_id, adherence_data, symptoms, chat_summary, report_summary }

         ┌───────────┐
         │ Aggregate │  ← Pull data from all sources
         │ Data      │
         └─────┬─────┘
               │
               ▼
         ┌───────────┐
         │ Generate  │  ← LLM: concise medical summary
         │ Summary   │
         └─────┬─────┘
               │
               ▼
         ┌───────────┐
         │ Return    │
         │ Summary   │
         └───────────┘
```

### LangGraph State Definition (conceptual)

```python
class AgentState(TypedDict):
    input: str
    intent: str                      # report, chat, emergency, summary
    patient_id: str
    doctor_id: Optional[str]
    report_id: Optional[str]
    raw_text: Optional[str]
    extracted_data: Optional[Dict]
    medicines: Optional[List[Dict]]
    chat_history: Optional[List[Dict]]
    symptoms: Optional[str]
    risk_level: Optional[str]
    context_docs: Optional[List[Dict]]
    response: Optional[str]
    summary: Optional[Dict]
    adherence_stats: Optional[Dict]
    error: Optional[str]
    next: Optional[str]
```

---

## 5. COMPONENT HIERARCHY

```
<App>
├── <AuthLayout>
│   ├── <LoginForm>
│   │   ├── EmailInput
│   │   ├── PasswordInput
│   │   └── SubmitButton
│   └── <RegisterForm>
│       ├── NameInput
│       ├── EmailInput
│       ├── PasswordInput
│       └── SubmitButton
│
├── <PatientLayout>                  # (authenticated patient)
│   ├── <Sidebar>
│   │   ├── Logo
│   │   ├── <NavItem> (Dashboard)
│   │   ├── <NavItem> (My Medicines)
│   │   ├── <NavItem> (Reports)
│   │   ├── <NavItem> (Chat)
│   │   ├── <NavItem> (Appointments)
│   │   └── <NavItem> (Emergency)
│   ├── <Header>
│   │   ├── PageTitle
│   │   ├── <ThemeToggle>
│   │   └── UserMenu (avatar + dropdown)
│   │
│   ├── <PatientDashboard>
│   │   ├── <WelcomeCard>
│   │   ├── <MedicineSummaryCard>    # active meds count
│   │   ├── <AdherenceChart>        # weekly adherence bar chart
│   │   ├── <UpcomingAppointments>
│   │   └── <RecentAlerts>
│   │
│   ├── <MedicinesPage>
│   │   ├── <MedicineList>
│   │   │   └── <MedicineCard> (×N)
│   │   │       ├── MedicineName
│   │   │       ├── DosageBadge
│   │   │       ├── FrequencyText
│   │   │       └── StatusIndicator
│   │   └── <AdherenceCalendar>
│   │
│   ├── <ReportsPage>
│   │   ├── <ReportUpload>
│   │   │   ├── DropZone (drag & drop)
│   │   │   └── UploadProgress
│   │   └── <ReportList>
│   │       └── <ReportCard> (×N)
│   │           ├── FileName
│   │           ├── UploadDate
│   │           ├── StatusBadge
│   │           └── ViewDetails (modal)
│   │
│   ├── <ChatPage>
│   │   └── <ChatWindow>
│   │       ├── MessageList
│   │       │   └── <ChatBubble> (×N)
│   │       └── ChatInput
│   │           ├── TextArea
│   │           └── SendButton
│   │
│   ├── <AppointmentsPage>
│   │   ├── AppointmentFilters
│   │   └── <AppointmentList>
│   │       └── <AppointmentCard> (×N)
│   │
│   └── <EmergencyPage>
│       └── <SymptomChecker>
│           ├── SymptomTextArea
│           ├── CheckButton
│           └── <RiskAlert> (LOW/MEDIUM/HIGH)
│
├── <DoctorLayout>                   # (authenticated doctor)
│   ├── <Sidebar>
│   │   ├── Logo
│   │   ├── <NavItem> (Dashboard)
│   │   ├── <NavItem> (Patients)
│   │   ├── <NavItem> (Alerts)
│   │   └── <NavItem> (Appointments)
│   ├── <Header>
│   │   ├── PageTitle
│   │   ├── <ThemeToggle>
│   │   └── UserMenu
│   │
│   ├── <DoctorDashboard>
│   │   ├── <StatsCards>             # total patients, alerts, etc.
│   │   ├── <AlertList>
│   │   │   └── <AlertCard> (×N)
│   │   └── <RecentPatientActivity>
│   │
│   ├── <PatientsPage>
│   │   └── <PatientList>
│   │       └── <PatientRow> (×N)
│   │
│   ├── <PatientDetailPage>
│   │   ├── <PatientInfoHeader>
│   │   ├── <SummaryCard>           # AI-generated summary
│   │   ├── <AdherenceOverview>
│   │   │   └── <AdherenceChart>
│   │   ├── <MedicineList>
│   │   ├── <ReportList>
│   │   └── <ChatHistoryView>
│   │
│   └── <AlertManagementPage>
│       ├── <AlertFilters>
│       └── <AlertList>
│           └── <AlertCard> (×N)
│               ├── RiskBadge
│               ├── SymptomsSummary
│               └── AcknowledgeButton
│
└── <Shared>
    ├── <LoadingState>
    ├── <ErrorBoundary>
    ├── <EmptyState>
    └── <ConfirmDialog>
```

---

## 6. BACKEND ARCHITECTURE

### Layered Architecture

```
┌──────────────────────────────────────────────────┐
│                   API Layer                       │
│           (FastAPI routers / controllers)          │
│   - Request validation (Pydantic)                 │
│   - Response formatting                           │
│   - Auth guards (JWT dependency)                  │
└────────────────────┬─────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────┐
│                Service Layer                       │
│           (Business logic / use cases)             │
│   - Orchestrates operations                       │
│   - Calls agents, DB, OCR, RAG                    │
│   - Transaction management                        │
└────────────────────┬─────────────────────────────┘
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
┌──────────────┐ ┌────────┐ ┌──────────────┐
│  Agent Layer │ │ DB     │ │ External     │
│  (LangGraph) │ │ Layer  │ │ Services     │
│              │ │ (SQLA) │ │ (OCR, GPT)   │
│  - Report    │ │        │ │              │
│  - Chat      │ │ Models │ │ - Google     │
│  - Emergency │ │        │ │   Vision     │
│  - Summary   │ │        │ │ - OpenAI     │
│  - Reminder  │ │        │ │ - ChromaDB   │
└──────────────┘ └────────┘ └──────────────┘
```

### Dependency Injection Pattern

```python
# app/api/deps.py

def get_db() -> Generator:
    yield db_session

def get_current_user() -> Patient:
    ...

def get_report_service(db=Depends(get_db)) -> ReportService:
    return ReportService(db)

def get_chat_agent(
    db=Depends(get_db),
    vector_store=Depends(get_vector_store)
) -> PatientChatAgent:
    return PatientChatAgent(db, vector_store)
```

### Middleware Stack

```
Request
  │
  ▼
CORS Middleware
  │
  ▼
Rate Limiting Middleware
  │
  ▼
Auth Middleware (JWT validation on protected routes)
  │
  ▼
Request Logging Middleware
  │
  ▼
Route Handler
  │
  ▼
Error Handler (global exception → structured JSON)
  │
  ▼
Response
```

---

## 7. FRONTEND ARCHITECTURE

### Route Design (Next.js App Router)

```
/                           → Landing page → redirect to login
/login                      → Login form (role select: patient/doctor)
/register                   → Registration form
/
/patient/dashboard          → Patient home
/patient/medicines          → Medicine list + adherence
/patient/reports            → Upload + view reports
/patient/chat               → AI chat
/patient/appointments       → Appointments
/patient/emergency          → Symptom checker
/
/doctor/dashboard           → Doctor home
/doctor/patients            → Patient list
/doctor/patients/[id]       → Patient detail + summary
/doctor/alerts              → Emergency alerts
/doctor/appointments        → Appointments
```

### State Management Strategy (Zustand)

```typescript
// authStore.ts
interface AuthState {
  user: User | null;
  token: string | null;
  role: 'patient' | 'doctor' | null;
  login: (creds) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

// patientStore.ts
interface PatientState {
  medicines: Medicine[];
  reports: Report[];
  adherenceStats: AdherenceStats;
  fetchMedicines: () => Promise<void>;
  fetchReports: () => Promise<void>;
  fetchAdherence: () => Promise<void>;
}

// uiStore.ts
interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  toggleSidebar: () => void;
  toggleTheme: () => void;
}
```

### API Client Pattern (Axios)

```typescript
// lib/api/client.ts
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor: attach JWT
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Response interceptor: handle 401 → refresh or logout
apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      useAuthStore.getState().logout();
    }
    return Promise.reject(err);
  }
);
```

### Data Flow Pattern

```
User Action
    │
    ▼
React Component (e.g., MedicinesPage)
    │ calls hook
    ▼
Custom Hook (useMedicines.ts)
    │ calls store action
    ▼
Zustand Store (patientStore.ts)
    │ calls API
    ▼
API Client (lib/api/medicines.ts)
    │ HTTP fetch
    ▼
FastAPI Backend → Response → Store update → Re-render
```

---

## 8. DEVELOPMENT ROADMAP

### Phase 1 — Foundation (Week 1)

```
Sprint 1.1: Project scaffolding
  ├── Initialize Next.js + Tailwind + shadcn/ui
  ├── Initialize FastAPI + SQLAlchemy + Alembic
  ├── Docker compose (PostgreSQL + app)
  ├── Folder structure as per architecture
  └── Environment variables setup

Sprint 1.2: Database + Auth
  ├── SQLAlchemy models (all tables)
  ├── Alembic migrations
  ├── JWT auth (Patient + Doctor)
  ├── Auth API endpoints
  └── Frontend auth pages (login, register)
```

### Phase 2 — Core Patient Features (Week 2)

```
Sprint 2.1: Report Upload + OCR
  ├── Report upload API (multipart)
  ├── Google Vision OCR integration
  ├── OCR preprocessor
  ├── Report list UI
  └── Upload component with drag & drop

Sprint 2.2: Medical Report Agent
  ├── LangGraph agent for extraction
  ├── OpenAI integration
  ├── Medicine storage
  ├── Patient medicine list UI
  └── Report detail view

Sprint 2.3: Patient Dashboard
  ├── Dashboard layout with sidebar
  ├── Dashboard API (aggregated stats)
  ├── Welcome card, summary cards
  ├── Adherence chart (recharts)
  └── Responsive design
```

### Phase 3 — AI Chat + RAG (Week 3)

```
Sprint 3.1: RAG System
  ├── ChromaDB setup
  ├── Embedding pipeline
  ├── Document ingestion from reports
  └── Retriever service

Sprint 3.2: Patient Chat Agent
  ├── LangGraph chat agent
  ├── Chat API endpoint
  ├── Chat UI with message history
  └── Source citation in responses
```

### Phase 4 — Emergency + Reminders (Week 4)

```
Sprint 4.1: Emergency Detection
  ├── LangGraph emergency agent
  ├── Symptom checker API
  ├── Risk classification UI
  ├── Alert storage
  └── Alert list for doctor

Sprint 4.2: Medicine Reminders
  ├── Reminder agent (background)
  ├── Adherence tracking API
  ├── Adherence log UI
  ├── Statistics computation
  └── Adherence chart (doctor view)
```

### Phase 5 — Doctor Features (Week 5)

```
Sprint 5.1: Doctor Dashboard
  ├── Patient list for doctor
  ├── Patient detail page
  ├── AI summary generation
  ├── Doctor summary agent
  └── Doctor dashboard stats

Sprint 5.2: Appointments
  ├── Appointment CRUD API
  ├── Appointment UI (patient + doctor)
  └── Calendar integration
```

### Phase 6 — Polish + Deploy (Week 6)

```
Sprint 6.1: Testing
  ├── Backend unit tests
  ├── API integration tests
  ├── Agent tests
  └── Frontend component tests

Sprint 6.2: Production Readiness
  ├── Docker optimization
  ├── Vercel deployment (frontend)
  ├── Render deployment (backend)
  ├── Neon PostgreSQL setup
  ├── CI/CD pipelines
  ├── Error monitoring
  └── Documentation
```

---

## 9. MODULE DEPENDENCY GRAPH

```
                    ┌─────────────┐
                    │  Database   │
                    │  (models)   │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                 ▼
    ┌──────────┐    ┌──────────┐    ┌──────────────┐
    │  Auth    │    │ Services │    │    OCR       │
    │  Service │◄──►│  Layer   │◄───│   Service    │
    └──────────┘    └────┬─────┘    └──────────────┘
                         │
          ┌──────────────┼──────────────────┐
          ▼              ▼                   ▼
   ┌───────────┐ ┌────────────┐ ┌──────────────────┐
   │  RAG /    │ │  LangGraph │ │  External APIs   │
   │ ChromaDB  │ │  Agents    │ │  (OpenAI)        │
   └───────────┘ └──────┬─────┘ └──────────────────┘
                        │
          ┌─────────────┼──────────────┐
          ▼             ▼              ▼
   ┌───────────┐ ┌──────────┐ ┌────────────┐
   │  Report   │ │  Chat    │ │  Doctor    │
   │  Agent    │ │  Agent   │ │  Summary   │
   └───────────┘ └──────────┘ └────────────┘
          │             │              │
          ▼             ▼              ▼
   ┌────────────┐ ┌──────────┐ ┌──────────────┐
   │  Reminder  │ │Emergency │ │  API Layer   │
   │  Agent     │ │ Agent    │ │  (routes)    │
   └────────────┘ └──────────┘ └──────┬───────┘
                                      │
                                      ▼
                               ┌──────────────┐
                               │  Frontend    │
                               │  (Next.js)   │
                               └──────────────┘
```

### Dependency Rules

```
1. Models (DB) ← No dependencies on other modules
2. Core (config, security) ← No dependencies on business modules
3. Services ← Depends on: Models, Core, Agents, OCR, RAG
4. Agents ← Depends on: Models, RAG, OpenAI
5. RAG ← Depends on: Models, OpenAI embeddings
6. OCR ← Depends on: Google Vision API
7. API Layer ← Depends on: Services, Core, Schemas
8. Frontend ← Depends on: API Layer (HTTP only)
```

---

## 10. FILE-BY-FILE IMPLEMENTATION ORDER

### Backend Implementation Order (68 files)

```
# ── Step 1: Core Setup ─────────────────────────────────
  1.  backend/requirements.txt
  2.  backend/.env
  3.  backend/app/__init__.py
  4.  backend/app/core/__init__.py
  5.  backend/app/core/config.py
  6.  backend/app/core/database.py
  7.  backend/app/core/security.py
  8.  backend/app/core/exceptions.py
  9.  backend/app/main.py

# ── Step 2: Database Models ───────────────────────────
  10. backend/app/models/__init__.py
  11. backend/app/models/patient.py
  12. backend/app/models/doctor.py
  13. backend/app/models/report.py
  14. backend/app/models/medicine.py
  15. backend/app/models/appointment.py
  16. backend/app/models/chat_history.py
  17. backend/app/models/adherence_log.py
  18. backend/app/models/emergency_alert.py
  19. backend/alembic.ini
  20. backend/alembic/env.py
  21. backend/alembic/versions/001_initial.py

# ── Step 3: Pydantic Schemas ──────────────────────────
  22. backend/app/schemas/__init__.py
  23. backend/app/schemas/auth.py
  24. backend/app/schemas/patient.py
  25. backend/app/schemas/doctor.py
  26. backend/app/schemas/medicine.py
  27. backend/app/schemas/report.py
  28. backend/app/schemas/chat.py
  29. backend/app/schemas/adherence.py
  30. backend/app/schemas/emergency.py
  31. backend/app/schemas/summary.py

# ── Step 4: Auth Service + API ────────────────────────
  32. backend/app/services/__init__.py
  33. backend/app/services/auth_service.py
  34. backend/app/api/__init__.py
  35. backend/app/api/deps.py
  36. backend/app/api/v1/__init__.py
  37. backend/app/api/v1/auth.py
  38. backend/app/api/v1/router.py

# ── Step 5: Patient & Doctor Services ─────────────────
  39. backend/app/services/patient_service.py
  40. backend/app/services/medicine_service.py
  41. backend/app/api/v1/patients.py
  42. backend/app/api/v1/doctors.py
  43. backend/app/api/v1/medicines.py

# ── Step 6: OCR Service ────────────────────────────────
  44. backend/app/ocr/__init__.py
  45. backend/app/ocr/google_vision.py
  46. backend/app/ocr/preprocessor.py

# ── Step 7: Report Service + API ──────────────────────
  47. backend/app/services/report_service.py
  48. backend/app/api/v1/reports.py

# ── Step 8: RAG System ────────────────────────────────
  49. backend/app/rag/__init__.py
  50. backend/app/rag/embeddings.py
  51. backend/app/rag/vector_store.py
  52. backend/app/rag/retriever.py

# ── Step 9: LangGraph Agents ──────────────────────────
  53. backend/app/agents/__init__.py
  54. backend/app/agents/medical_report_agent/state.py
  55. backend/app/agents/medical_report_agent/prompts.py
  56. backend/app/agents/medical_report_agent/nodes.py
  57. backend/app/agents/medical_report_agent/graph.py
  58. backend/app/agents/patient_chat_agent/state.py
  59. backend/app/agents/patient_chat_agent/prompts.py
  60. backend/app/agents/patient_chat_agent/nodes.py
  61. backend/app/agents/patient_chat_agent/graph.py
  62. backend/app/agents/emergency_agent/state.py
  63. backend/app/agents/emergency_agent/prompts.py
  64. backend/app/agents/emergency_agent/nodes.py
  65. backend/app/agents/emergency_agent/graph.py
  66. backend/app/agents/doctor_summary_agent/state.py
  67. backend/app/agents/doctor_summary_agent/prompts.py
  68. backend/app/agents/doctor_summary_agent/nodes.py
  69. backend/app/agents/doctor_summary_agent/graph.py
  70. backend/app/agents/reminder_agent/state.py
  71. backend/app/agents/reminder_agent/prompts.py
  72. backend/app/agents/reminder_agent/nodes.py
  73. backend/app/agents/reminder_agent/graph.py
  74. backend/app/agents/orchestrator.py

# ── Step 10: Remaining Services + APIs ────────────────
  75. backend/app/services/chat_service.py
  76. backend/app/services/adherence_service.py
  77. backend/app/services/emergency_service.py
  78. backend/app/services/summary_service.py
  79. backend/app/api/v1/chat.py
  80. backend/app/api/v1/adherence.py
  81. backend/app/api/v1/emergency.py
  82. backend/app/api/v1/summaries.py
  83. backend/app/api/v1/appointments.py

# ── Step 11: Background Tasks ─────────────────────────
  84. backend/app/tasks/__init__.py
  85. backend/app/tasks/reminder_scheduler.py
  86. backend/app/tasks/adherence_monitor.py

# ── Step 12: Tests ────────────────────────────────────
  87. backend/tests/conftest.py
  88. backend/tests/test_api/test_auth.py
  89. backend/tests/test_api/test_reports.py
  90. backend/tests/test_api/test_chat.py
  91. backend/tests/test_services/test_auth_service.py
  92. backend/tests/test_agents/test_report_agent.py
  (remaining test files...)

# ── Step 13: Docker ───────────────────────────────────
  93. backend/Dockerfile
  94. docker/docker-compose.yml
  95. docker/docker-compose.dev.yml
  96. docker/postgres/init.sql
```

### Frontend Implementation Order (60+ files)

```
# ── Step 1: Project Setup ─────────────────────────────
  1.  frontend/package.json
  2.  frontend/next.config.js
  3.  frontend/tsconfig.json
  4.  frontend/tailwind.config.ts
  5.  frontend/components.json
  6.  frontend/.env.local
  7.  frontend/src/app/layout.tsx
  8.  frontend/src/app/page.tsx

# ── Step 2: shadcn/ui Components ─────────────────────
  9.  frontend/src/components/ui/button.tsx
  10. frontend/src/components/ui/input.tsx
  11. frontend/src/components/ui/card.tsx
  12. frontend/src/components/ui/avatar.tsx
  13. frontend/src/components/ui/badge.tsx
  14. frontend/src/components/ui/dialog.tsx
  15. frontend/src/components/ui/select.tsx
  16. frontend/src/components/ui/table.tsx
  17. frontend/src/components/ui/tabs.tsx
  18. frontend/src/components/ui/toast.tsx
  19. frontend/src/components/ui/dropdown-menu.tsx
  20. frontend/src/components/ui/skeleton.tsx
  21. frontend/src/lib/utils.ts (cn utility)

# ── Step 3: Types ─────────────────────────────────────
  22. frontend/src/types/auth.ts
  23. frontend/src/types/patient.ts
  24. frontend/src/types/medicine.ts
  25. frontend/src/types/report.ts
  26. frontend/src/types/chat.ts
  27. frontend/src/types/doctor.ts

# ── Step 4: API Client ────────────────────────────────
  28. frontend/src/lib/api/client.ts
  29. frontend/src/lib/api/auth.ts
  30. frontend/src/lib/api/patients.ts
  31. frontend/src/lib/api/medicines.ts
  32. frontend/src/lib/api/reports.ts
  33. frontend/src/lib/api/chat.ts
  34. frontend/src/lib/api/doctor.ts

# ── Step 5: Zustand Stores ───────────────────────────
  35. frontend/src/lib/store/authStore.ts
  36. frontend/src/lib/store/patientStore.ts
  37. frontend/src/lib/store/uiStore.ts

# ── Step 6: Auth UI ──────────────────────────────────
  38. frontend/src/middleware.ts
  39. frontend/src/app/(auth)/layout.tsx
  40. frontend/src/app/(auth)/login/page.tsx
  41. frontend/src/app/(auth)/register/page.tsx
  42. frontend/src/components/auth/LoginForm.tsx
  43. frontend/src/components/auth/RegisterForm.tsx
  44. frontend/src/lib/schemas/auth.ts

# ── Step 7: Shared Layout Components ──────────────────
  45. frontend/src/components/shared/Header.tsx
  46. frontend/src/components/shared/Sidebar.tsx
  47. frontend/src/components/shared/ThemeToggle.tsx
  48. frontend/src/components/shared/LoadingState.tsx

# ── Step 8: Patient Dashboard ─────────────────────────
  49. frontend/src/app/(patient)/layout.tsx
  50. frontend/src/app/(patient)/dashboard/page.tsx
  51. frontend/src/components/patient/MedicineCard.tsx
  52. frontend/src/components/patient/AdherenceChart.tsx

# ── Step 9: Reports UI ───────────────────────────────
  53. frontend/src/app/(patient)/reports/page.tsx
  54. frontend/src/components/patient/ReportUpload.tsx
  55. frontend/src/lib/schemas/report.ts

# ── Step 10: Medicines UI ─────────────────────────────
  56. frontend/src/app/(patient)/medicines/page.tsx

# ── Step 11: Chat UI ──────────────────────────────────
  57. frontend/src/app/(patient)/chat/page.tsx
  58. frontend/src/components/patient/ChatWindow.tsx
  59. frontend/src/lib/hooks/useChat.ts

# ── Step 12: Emergency UI ─────────────────────────────
  60. frontend/src/app/(patient)/emergency/page.tsx
  61. frontend/src/components/emergency/SymptomChecker.tsx
  62. frontend/src/lib/schemas/symptom.ts

# ── Step 13: Appointments UI ──────────────────────────
  63. frontend/src/app/(patient)/appointments/page.tsx

# ── Step 14: Doctor UI ────────────────────────────────
  64. frontend/src/app/(doctor)/layout.tsx
  65. frontend/src/app/(doctor)/dashboard/page.tsx
  66. frontend/src/app/(doctor)/patients/page.tsx
  67. frontend/src/app/(doctor)/patients/[id]/page.tsx
  68. frontend/src/app/(doctor)/alerts/page.tsx
  69. frontend/src/app/(doctor)/appointments/page.tsx
  70. frontend/src/components/doctor/PatientList.tsx
  71. frontend/src/components/doctor/PatientDetail.tsx
  72. frontend/src/components/doctor/SummaryCard.tsx
  73. frontend/src/components/doctor/AdherenceOverview.tsx
```

### Total File Count

```
Backend:    ~96 files
Frontend:   ~73 files
Infra:      ~5 files
Total:      ~174 files
across ~6 weeks of development
```

---

## IMPLEMENTATION STRATEGY SUMMARY

| Dimension | Decision | Rationale |
|-----------|----------|-----------|
| **Monorepo** | Single repo, two directories | Simple dev setup, shared CI |
| **API versioning** | `/api/v1/` prefix | Allows future breaking changes |
| **Auth** | JWT access + refresh tokens | Stateless, scalable |
| **State management** | Zustand (not Redux) | Minimal boilerplate, TypeScript native |
| **LangGraph** | Each agent in own package | Clean separation, testable |
| **RAG** | ChromaDB (in-process) | Simple, no separate server needed |
| **OCR** | Google Vision (paid) | Best accuracy for medical text |
| **Async** | FastAPI async endpoints | Non-blocking I/O for AI calls |
| **ORM** | SQLAlchemy 2.0 | Mature, async support, Alembic |
| **Background tasks** | APScheduler | Lightweight, no need for Celery in MVP |
| **File storage** | Local (MVP) → S3 (prod) | Iterative, swap storage backend later |
| **Testing** | pytest (backend), Vitest (frontend) | Industry standard |

---

## 16. CLINICAL VALIDATION PIPELINE

**Status:** ✅ Implemented (Phase M — v0.17.0)

Files: `app/validation/` (21 files across 4 sub-modules)

### Dataset Management (`app/validation/dataset/`)

| Module | Responsibility |
|--------|---------------|
| `ground_truth.py` | `GroundTruth`, `GroundTruthEntry`, `GroundTruthSet` — 10 document types (Prescription, CBC, Lipid, Thyroid, Kidney, Liver, Diabetes, Radiology, Discharge Summary, Clinical Notes), 4 difficulty levels, 10 question categories |
| `dataset_loader.py` | `DatasetLoader` — JSON/JSONL load/save, directory batch loading, format versioning |
| `dataset_manager.py` | `DatasetManager` — CRUD operations, import/export, stats, caching |
| `dataset_validator.py` | `DatasetValidator`, `ValidationResult` — structural integrity checks |
| `dataset_splitter.py` | `DatasetSplitter` — train/val/test splits (entry-level and document-level) |
| `fixtures/sample_golden_qa.json` | Sample benchmark dataset with 3 document types (CBC, Lipid, Prescription) |

### Benchmark System (`app/validation/benchmark/`)

| Module | Responsibility |
|--------|---------------|
| `benchmark_config.py` | `BenchmarkConfig` — configurable top_k, k_values, warmup runs, measurements |
| `benchmark_metrics.py` | `BenchmarkMetrics` — retrieval_recall, precision@k, MRR, NDCG, citation precision/recall/F1, groundedness, hallucination_rate, answer_relevance, statistical utilities |
| `benchmark_runner.py` | `BenchmarkRunner` — warmup + multi-run benchmark execution with latency/memory/token tracking |
| `benchmark_suite.py` | `BenchmarkSuite`, `BenchmarkResult` — result aggregation and comparison |
| `benchmark_history.py` | `BenchmarkHistory` — persistent result storage, comparison, regression detection |

### Optimization Module (`app/validation/optimization/`)

| Module | Responsibility |
|--------|---------------|
| `chunk_optimizer.py` | `ChunkOptimizer` — grid search over chunk_size (128-2048), chunk_overlap (0-128), strategies (fixed, recursive, semantic, sentence) |
| `prompt_optimizer.py` | `PromptOptimizer` — variant registration, weighted scoring (relevance × 0.4 + groundedness × 0.4 + hallucination × 0.2) |
| `retrieval_optimizer.py` | `RetrievalOptimizer` — grid search over top_k (3-20), similarity_threshold (0.5-0.8), rerank, hybrid, MMR |
| `reranking_optimizer.py` | `RerankingOptimizer` — 5 strategies (score, diversity, hybrid, section_boosted, recency), configurable final_k and penalties |

### Evaluation Suite (`app/validation/evaluation/`)

| Module | Responsibility |
|--------|---------------|
| `clinical_test_runner.py` | `ClinicalTestRunner`, `ClinicalTestCase`, `ClinicalTestResult`, `ClinicalTestSummary` — per-question evaluation with answer matching, citation scoring, difficulty/category breakdown |
| `regression_suite.py` | `RegressionSuite`, `RegressionThresholds`, `RegressionResult` — automated quality gates (latency, recall, hallucination, citation precision/recall, groundedness, relevance, token usage) |
| `report_generator.py` | `ReportGenerator` — validation, benchmark, regression, optimization reports + performance dashboard JSON |
| `statistics.py` | `Statistics` — confusion matrix, accuracy, precision/recall/F1, McNemar test, confidence intervals |

### Pipeline Flow

```
Dataset (JSON/JSONL)
    │
    ├── DatasetValidator.validate() → ValidationResult
    │
    ├── DatasetSplitter.split() → train/val/test
    │
    ├── BenchmarkRunner.run(questions, answer_fn)
    │       │
    │       ├── For each question:
    │       │     ├── measure latency
    │       │     ├── call answer_fn → response
    │       │     ├── measure memory
    │       │     ├── measure tokens
    │       │     ├── score citations vs expected
    │       │     └── compare with ground_truth_fn
    │       │
    │       └── Aggregate → BenchmarkResult
    │
    ├── ClinicalTestRunner.run(dataset, answer_fn)
    │       └── Per-entry: answer_match + citation_score → ClinicalTestSummary
    │
    ├── RegressionSuite.run(benchmark_result)
    │       └── Check all thresholds → RegressionResult (PASS/FAIL)
    │
    ├── Optimizers (Chunk/Prompt/Retrieval/Reranking)
    │       └── Grid search → best_config + top_n
    │
    └── ReportGenerator
            └── VALIDATION_REPORT.md, BENCHMARK_SUMMARY.md,
                REGRESSION_REPORT.md, OPTIMIZATION_REPORT.md,
                PERFORMANCE_DASHBOARD.json
```

### Supported Metrics

| Metric | Description |
|--------|-------------|
| Retrieval Recall | Fraction of relevant documents retrieved |
| Precision@K | Precision in top-K results |
| MRR | Mean Reciprocal Rank |
| NDCG | Normalized Discounted Cumulative Gain |
| Citation Precision | Fraction of correct citations |
| Citation Recall | Fraction of expected citations covered |
| Groundedness | Fraction of claims supported by evidence |
| Answer Relevance | Fraction of answers that address the question |
| Hallucination Rate | Fraction of unsupported claims |
| Latency (ms) | P50, P95, P99, mean, min, max, std_dev |
| Memory Usage (MB) | Peak and mean memory |
| Token Usage | Mean, total, min, max |

### 110 Validation Tests — All Passing

- Dataset loader (7), manager (10), splitter (6), validator (9), ground truth (14)
- Benchmark metrics (12), runner (7), suite (6), history (7)
- Clinical test runner (8), optimizers (13)
- **Total: 110 tests — all passing, zero regressions**

---

## NEXT STEPS

Ready to begin implementation when you confirm.

The recommended starting point:

**Phase 1, Sprint 1.1** — Project scaffolding:

1. `backend/` — FastAPI + SQLAlchemy + config + main.py
2. `frontend/` — Next.js + Tailwind + shadcn/ui setup
3. `docker/` — Docker compose with PostgreSQL
4. Environment variables and base configuration

Shall I proceed with Phase 1, Sprint 1.1?
