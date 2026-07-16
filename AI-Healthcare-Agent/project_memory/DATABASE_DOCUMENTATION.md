# Database Documentation

> PostgreSQL 16 database schema for the AI Healthcare Follow-up Assistant.
> **Last updated:** 2026-07-14 (Sprint 3B - Production Data Layer)

---

## Connection

| Property | Value |
|----------|-------|
| Engine | PostgreSQL 16 |
| Host | localhost (dev) / Neon (production) |
| Port | 5432 |
| Database | healthcare_agent |
| User | healthcare_user |
| ORM | SQLAlchemy 2.0 + asyncpg |
| Migrations | Alembic 1.14 |
| Migration Revision | `0001` (initial_schema) |

---

## Tables (10 total)

### patients

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default `gen_random_uuid()` |
| email | VARCHAR(255) | **UNIQUE**, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL |
| full_name | VARCHAR(255) | NOT NULL |
| phone | VARCHAR(50) | NULLABLE |
| date_of_birth | DATE | NULLABLE |
| gender | VARCHAR(20) | NULLABLE |
| blood_group | VARCHAR(10) | NULLABLE |
| address | TEXT | NULLABLE |
| emergency_contact | VARCHAR(255) | NULLABLE |
| emergency_phone | VARCHAR(50) | NULLABLE |
| terms_accepted | BOOLEAN | DEFAULT FALSE, NOT NULL |
| terms_accepted_at | TIMESTAMPTZ | NULLABLE |
| is_active | BOOLEAN | DEFAULT TRUE, NOT NULL |
| deleted_at | TIMESTAMPTZ | NULLABLE |
| deleted_by | VARCHAR(255) | NULLABLE |
| created_at | TIMESTAMPTZ | DEFAULT NOW(), NOT NULL |
| updated_at | TIMESTAMPTZ | DEFAULT NOW(), NOT NULL (auto-update trigger) |

**Indexes:** `email` (unique), `(is_active, created_at)`

**Relationships (all cascade delete):**
- Has many `reports`
- Has many `medicines`
- Has many `chat_history`
- Has many `adherence_logs`
- Has many `emergency_alerts`
- Has many `appointments`
- Has many `patient_doctors`

---

### doctors

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default `gen_random_uuid()` |
| email | VARCHAR(255) | **UNIQUE**, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL |
| full_name | VARCHAR(255) | NOT NULL |
| specialization | VARCHAR(255) | NULLABLE |
| license_number | VARCHAR(100) | NULLABLE |
| phone | VARCHAR(50) | NULLABLE |
| hospital_name | VARCHAR(255) | NULLABLE |
| years_of_experience | INTEGER | NULLABLE |
| is_active | BOOLEAN | DEFAULT TRUE, NOT NULL |
| deleted_at | TIMESTAMPTZ | NULLABLE |
| deleted_by | VARCHAR(255) | NULLABLE |
| created_at | TIMESTAMPTZ | DEFAULT NOW(), NOT NULL |
| updated_at | TIMESTAMPTZ | DEFAULT NOW(), NOT NULL (auto-update trigger) |

**Indexes:** `email` (unique), `specialization`, `(is_active, created_at)`

**Relationships:**
- Has many `appointments` (cascade delete)
- Has many `patient_doctors` (cascade delete)
- Has many `emergency_alerts` (acknowledged_by, SET NULL on delete)

---

### patient_doctors

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default `gen_random_uuid()` |
| patient_id | UUID | FK → `patients.id`, ON DELETE CASCADE, INDEX |
| doctor_id | UUID | FK → `doctors.id`, ON DELETE CASCADE, INDEX |
| is_active | BOOLEAN | DEFAULT TRUE, NOT NULL |
| deleted_at | TIMESTAMPTZ | NULLABLE |
| deleted_by | VARCHAR(255) | NULLABLE |
| created_at | TIMESTAMPTZ | DEFAULT NOW(), NOT NULL |
| updated_at | TIMESTAMPTZ | DEFAULT NOW(), NOT NULL (auto-update trigger) |

**Constraints:** UNIQUE(patient_id, doctor_id)

---

### refresh_tokens

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default `gen_random_uuid()` |
| jti | VARCHAR(255) | **UNIQUE**, NOT NULL |
| token_hash | VARCHAR(255) | NOT NULL |
| user_id | UUID | NOT NULL, INDEX (polymorphic, no FK) |
| role | VARCHAR(50) | NOT NULL |
| device_info | TEXT | NULLABLE |
| ip_address | VARCHAR(45) | NULLABLE |
| is_revoked | BOOLEAN | DEFAULT FALSE, NOT NULL |
| revoked_at | TIMESTAMPTZ | NULLABLE |
| expires_at | TIMESTAMPTZ | NOT NULL |
| created_at | TIMESTAMPTZ | DEFAULT NOW(), NOT NULL |
| updated_at | TIMESTAMPTZ | DEFAULT NOW(), NOT NULL (auto-update trigger) |

