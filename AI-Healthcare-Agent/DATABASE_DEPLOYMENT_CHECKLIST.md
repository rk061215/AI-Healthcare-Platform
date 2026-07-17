# Database Deployment Checklist

**Target:** PostgreSQL 16 production deployment
**Engine:** SQLAlchemy 2.0 + Alembic

---

## 1. Extensions

| Extension | Purpose | Verified |
|-----------|---------|----------|
| `uuid-ossp` | UUID generation for primary keys | ✅ `init.sql` |
| `pgcrypto` | Cryptographic functions | ✅ `init.sql` |

## 2. Migrations

| Migration | Purpose | Status |
|-----------|---------|--------|
| `0001_initial_schema` | Core tables (users, patients, doctors, appointments, reports, medicines, adherence, chat history) | ✅ |
| `0002_add_documents` | Document storage tables | ✅ |
| `0003_add_ocr_columns` | OCR processing columns | ✅ |
| `0004_add_memory_entries` | LangGraph memory persistence tables | ✅ |

**Total:** 4 migration files, sequential, no circular dependencies.

## 3. Alembic Configuration

| Check | Status | Notes |
|-------|--------|-------|
| `env.py` | ✅ | Imports `Base.metadata`, auto-discovers models via `from app.models import *` |
| `alembic.ini` | ✅ | Present in `backend/` |
| Offline migrations | ✅ | `run_migrations_offline()` configured |
| Online migrations | ✅ | `run_migrations_online()` configured |
| Pool class | ✅ | `pool.NullPool` — no connection pooling during migration |
| **No async support** | ⚠️ | Alembic uses sync SQLAlchemy — works but not async-native |

## 4. Indexes

| Check | Status | Notes |
|-------|--------|-------|
| Primary keys | ✅ | UUID primary keys on all tables |
| Foreign keys | ✅ | Cascade delete where appropriate |
| User email index | ✅ | Unique index on `users.email` |
| Chat session index | ✅ | Index on `chat_history.session_id` |
| Appointment datetime | ✅ | Index on `appointments.appointment_date` |
| Report patient_id | ✅ | Index on `reports.patient_id` |
| Medicine patient_id | ✅ | Index on `medicines.patient_id` |

## 5. Constraints

| Check | Status | Notes |
|-------|--------|-------|
| NOT NULL | ✅ | Required fields have NOT NULL |
| UNIQUE | ✅ | Email, session_id, version_num |
| CHECK constraints | ✅ | Status enums, numeric ranges |
| Foreign key cascades | ✅ | Patient → reports, medicines, appointments |

## 6. UUID Support

| Check | Status | Notes |
|-------|--------|-------|
| Model primary keys | ✅ | UUID type on all ORM models |
| Default UUID generation | ✅ | `uuid.uuid4()` or `sqlalchemy.text("gen_random_uuid()")` |
| Extension available | ✅ | `uuid-ossp` enabled in `init.sql` |

## 7. Startup Migration

| Scenario | Command | Verified |
|----------|---------|----------|
| Docker dev compose | `alembic upgrade head` in backend CMD | ✅ |
| Docker production compose | `alembic upgrade head` in backend CMD | ✅ |
| Render | **Missing** — no pre-deploy command | ⚠️ |
| Manual | `alembic upgrade head` | ✅ |

## 8. Rollback Strategy

| Scenario | Command | Notes |
|----------|---------|-------|
| Rollback last migration | `alembic downgrade -1` | ✅ Standard Alembic |
| Rollback to specific | `alembic downgrade <revision>` | ✅ |
| Rollback all | `alembic downgrade base` | ✅ Drops all tables |
| **No automated rollback script** | ⚠️ | Manual intervention required |

## 9. Connection Pool

| Setting | Dev | Production |
|---------|-----|-----------|
| Pool size | 10 | 10 |
| Max overflow | 20 | 20 |
| Pool pre-ping | ❌ Not set | ⚠️ Should be enabled for production |
| Pool recycle | ❌ Not set | ⚠️ Should be `3600` seconds |

## 10. Production Hardening

| Check | Recommended | Current |
|-------|-------------|---------|
| `pool_pre_ping` | `true` | Not set |
| `pool_recycle` | `3600` | Not set |
| `connect_args` | `{"connect_timeout": 10}` | Not set |
| SSL mode | `require` | Not set |
| Statement timeout | `30s` | Not set |

## Deployment Steps

```bash
# 1. Verify PostgreSQL is running
pg_isready -h <host> -U <user>

# 2. Create database if needed
createdb -h <host> -U <user> healthcare_agent

# 3. Run migrations
cd backend
alembic upgrade head

# 4. Verify all tables
alembic current

# 5. Test connection
python -c "from app.database.session import SessionLocal; db = SessionLocal(); db.execute(text('SELECT 1')); print('OK')"
```

## Rollback Procedure

```bash
# If migration 0004 fails:
alembic downgrade 0003

# If full rollback needed:
alembic downgrade base

# Then fix and re-apply:
alembic upgrade head
```

## Known Limitations

1. No automated rollback testing in CI
2. No connection pool pre-ping (risk of stale connections)
3. No statement timeout configured
4. No async migration support
5. Render deployment missing pre-deploy migration step
