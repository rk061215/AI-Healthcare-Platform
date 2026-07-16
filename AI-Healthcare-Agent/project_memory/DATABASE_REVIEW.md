# Production Database Review — Sprint 3B Preparation

**Review Date:** 2026-07-11
**Reviewer:** Automated audit
**Status:** Draft — awaiting approval before Sprint 3B

> This document reviews every table, relationship, constraint, and strategy in the database layer.
> It identifies gaps between current implementation and production requirements.
> No code modifications have been made.

---

## Table of Contents

- [Scope and Methodology](#scope-and-methodology)
- [Table-by-Table Review](#table-by-table-review)
  - [patients](#1-patients)
  - [doctors](#2-doctors)
  - [patient_doctors](#3-patient_doctors)
  - [refresh_tokens](#4-refresh_tokens)
  - [reports](#5-reports)
  - [medicines](#6-medicines)
  - [appointments](#7-appointments)
  - [chat_history](#8-chat_history)
  - [adherence_logs](#9-adherence_logs)
  - [emergency_alerts](#10-emergency_alerts)
- [Cross-Cutting Concerns](#cross-cutting-concerns)
  - [UUID Strategy](#uuid-strategy)
  - [Timestamp Strategy](#timestamp-strategy)
  - [Soft Delete Strategy](#soft-delete-strategy)
  - [Audit Strategy](#audit-strategy)
  - [Backup Strategy](#backup-strategy)
  - [Partitioning Strategy](#partitioning-strategy)
  - [Enum Usage](#enum-usage)
- [Documentation Gaps](#documentation-gaps)
- [Summary of Issues](#summary-of-issues)
- [Recommended Improvements](#recommended-improvements)

---

## Scope and Methodology

### What was reviewed

- 10 SQLAlchemy model files in `backend/app/models/`
- 1 base model file (`backend/app/database/base.py`)
- 1 session/engine file (`backend/app/database/session.py`)
- 1 migration file (`backend/alembic/versions/0001_initial_schema.py`)
- 1 supported document (`project_memory/DATABASE_DOCUMENTATION.md`)
- All relationships, cascade rules, indexes, constraints, and type choices

### What was NOT reviewed

- Actual PostgreSQL database (no live instance — migrations never applied)
- Query performance (no query plan analysis)
- Production data volume testing
- Connection pool tuning under load

---

## Table-by-Table Review

### 1. patients

| Aspect | Current State | Assessment |
|--------|--------------|------------|
| Table name | `patients` | ✅ Standard plural |
| PK | `id` UUID via `UUIDMixin` | ✅ |
| Unique constraints | `email` (unique=True, index=True) | ✅ |
| Indexes | `email` only | ⚠️ Missing composite indexes for common queries |
| Nullable columns | phone, date_of_birth, gender, blood_group, address, emergency_contact, emergency_phone, terms_accepted_at | ✅ Appropriate for optional PII |
| Non-nullable | email, password_hash, full_name, is_active, terms_accepted | ✅ |
| Defaults | is_active=True, terms_accepted=False | ✅ |
| Timestamps | created_at, updated_at via `TimestampMixin` | ✅ |
| Cascade rules | all, delete-orphan on 7 children | ⚠️ See below |
| Soft delete | `is_active` boolean (no `deleted_at`, no filter) | ⚠️ Partial |
| Audit | None beyond timestamps | ⚠️ Missing |

#### Issues

1. **CASCADE on all 7 children**: Deleting a patient cascade-deletes reports, medicines, chat_history, adherence_logs, emergency_alerts, appointments, and doctor_assignments. In a production healthcare system, **hard deletion of patient records may violate regulatory requirements** (HIPAA, GDPR). Even test/deprecated patients may need retention.

2. **No `deleted_at`**: Without a timestamp, cannot distinguish "never deleted" from "deleted but not filtered."

3. **No composite indexes**: Common queries like `WHERE is_active = true AND created_at >= '2026-01-01'` will scan without a composite index.

---

### 2. doctors

| Aspect | Current State | Assessment |
|--------|--------------|------------|
| Table name | `doctors` | ✅ Standard plural |
| PK | `id` UUID via `UUIDMixin` | ✅ |
| Unique constraints | `email` (unique=True, index=True) | ✅ |
| Indexes | `email` only | ⚠️ Missing specialization index |
| Nullable columns | specialization, license_number, phone, hospital_name, years_of_experience | ✅ |
| Timestamps | created_at, updated_at via `TimestampMixin` | ✅ |
| Soft delete | `is_active` boolean | ⚠️ Partial |

#### Issues

1. **`acknowledged_alerts` relationship has NO cascade on the Doctor side**. If a doctor is deleted while having acknowledged alerts, the FK `emergency_alerts.acknowledged_by` will cause a **foreign key violation** because there is no `ondelete` clause on that FK and no cascade on the relationship. The doctor-side relationship uses no cascade (correct — you want to preserve alerts), but the FK itself lacks `ondelete="SET NULL"`.

2. **No specialization index**: `WHERE specialization = 'Cardiology'` will do a sequential scan.

---

### 3. patient_doctors

| Aspect | Current State | Assessment |
|--------|--------------|------------|
| Table name | `patient_doctors` | ✅ Junction table convention |
| PK | `id` UUID (manual definition) | ✅ |
| FK: patient_id | `patients.id` ON DELETE CASCADE | ✅ |
| FK: doctor_id | `doctors.id` ON DELETE CASCADE | ✅ |
| Unique constraint | `(patient_id, doctor_id)` via `__table_args__` | ✅ Prevents duplicate assignments |
| Boolean | `is_active` (default True) | ✅ |
| Timestamps | created_at, updated_at via `TimestampMixin` | ✅ |
| Soft delete | `is_active` boolean | ✅ |

#### Observation

- This is the **only table using `UniqueConstraint` in `__table_args__`**.
- The `is_active` flag allows historical tracking — a patient-doctor relationship can be deactivated without data loss.

#### Improvement Opportunity

- Add a `deactivated_at` timestamp to distinguish "active but not yet used" from "was active, then deactivated."

---

### 4. refresh_tokens

| Aspect | Current State | Assessment |
|--------|--------------|------------|
| Table name | `refresh_tokens` | ✅ |
| PK | `id` UUID (manual definition) | ✅ |
| Unique constraints | `jti` (unique=True, index=True) | ✅ |
| Indexes | `jti`, `user_id` | ✅ |
| FK constraints | **NONE** — no foreign key to patients or doctors | ⚠️ |
| Timestamps | created_at, updated_at via `TimestampMixin`, plus revoked_at, expires_at | ✅ |
| Soft delete | `is_revoked` boolean | ✅ Appropriate |

#### Issues

1. **No FK to patients or doctors**: `user_id` is stored as `String(255)` with no FK constraint. This means:
   - Orphaned tokens (user_id pointing to deleted user) are possible.
   - No referential integrity — a typo or inconsistent UUID format is silently accepted.
   - Cannot cascade-delete tokens when a user is deleted (tokens become zombies).

2. **No composite index on `(user_id, is_revoked)`**: Common query pattern: "find all non-revoked tokens for this user" — currently requires filtering in application code.

3. **No cleanup scheduling**: `cleanup_expired` exists in the repository but is never called by a scheduler or background task.

---

### 5. reports

| Aspect | Current State | Assessment |
|--------|--------------|------------|
| Table name | `reports` | ✅ |
| PK | `id` UUID (manual definition) | ✅ |
| FK: patient_id | `patients.id` ON DELETE CASCADE, index=True | ✅ |
| FK: doctor_id | `doctors.id`, **NO ondelete**, **nullable** | ❌ |
| Indexes | `patient_id` only | ⚠️ |
| Timestamps | `uploaded_at`, `processed_at` (manual, no TimestampMixin) | ⚠️ |
| Extracted data | `JSON` type (not `JSONB` on SQLite compat — correct for PG would be JSONB) | ⚠️ |

#### Issues

1. **doctor_id FK has NO ondelete action**: If a doctor is deleted, `reports.doctor_id` will not be set to NULL. PostgreSQL will raise a foreign key violation. This is a **production blocker** — doctor deletion will fail if they have associated reports.

2. **No `updated_at`**: Report status changes from `pending` → `processing` → `completed`/`failed`, but there is no `updated_at` to track when the last status change occurred.

3. **No composite status indexes**: Common queries like `WHERE patient_id = ? AND status = 'pending'` will not use an index for the `status` filter.

4. **No `file_size` column**: Cannot track storage usage per patient or detect oversized uploads without opening the file.

5. **No `original_filename` column**: `file_path` is stored but the original user-provided filename is not.

---

### 6. medicines

| Aspect | Current State | Assessment |
|--------|--------------|------------|
| Table name | `medicines` | ✅ |
| PK | `id` UUID (manual definition) | ✅ |
| FK: report_id | `reports.id` ON DELETE CASCADE | ✅ |
| FK: patient_id | `patients.id` ON DELETE CASCADE, index=True | ✅ |
| Indexes | `patient_id` only | ❌ |
| Timestamps | `created_at` only (manual, no TimestampMixin) | ❌ |
| Soft delete | `is_active` boolean | ⚠️ Partial |
| Route | `String(50)` free text | ⚠️ |

#### Issues

1. **Missing composite index `(patient_id, is_active)`**: The DATABASE_DOCUMENTATION claims this index exists, but the model file (`medicine.py:17`) only defines `index=True` on `patient_id`. There is no `__table_args__` with `Index('ix_medicines_patient_active', patient_id, is_active)`. **Documentation is incorrect — this index does not exist.**

2. **No `updated_at`**: Unlike the `TimestampMixin` models, `Medicine` defines its own `created_at` but has **no `updated_at`** column. Updating a medicine's dosage or frequency silently loses the last-updated timestamp.

3. **No `frequency` enum**: `frequency` is `String(255)` free text. Values like "twice daily", "2x/day", "bid", "BID" all mean the same thing but will be stored differently — making adherence calculations unreliable.

4. **No `end_date` validation**: No check that `end_date >= start_date` (application-level validation exists but no DB constraint).

---

### 7. appointments

| Aspect | Current State | Assessment |
|--------|--------------|------------|
| Table name | `appointments` | ✅ |
| PK | `id` UUID via `UUIDMixin` | ✅ |
| FK: patient_id | `patients.id` ON DELETE CASCADE, index=True | ✅ |
| FK: doctor_id | `doctors.id` ON DELETE CASCADE, index=True | ✅ |
| Indexes | `patient_id`, `doctor_id` (individual) | ⚠️ |
| Timestamps | created_at, updated_at via `TimestampMixin` | ✅ |
| Status | `String(50)` free text, default "scheduled" | ⚠️ |

#### Issues

1. **No check constraint on `scheduled_at`**: The appointment datetime is stored without a DB-level constraint that it's in the future (or at least not absurdly far in the past). Application validation exists but no DB guard.

2. **No composite index `(doctor_id, scheduled_at)`**: Common query: "Get upcoming appointments for this doctor, ordered by time." Currently requires sorting across the index on `doctor_id` with no time-range optimization.

3. **No composite index `(patient_id, status)`**: Common query: "Get upcoming appointments for this patient." Same issue.

4. **Status as free-text**: `String(50)` with no enum or check constraint. Values like "scheduled", "Scheduled", "SCHEDULED", "confirmed", "Confirmed" could all coexist. No check constraint prevents invalid values.

5. **No `cancelled_at`**: If an appointment is cancelled (status changes), there's no timestamp recording when.

---

### 8. chat_history

| Aspect | Current State | Assessment |
|--------|--------------|------------|
| Table name | `chat_history` | ✅ |
| PK | `id` UUID (manual definition) | ✅ |
| FK: patient_id | `patients.id` ON DELETE CASCADE, index=True | ✅ |
| Indexes | `patient_id` only | ⚠️ |
| Timestamps | `created_at` only (manual, no TimestampMixin) | ❌ |
| Metadata | `JSON` type (renamed from `metadata` to `metadata_` for SQLAlchemy compat) | ✅ |

#### Issues

1. **No `updated_at`**: Chat messages are immutable (not updated after creation), so this is **acceptable**. But the model should still be consistent — either use `TimestampMixin` everywhere or none.

2. **No composite index `(patient_id, created_at)`**: Common query: "Get the last 50 messages for this patient, ordered by time." Currently the index on `patient_id` helps, but sorting by `created_at` requires a separate sort operation.

3. **No role constraint**: `role` is `String(20)` free text. Currently only "user" and "assistant" are used, but there's no DB-level check preventing "User", "USER", "system", "doctor", etc.

4. **No message length limit**: `Text` is unbounded. A single excessively long message could cause storage issues. Consider a check constraint or application-level truncation.

---

### 9. adherence_logs

| Aspect | Current State | Assessment |
|--------|--------------|------------|
| Table name | `adherence_logs` | ✅ |
| PK | `id` UUID (manual definition) | ✅ |
| FK: medicine_id | `medicines.id` ON DELETE CASCADE, index=True | ✅ |
| FK: patient_id | `patients.id` ON DELETE CASCADE, index=True | ✅ |
| Indexes | `medicine_id`, `patient_id` (individual) | ⚠️ |
| Timestamps | `created_at` only (manual, no TimestampMixin) | ⚠️ |
| Status | `String(20)` free text, default "pending" | ⚠️ |

#### Issues

1. **Missing composite index `(patient_id, status)`**: The DATABASE_DOCUMENTATION claims this index exists, but the model (`adherence_log.py:16-17`) only defines individual indexes on `medicine_id` and `patient_id`. There is no `__table_args__` with this composite index. **Documentation is incorrect.**

2. **No `updated_at`**: If a log status changes from `pending` → `taken`/`missed`, there's no timestamp for when the change occurred.

3. **No check constraint on `scheduled_time` vs `taken_at`**: No DB-level check that `taken_at >= scheduled_time` (medication cannot be taken before it was scheduled). Application-level validation exists but no DB guard.

4. **Status as free-text**: `String(20)` with no enum. Invalid values like "taken", "Taken", "TAKEN", "missed", "skipped" could coexist.

---

### 10. emergency_alerts

| Aspect | Current State | Assessment |
|--------|--------------|------------|
| Table name | `emergency_alerts` | ✅ |
| PK | `id` UUID (manual definition) | ✅ |
| FK: patient_id | `patients.id` ON DELETE CASCADE, index=True | ✅ |
| FK: acknowledged_by | `doctors.id`, **NO ondelete, nullable** | ❌ |
| Indexes | `patient_id`, `risk_level` (individual) | ⚠️ |
| Timestamps | `created_at` only (manual, no TimestampMixin) | ⚠️ |
| Risk level | `String(20)` free text | ⚠️ |

#### Issues

1. **acknowledged_by FK has NO ondelete action**: If a doctor is deleted while they have acknowledged alerts, the FK will cause a **foreign key violation**. Same issue as `reports.doctor_id`. Needs `ondelete="SET NULL"`.

2. **No composite index `(risk_level, is_acknowledged)`**: Common query: "Get all unacknowledged HIGH-risk alerts." Currently requires filtering in application code without index support.

3. **No `updated_at`**: If an alert's acknowledgment status changes, there's no timestamp.

4. **Risk level as free-text**: `String(20)` with no enum. Values like "LOW", "low", "Low", "MEDIUM", "medium", "HIGH", "high" could all coexist. The prompt specifies `LOW | MEDIUM | HIGH` but there's no DB constraint enforcing this.

5. **No check constraint that `resolved_at >= created_at`**: A resolved timestamp before creation is logically impossible.

---

## Cross-Cutting Concerns

### UUID Strategy

| Aspect | Current State | Assessment |
|--------|--------------|------------|
| Generation | `uuid.uuid4()` (random UUID) in Python | ✅ |
| Storage | `UUID(as_uuid=True)` — native PostgreSQL UUID type | ✅ |
| Uniqueness | `unique=True` on all PK columns | ✅ (redundant with PK) |
| Consistency | Mix of `UUIDMixin` (3 models) and manual definition (7 models) | ⚠️ |
| Indexing | PK auto-indexed; some FK columns manually indexed | ⚠️ Inconsistent |

#### Observations

- 3 models use `UUIDMixin` (Patient, Doctor, Appointment).
- 7 models define `id` manually with the same three lines repeated (PatientDoctor, RefreshToken, Report, Medicine, ChatHistory, AdherenceLog, EmergencyAlert).
- This is **code duplication** — a maintenance burden if the UUID strategy changes.
- Some models that don't use `UUIDMixin` also don't use `TimestampMixin` (Report, Medicine, ChatHistory, AdherenceLog, EmergencyAlert) — suggesting these models weren't built with the mixin pattern from the start.

#### Recommendation

- **Not all models need to use UUIDMixin**: The junction table `patient_doctors` could use a composite PK `(patient_id, doctor_id)` instead of a surrogate UUID, reducing index size by ~16 bytes per row.

### Timestamp Strategy

| Model | created_at | updated_at | Source |
|-------|-----------|------------|--------|
| Patient | ✅ | ✅ | `TimestampMixin` |
| Doctor | ✅ | ✅ | `TimestampMixin` |
| PatientDoctor | ✅ | ✅ | `TimestampMixin` |
| RefreshToken | ✅ | ✅ | `TimestampMixin` |
| Appointment | ✅ | ✅ | `TimestampMixin` |
| Report | ✅ (`uploaded_at`, no `created_at`) | ❌ | Manual |
| Medicine | ✅ (`created_at`) | ❌ | Manual |
| ChatHistory | ✅ (`created_at`) | ❌ | Manual |
| AdherenceLog | ✅ (`created_at`) | ❌ | Manual |
| EmergencyAlert | ✅ (`created_at`) | ❌ | Manual |

#### Issue

5 out of 10 models lack `updated_at`. This means:
- When a report status changes, there's no record of when.
- When a medicine is modified, there's no record of when.
- When a chat message is flagged/removed, there's no record.

Models that have immutable records (chat_history) can reasonably skip `updated_at`. Models with mutable state (reports with status transitions, medicines with dosage changes) should have it.

### Soft Delete Strategy

| Model | `is_active` | `deleted_at` | Global Filter | Notes |
|-------|------------|-------------|---------------|-------|
| Patient | ✅ | ❌ | ❌ | Can toggle inactive, but records remain |
| Doctor | ✅ | ❌ | ❌ | Same |
| PatientDoctor | ✅ | ❌ | ❌ | Active flag used for assignment lifecycle |
| Medicine | ✅ | ❌ | ❌ | Active flag used for current medication |
| Report | ❌ | ❌ | ❌ | Not soft-deletable |
| Appointment | ❌ | ❌ | ❌ | Not soft-deletable |
| ChatHistory | ❌ | ❌ | ❌ | Not soft-deletable |
| AdherenceLog | ❌ | ❌ | ❌ | Not soft-deletable |
| EmergencyAlert | ❌ | ❌ | ❌ | Not soft-deletable |
| RefreshToken | ❌ | ❌ | ❌ | Uses `is_revoked` instead |

#### Assessment

- **Inconsistent**: 4 of 10 models have soft-delete capability; 6 don't.
- **No global filter**: No `WHERE is_active = true` is automatically applied. Queries must manually filter — easy to forget.
- **No `deleted_at`**: Cannot distinguish "set inactive 2 years ago" from "just deactivated."
- **Healthcare concern**: Regulatory requirements (HIPAA, GDPR) may require data retention even after "deletion." Soft delete with a `deleted_at` timestamp is the minimum viable approach.

### Audit Strategy

| Aspect | Current State | Assessment |
|--------|--------------|------------|
| Creation time | `created_at` on all models | ✅ |
| Update time | `updated_at` on 5/10 models | ⚠️ Partial |
| Who created | ❌ No `created_by` | ❌ |
| Who updated | ❌ No `updated_by` | ❌ |
| Change history | ❌ No event log, no trigger, no versioning | ❌ |
| Deletion audit | ❌ No `deleted_by`, no `deleted_at` | ❌ |

#### Assessment

There is **no audit trail** beyond basic timestamps. In a healthcare application, this means:
- Cannot determine who created a report (only when).
- Cannot determine who modified a prescription (only when, if `updated_at` exists).
- Cannot track status changes on reports or appointments.
- Cannot reconstruct the state of a record at a previous point in time.

This is a **compliance risk** for healthcare deployments.

### Backup Strategy

| Aspect | Current State | Assessment |
|--------|--------------|------------|
| Automated backups | Not configured in code | ❌ |
| Backup schedule | Not documented | ❌ |
| Retention policy | Not documented | ❌ |
| Restore procedure | Not documented | ❌ |
| Point-in-time recovery | Not configured | ❌ |
| Backup verification | Not configured | ❌ |

#### Assessment

The backup strategy is **entirely absent**. There is no mechanism, schedule, procedure, or documentation for database backups. This is a **critical gap** for any production deployment.

### Partitioning Strategy

| Aspect | Current State | Assessment |
|--------|--------------|------------|
| Table partitioning | Not implemented | ❌ |
| Partition key | N/A | N/A |
| Partition management | N/A | N/A |

#### Assessment

Partitioning is not needed at the current scale but should be planned for these high-growth tables:

| Table | Growth Driver | Estimated Annual Rows | Partition Candidate |
|-------|--------------|----------------------|---------------------|
| `chat_history` | 50 msgs/patient/day | ~18M for 1,000 patients | By month (`created_at`) |
| `adherence_logs` | 4 logs/patient/day | ~1.5M for 1,000 patients | By month (`scheduled_time`) |
| `emergency_alerts` | Low frequency | ~3.6K for 1,000 patients | Not needed yet |
| `reports` | 1/patient/week | ~52K for 1,000 patients | By year (`uploaded_at`) |

### Enum Usage

| Field | Current Type | Values | Issue |
|-------|-------------|--------|-------|
| `appointments.status` | `String(50)` | "scheduled" (default) | No constraint; "Completed", "completed", "COMPLETED" all valid |
| `reports.status` | `String(50)` | "pending" (default) | Same issue |
| `adherence_logs.status` | `String(20)` | "pending" (default) | Same issue |
| `emergency_alerts.risk_level` | `String(20)` | Free text | LOW/medium/HIGH inconsistency |
| `chat_history.role` | `String(20)` | Free text | "user" vs "User" vs "USER" |
| `patient.gender` | `String(20)` | Free text | "male" vs "Male" vs "M" |
| `patient.blood_group` | `String(10)` | Free text | "A+" vs "A RhD Positive" |
| `medicine.route` | `String(50)` | Free text | "oral" vs "Oral" vs "PO" |

**No SQLAlchemy `Enum` type is used anywhere.** All "enum-like" fields are plain `String` columns with no check constraints. This means:
1. Invalid values are silently accepted.
2. Case-insensitive queries require `ILIKE` or `LOWER()`.
3. Schema documentation is misleading (code doesn't enforce what docs describe).

---

## Documentation Gaps

Between `project_memory/DATABASE_DOCUMENTATION.md` and the actual model files:

| Claim in DATABASE_DOCUMENTATION.md | Reality | Severity |
|------------------------------------|---------|----------|
| `medicines` has composite index `(patient_id, is_active)` | ❌ No such index — only individual `patient_id` index | Medium |
| `adherence_logs` has composite index `(patient_id, status)` | ❌ No such index — only individual `patient_id` index | Medium |
| `chat_history` column named `metadata` (JSONB) | ⚠️ Named `metadata_` in code (SQLAlchemy compat), column "metadata" in DB via string override. Type is `JSON` (not `JSONB`). | Low |
| `reports.extracted_data` is JSONB | ⚠️ Stored as `JSON` (SQLite compat). Would be `JSONB` on PostgreSQL. | Low (documented). |
| Migration status: "Pending" | ✅ Migration file exists (`0001_initial_schema.py`) but never applied. | Low (already known) |

---

## Summary of Issues

### Critical (Production Blockers)

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| **DB-01** | `reports.doctor_id` FK has no `ondelete` action | `report.py:18` | Deleting a doctor with reports causes FK violation |
| **DB-02** | `emergency_alerts.acknowledged_by` FK has no `ondelete` action | `emergency_alert.py:21` | Deleting a doctor with acknowledged alerts causes FK violation |
| **DB-03** | `refresh_tokens.user_id` has no FK constraint | `refresh_token.py:23` | Orphaned tokens; no referential integrity |
| **DB-04** | No backup strategy anywhere | Cross-cutting | Complete data loss vulnerability |
| **DB-05** | Hard CASCADE deletes on all patient children | `patient.py:26-32` | Regulatory non-compliance (GDPR/HIPAA) |

### High

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| **DB-06** | 5 of 10 models missing `updated_at` | Report, Medicine, ChatHistory, AdherenceLog, EmergencyAlert | No change tracking |
| **DB-07** | No `deleted_at` on any model with soft delete | Patient, Doctor, PatientDoctor, Medicine | Cannot audit deletion timing |
| **DB-08** | No composite index `(patient_id, is_active)` despite documentation claim | `medicine.py` | Slow queries for active medication lists |
| **DB-09** | No composite index `(patient_id, status)` despite documentation claim | `adherence_log.py` | Slow adherence queries |
| **DB-10** | No composite index `(doctor_id, scheduled_at)` | `appointment.py` | Slow upcoming-appointment queries |
| **DB-11** | No composite index `(patient_id, created_at)` on chat_history | `chat_history.py` | Slow history retrieval |
| **DB-12** | No composite index `(risk_level, is_acknowledged)` on emergency_alerts | `emergency_alert.py` | Slow unacknowledged alert queries |

### Medium

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| **DB-13** | No `Enum` types used anywhere — 8 string fields without constraints | Multiple models | Data quality degradation over time |
| **DB-14** | No audit trail (`created_by`, `updated_by`, event log) | Cross-cutting | Compliance risk |
| **DB-15** | `patient_doctors` uses surrogate UUID PK instead of composite PK `(patient_id, doctor_id)` | `patient_doctor.py:13` | Extra index size, redundant unique constraint |
| **DB-16** | No `file_size` or `original_filename` on reports | `report.py` | Cannot track storage or show user-friendly names |
| **DB-17** | No check constraint on `scheduled_at` (must be in future) | `appointment.py` | Past appointments could be created |
| **DB-18** | No check constraint `end_date >= start_date` on medicines | `medicine.py` | Logically impossible durations |
| **DB-19** | No check constraint `taken_at >= scheduled_time` on adherence_logs | `adherence_log.py` | Logically impossible logs |
| **DB-20** | No cleanup scheduler for expired refresh tokens | `refresh_token.py` | Table growth without bound |

### Low

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| **DB-21** | UUIDMixin not used by 7 of 10 models (code duplication) | Multiple | Maintenance burden |
| **DB-22** | Documentation out of date with actual implementation | `DATABASE_DOCUMENTATION.md` | Misleading for new contributors |
| **DB-23** | No partitioning plan for high-growth tables | Cross-cutting | Future performance issue |
| **DB-24** | No `cancelled_at` on appointments | `appointment.py` | Cannot track cancellation time |

---

## Recommended Improvements

### Tier 1: Pre-Sprint 3B Blockers (Fix Before Migration)

These must be addressed before the Alembic migration is applied to a production database:

1. **Add `ondelete="SET NULL"` to `reports.doctor_id`** and **`emergency_alerts.acknowledged_by`** FKs. Without this, deleting a doctor crashes with a FK violation.

2. **Add an FK constraint from `refresh_tokens.user_id`** to `patients.id` and `doctors.id`, or implement a polymorphic FK pattern. Orphaned tokens are a security and data-integrity concern.

3. **Replace hard CASCADE deletes on Patient with `SET NULL` or soft-delete for regulated tables**. A soft-delete with `deleted_at` and `deleted_by` is the minimum for healthcare compliance. The `all, delete-orphan` cascade on 7 children must be reviewed per-child.

### Tier 2: Indexes (Same Sprint, Before Migration)

4. **Add composite index `(patient_id, is_active)` on medicines** — confirms the documented design intent.

5. **Add composite index `(patient_id, status)` on adherence_logs** — confirms documented intent.

6. **Add composite index `(doctor_id, scheduled_at)` on appointments** — supports upcoming-appointment query.

7. **Add composite index `(patient_id, created_at)` on chat_history** — supports chat history pagination.

8. **Add composite index `(risk_level, is_acknowledged)` on emergency_alerts** — supports unacknowledged alert queries.

9. **Add composite index `(user_id, is_revoked)` on refresh_tokens** — supports "find valid tokens for user" queries.

### Tier 3: Data Quality (Same Sprint or Sprint 3B)

10. **Replace `String` enums with SQLAlchemy `Enum` types** for: `appointments.status`, `reports.status`, `adherence_logs.status`, `emergency_alerts.risk_level`, `chat_history.role`, `patient.gender`, `patient.blood_group`, `medicine.route`. Add a migration that validates existing data and converts. This prevents data corruption at the database level.

11. **Add `updated_at` to mutable models**: Report, Medicine, AdherenceLog, EmergencyAlert. ChatHistory can remain immutable (no `updated_at` needed). This is a schema change requiring a migration.

12. **Add `deleted_at` and `deleted_by` to soft-delete models**: Patient, Doctor, PatientDoctor, Medicine. Models without soft-delete (reports, appointments, chat) should get a discussion — do they need soft delete or can they be hard-deleted?

### Tier 4: Audit and Compliance (Medium-term)

13. **Add `created_by` and `updated_by`** to models where attribution matters (reports, appointments, medicines). Requires knowing the current user context in the service layer.

14. **Implement an audit log table** (`audit_events` or `event_log`) for tracking state changes on critical entities. This can be done with SQLAlchemy event listeners or database triggers.

15. **Document and implement a backup strategy**: daily automated backups with 30-day retention, weekly verification restore, point-in-time recovery via WAL archiving.

### Tier 5: Structural (Long-term)

16. **Plan partitioning for high-growth tables**: `chat_history` and `adherence_logs` will grow fastest. Plan monthly range partitioning on `created_at` for these tables.

17. **Remove surrogate PK on `patient_doctors`** — use composite PK `(patient_id, doctor_id)` instead. This is a multi-step migration (add composite PK, remove old PK column, update FKs that reference `patient_doctors.id` if any).

18. **Add check constraints** for data integrity:
   - `appointments.scheduled_at > NOW()` (or a reasonable minimum)
   - `medicines.end_date >= medicines.start_date`
   - `adherence_logs.taken_at >= adherence_logs.scheduled_time`
   - `emergency_alerts.resolved_at >= emergency_alerts.created_at`

19. **Add `file_size` and `original_filename` to reports** for storage tracking and user experience.

---

*End of review. No code has been modified.*

*Total issues identified: 24 (5 critical, 7 high, 8 medium, 4 low)*
*Total recommended improvements: 19 (across 5 tiers)*

---

*Last updated: 2026-07-11*