**Indexes:** `jti` (unique), `(user_id, is_revoked)`, `(expires_at)`

> **Design note:** No FK constraint on `user_id` — polymorphic reference to patients/doctors.
> Application-level validation ensures consistency. FK omitted deliberately.

---

### reports

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default `gen_random_uuid()` |
| patient_id | UUID | FK → `patients.id`, ON DELETE CASCADE |
| doctor_id | UUID | FK → `doctors.id`, **ON DELETE SET NULL**, NULLABLE |
| title | VARCHAR(255) | NULLABLE |
| file_path | VARCHAR(500) | NOT NULL |
| file_type | VARCHAR(50) | NULLABLE |
| file_size | INTEGER | NULLABLE |
| original_filename | VARCHAR(255) | NULLABLE |
| ocr_text | TEXT | NULLABLE |
| extracted_data | JSON | NULLABLE |
| status | VARCHAR(20) | DEFAULT 'pending', NOT NULL |
| error_message | TEXT | NULLABLE |
| uploaded_at | TIMESTAMPTZ | NOT NULL |
| processed_at | TIMESTAMPTZ | NULLABLE |
| created_at | TIMESTAMPTZ | DEFAULT NOW(), NOT NULL |
| updated_at | TIMESTAMPTZ | DEFAULT NOW(), NOT NULL (auto-update trigger) |

**Indexes:** `patient_id`, `(patient_id, status)`, `(status, uploaded_at)`

**Relationships:**
- Belongs to `patient`
- Belongs to `doctor` (optional, SET NULL on doctor delete)
- Has many `medicines` (cascade delete)

---

### medicines

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default `gen_random_uuid()` |
| report_id | UUID | FK → `reports.id`, ON DELETE CASCADE |
| patient_id | UUID | FK → `patients.id`, ON DELETE CASCADE |
| name | VARCHAR(255) | NOT NULL |
| dosage | VARCHAR(100) | NULLABLE |
| frequency | VARCHAR(255) | NULLABLE |
| duration | VARCHAR(100) | NULLABLE |
| route | VARCHAR(20) | NULLABLE |
| instructions | TEXT | NULLABLE |
| start_date | DATE | NULLABLE |
| end_date | DATE | NULLABLE |
| is_active | BOOLEAN | DEFAULT TRUE, NOT NULL |
| deleted_at | TIMESTAMPTZ | NULLABLE |
| deleted_by | VARCHAR(255) | NULLABLE |
| created_at | TIMESTAMPTZ | DEFAULT NOW(), NOT NULL |
| updated_at | TIMESTAMPTZ | DEFAULT NOW(), NOT NULL (auto-update trigger) |

**Indexes:** `(patient_id, is_active)`
**Check Constraints:** `end_date >= start_date` (when both set)

**Relationships:**
- Belongs to `report`
- Belongs to `patient`
- Has many `adherence_logs` (cascade delete)

---

### appointments

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default `gen_random_uuid()` |
| patient_id | UUID | FK → `patients.id`, ON DELETE CASCADE |
| doctor_id | UUID | FK → `doctors.id`, ON DELETE CASCADE |
| title | VARCHAR(255) | NULLABLE |
| description | TEXT | NULLABLE |
| scheduled_at | TIMESTAMPTZ | NOT NULL |
| status | VARCHAR(20) | DEFAULT 'scheduled', NOT NULL |
| follow_up_notes | TEXT | NULLABLE |
| cancelled_at | TIMESTAMPTZ | NULLABLE |
| is_active | BOOLEAN | DEFAULT TRUE, NOT NULL |
| deleted_at | TIMESTAMPTZ | NULLABLE |
| deleted_by | VARCHAR(255) | NULLABLE |
| created_at | TIMESTAMPTZ | DEFAULT NOW(), NOT NULL |
| updated_at | TIMESTAMPTZ | DEFAULT NOW(), NOT NULL (auto-update trigger) |

**Indexes:** `patient_id`, `doctor_id`, `(doctor_id, scheduled_at)`, `(patient_id, status)`, `(status, scheduled_at)`

**Relationships:**
- Belongs to `patient`
- Belongs to `doctor`

---

### chat_history

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default `gen_random_uuid()` |
| patient_id | UUID | FK → `patients.id`, ON DELETE CASCADE |
| role | VARCHAR(20) | NOT NULL ('user' or 'assistant') |
| message | TEXT | NOT NULL |
| metadata | JSON | NULLABLE |
| created_at | TIMESTAMPTZ | DEFAULT NOW(), NOT NULL |
| updated_at | TIMESTAMPTZ | DEFAULT NOW(), NOT NULL (auto-update trigger) |

**Indexes:** `(patient_id, created_at)`
**Check Constraints:** `length(message) <= 100000`

**Relationships:**
- Belongs to `patient`

---

### adherence_logs

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default `gen_random_uuid()` |
| medicine_id | UUID | FK → `medicines.id`, ON DELETE CASCADE |
| patient_id | UUID | FK → `patients.id`, ON DELETE CASCADE |
| scheduled_time | TIMESTAMPTZ | NOT NULL |
| taken_at | TIMESTAMPTZ | NULLABLE |
| status | VARCHAR(20) | DEFAULT 'pending', NOT NULL |
| notes | TEXT | NULLABLE |
| created_at | TIMESTAMPTZ | DEFAULT NOW(), NOT NULL |
| updated_at | TIMESTAMPTZ | DEFAULT NOW(), NOT NULL (auto-update trigger) |

**Indexes:** `(patient_id, status)`, `(scheduled_time)`
**Check Constraints:** `taken_at >= scheduled_time` (when both set)

**Relationships:**
- Belongs to `medicine`
- Belongs to `patient`

---

### emergency_alerts

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default `gen_random_uuid()` |
| patient_id | UUID | FK → `patients.id`, ON DELETE CASCADE |
| risk_level | VARCHAR(20) | NOT NULL |
| symptoms | TEXT | NOT NULL |
| analysis | TEXT | NULLABLE |
| is_acknowledged | BOOLEAN | DEFAULT FALSE, NOT NULL |
| acknowledged_by | UUID | FK → `doctors.id`, **ON DELETE SET NULL**, NULLABLE |
| resolved_at | TIMESTAMPTZ | NULLABLE |
| created_at | TIMESTAMPTZ | DEFAULT NOW(), NOT NULL |
| updated_at | TIMESTAMPTZ | DEFAULT NOW(), NOT NULL (auto-update trigger) |

**Indexes:** `(patient_id, created_at)`, `(risk_level, is_acknowledged)`
**Check Constraints:** `resolved_at >= created_at` (when both set)

**Relationships:**
- Belongs to `patient`
- Belongs to `doctor` (acknowledger, SET NULL on doctor delete)

---

## Entity Relationship Diagram

```
┌───────────┐       ┌──────────────────┐       ┌───────────┐
│  patients │───<── │ patient_doctors  │ ──>───│  doctors  │
└───────────┘       └──────────────────┘       └───────────┘
      │                                                │
      ├──<── reports ──>── medicines                   │
      │                       │                        │
      ├──<── chat_history     │                        │
      │                       │                        │
      ├──<── adherence_logs ──┘                        │
      │                                                │
      ├──<── emergency_alerts ──>── (SET NULL on del)──┘
      │
      └──<── appointments ──>─── (doctor) ────────────┘

┌──────────────────┐
│  refresh_tokens  │  (standalone, polymorphic user_id, no FK)
└──────────────────┘
```

---

## Composite Indexes (19 total)

| Index | Table | Columns | Purpose |
|-------|-------|---------|---------|
| `ix_patients_active_created` | patients | is_active, created_at | Active patient listing |
| `ix_doctors_specialization` | doctors | specialization | Filter by specialty |
| `ix_doctors_active_created` | doctors | is_active, created_at | Active doctor listing |
| `ix_refresh_tokens_user_revoked` | refresh_tokens | user_id, is_revoked | Find valid tokens for user |
| `ix_refresh_tokens_expires` | refresh_tokens | expires_at | Expired token cleanup |
| `ix_appointments_doctor_scheduled` | appointments | doctor_id, scheduled_at | Doctor's upcoming appointments |
| `ix_appointments_patient_status` | appointments | patient_id, status | Patient's appointments by status |
| `ix_appointments_status_scheduled` | appointments | status, scheduled_at | Time-based status queries |
| `ix_medicines_patient_active` | medicines | patient_id, is_active | Active medication list |
| `ix_reports_patient_status` | reports | patient_id, status | Patient's reports by status |
| `ix_reports_status_uploaded` | reports | status, uploaded_at | Pending report processing |
| `ix_chat_history_patient_created` | chat_history | patient_id, created_at | Chat history timeline |
| `ix_adherence_logs_patient_status` | adherence_logs | patient_id, status | Adherence by status |
| `ix_adherence_logs_scheduled` | adherence_logs | scheduled_time | Time-based adherence queries |
| `ix_emergency_alerts_patient_created` | emergency_alerts | patient_id, created_at | Patient alert timeline |
| `ix_emergency_alerts_risk_acknowledged` | emergency_alerts | risk_level, is_acknowledged | Unacknowledged high-risk alerts |

---

## Check Constraints (5 total)

| Name | Table | Constraint |
|------|-------|-----------|
| `ck_medicine_date_range` | medicines | `end_date >= start_date` (when both set) |
| `ck_chat_message_length` | chat_history | `length(message) <= 100000` |
| `ck_adherence_taken_after_scheduled` | adherence_logs | `taken_at >= scheduled_time` (when both set) |
| `ck_emergency_resolved_after_created` | emergency_alerts | `resolved_at >= created_at` (when both set) |

---

## Database Triggers

Every table has an `updated_at` auto-update trigger:

- **Trigger:** `trg_{table}_updated_at` BEFORE UPDATE
- **Function:** Updates `updated_at` column to `NOW()` on row modification
- **Coverage:** All 10 tables

---

## Seed Data

The `SeedData` class (`app/core/seed.py`) provides comprehensive development/test data:

| Entity | Records | Details |
|--------|---------|---------|
| Patients | 3 | Alice (Cardiology), Bob (Cardiology), Carol (Internal Med) |
| Doctors | 3 | System Admin, Dr. Sarah Chen (Cardiology), Dr. Mike Patel (Internal Med) |
| Assignments | 3 | Patient-Doctor mappings |
| Reports | 3 | Blood work, chest X-Ray, lipid panel |
| Medicines | 3 | Lisinopril, Atorvastatin, Metformin |
| Appointments | 5 | Past and upcoming appointments |
| Chat Messages | 6 | Realistic patient-assistant conversation |
| Adherence Logs | 5 | Mix of taken and missed doses |
| Emergency Alerts | 2 | High-risk (unacknowledged), low-risk (acknowledged) |

Run with: `DatabaseReset(db).seed_data()`

---

## Health Checks

The `DatabaseHealthChecker` (`app/core/health.py`) provides:

- Connection latency measurement
- Table existence verification
- Migration revision checking
- Connection pool statistics (PostgreSQL only)
- Index count verification (PostgreSQL only)
- Table size details (PostgreSQL only)

Health endpoint: `GET /api/v1/health`
Details endpoint: `GET /api/v1/health/details`

---

## Backup Strategy

The `BackupManager` (`app/core/backup.py`) provides:

- `pg_dump` based backup creation
- Backup verification (validates file header)
- Automatic cleanup of backups older than retention period
- 30-day default retention
- Restore with error checking
- List backups with size/date info

---

## N+1 Query Prevention

The `QueryOptimizer` (`app/database/query_optimizer.py`) provides:

- Eager-loading strategies per model
- `paginate_with_optimization()` with automatic `selectinload`
- Predefined relationship paths for all 10 models
- Use `QueryOptimizer.apply_eager_loading()` or `paginate_with_optimization()`

---

## Migration History

| Migration ID | Description | Date | Status |
|-------------|-------------|------|--------|
| `0001` | Initial schema — all 10 tables, 19 indexes, 4 check constraints, auto-update triggers | 2026-07-14 | ✅ Current |

---

## Sprint 3B Improvements

The following improvements were implemented in Sprint 3B (Production Data Layer):

1. **Migration synced with models** — All columns, indexes, constraints, FKs now match SQLAlchemy model definitions
2. **Composite indexes** — 16 query-optimized composite indexes across all tables
3. **Check constraints** — 4 data integrity constraints enforced at DB level
4. **Auto-update triggers** — All tables auto-update `updated_at` on row modification
5. **Seed data** — Realistic test data across all 10 tables (30+ records)
6. **Health checks** — Comprehensive health checking with table/index verification
7. **Backup manager** — Backup creation, verification, restore, and retention cleanup
8. **N+1 prevention** — `QueryOptimizer` with eager-loading strategies for all models
9. **Integration tests** — 60+ tests covering models, relationships, constraints, pagination, filtering, sorting, N+1, seed, health, reset, soft delete
10. **Polymorphic FK pattern** — `refresh_tokens.user_id` documented as intentional no-FK design
