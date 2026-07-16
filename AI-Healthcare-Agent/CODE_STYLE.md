# Code Style Guide

This document defines the coding standards for the AI Healthcare Follow-up Assistant. Adherence to these standards is enforced through automated tooling (pre-commit hooks, CI checks) and manual code review.

## Table of Contents

- [Python Style Guide](#python-style-guide)
- [TypeScript Style Guide](#typescript-style-guide)
- [Naming Conventions](#naming-conventions)
- [Folder Conventions](#folder-conventions)
- [File Naming](#file-naming)
- [API Naming](#api-naming)
- [Database Naming](#database-naming)
- [Environment Variable Naming](#environment-variable-naming)
- [Logging Standards](#logging-standards)
- [Exception Handling](#exception-handling)

---

## Python Style Guide

### Formatter and Linter

| Tool      | Configuration                          | Command                   |
|-----------|----------------------------------------|---------------------------|
| Black     | `pyproject.toml` — line-length=100     | `black .`                 |
| isort     | `pyproject.toml` — profile=black       | `isort .`                 |
| flake8    | `pyproject.toml` — max-line-length=100 | `flake8 app/`             |
| mypy      | `pyproject.toml` — strict=false        | `mypy app/`               |

### Black Rules

- Line length: **100 characters**.
- Trailing commas on multi-line constructs.
- Strings use **double quotes** (`"`) except when the string contains a double quote.
- No extra blank lines at the end of a file.

### isort Rules

- Profile: `black` (compatible with Black's formatting).
- Third-party imports after standard library, then local imports.
- Groups separated by a blank line.

```python
# Standard library
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

# Third-party
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Local
from app.core.exceptions import NotFoundException
from app.schemas.patient import PatientResponse
```

### Type Annotations

Every function **must** have type annotations (enforced by mypy for public APIs).

```python
# Correct
def get_patient_by_email(email: str) -> Optional[Patient]:
    ...

# Incorrect — missing return type
def get_patient_by_email(email):
    ...

# Use Optional[x] for x | None
def find_user(user_id: Optional[str] = None) -> dict[str, Any]:
    ...

# Prefer | syntax for unions (Python 3.12+)
def process(value: str | int) -> bool:
    ...
```

### Docstrings

- Use **Google-style** docstrings for all public modules, classes, and functions.
- One-line docstrings for simple functions.

```python
def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token.

    Args:
        subject: The user ID (UUID string).
        role: The user role ("patient" or "doctor").
        expires_delta: Custom expiry duration. Defaults to settings value.

    Returns:
        Encoded JWT string.
    """
    ...
```

### Imports Ordering

1. Standard library
2. Third-party libraries (alphabetical)
3. Local application modules (alphabetical)
4. Each group separated by a blank line
5. Avoid wildcard imports (`from module import *`)

### Class Structure

```python
class AppointmentService:
    """Business logic for appointment management."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = AppointmentRepository(db)

    def create_appointment(self, data: dict) -> Appointment:
        ...
```

---

## TypeScript Style Guide

### Formatter and Linter

| Tool       | Configuration          | Command                      |
|------------|------------------------|------------------------------|
| Prettier   | `.prettierrc`          | `prettier --write src/`      |
| ESLint     | `eslint.config.js`     | `next lint`                  |
| TypeScript | `tsconfig.json`        | `tsc --noEmit`               |

### Prettier Rules

- Single quotes (`'`) for strings.
- Trailing commas in all multi-line constructs.
- Print width: **100 characters**.
- Tab width: **2 spaces**.
- Semicolons required.
- JSX single quotes for attributes.

```typescript
// Correct
const greeting = 'Hello, world!';

// Incorrect
const greeting = "Hello, world!";
```

### TypeScript Rules

- Enable `strict: true` in `tsconfig.json`.
- Prefer `interface` over `type` for object shapes.
- Use `type` for unions, intersections, and utility types.
- Avoid `any` — use `unknown` and type guards instead.
- Use `const` for values that never change.

```typescript
// Correct — interface for objects
interface PatientProfile {
  id: string;
  fullName: string;
  email: string;
}

// Correct — type for unions
type UserRole = 'patient' | 'doctor';

// Incorrect — avoid any
function process(data: any): void { ... }

// Correct — use unknown with type guard
function process(data: unknown): void {
  if (typeof data === 'string') {
    console.log(data.toUpperCase());
  }
}
```

### React Component Patterns

```typescript
// Use function components (not class components)
export function PatientDashboard({ patientId }: { patientId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ['patient', patientId],
    queryFn: () => api.getPatient(patientId),
  });

  if (isLoading) return <LoadingState />;

  return <div>{/* ... */}</div>;
}
```

### State Management (Zustand)

```typescript
interface AuthState {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      login: async (email, password) => {
        const response = await authApi.login(email, password);
        set({ user: response.user, token: response.accessToken });
      },
      logout: () => set({ user: null, token: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token }),
    }
  )
);
```

---

## Naming Conventions

### Python

| Element              | Convention   | Example                       |
|----------------------|--------------|-------------------------------|
| Modules              | snake_case   | `appointment_service.py`      |
| Classes              | PascalCase   | `AppointmentService`          |
| Functions            | snake_case   | `create_appointment()`        |
| Variables            | snake_case   | `patient_email`               |
| Constants            | UPPER_CASE   | `MAX_UPLOAD_SIZE_MB`          |
| Private members      | `_` prefix   | `_check_ownership()`          |
| Protected members    | `_` prefix   | `_validate_password()`        |
| Method parameters    | snake_case   | `user_id: str`                |
| Type variables       | PascalCase   | `ModelType`, `T`              |

### TypeScript

| Element              | Convention   | Example                       |
|----------------------|--------------|-------------------------------|
| Files                | kebab-case   | `patient-dashboard.tsx`       |
| Components           | PascalCase   | `PatientDashboard`            |
| Functions            | camelCase    | `formatDate()`                |
| Variables            | camelCase    | `patientEmail`                |
| Interfaces           | PascalCase   | `PatientProfile`              |
| Types                | PascalCase   | `UserRole`                    |
| Constants            | UPPER_CASE   | `API_BASE_URL`                |
| Enums                | PascalCase   | `enum AppointmentStatus`      |
| Enum members         | PascalCase   | `AppointmentStatus.Scheduled` |

### URL / Route Parameters

| Element              | Convention   | Example                       |
|----------------------|--------------|-------------------------------|
| Route paths          | kebab-case   | `/api/v1/patient-appointments`|
| Query parameters     | snake_case   | `?page=1&per_page=20`        |
| Path parameters      | snake_case   | `/appointments/{appointment_id}` |

---

## Folder Conventions

### Backend

```
backend/
├── app/
│   ├── api/
│   │   ├── v1/           # Route handlers grouped by domain
│   │   │   ├── auth.py
│   │   │   ├── patients.py
│   │   │   └── ...
│   │   └── deps.py       # Shared dependencies
│   ├── agents/           # LangGraph agents by domain
│   │   ├── medical_agent/
│   │   ├── chat_agent/
│   │   └── ...
│   ├── core/             # Config, security, logging, exceptions
│   ├── database/         # Engine setup, base model
│   ├── middleware/       # CORS, CSRF, rate limit, error handler
│   ├── models/           # SQLAlchemy models (one file per model)
│   ├── repositories/     # Data access layer (one per model)
│   ├── schemas/          # Pydantic schemas (one per domain)
│   ├── services/         # Business logic (one per domain)
│   ├── prompts/          # LLM prompt templates
│   ├── rag/              # RAG system (vector store, retriever)
│   ├── ocr/              # OCR service
│   ├── tasks/            # Background task definitions
│   └── utils/            # Shared utilities
├── tests/
│   ├── conftest.py       # Shared fixtures
│   └── test_api/         # API-level integration tests
├── alembic/              # Database migrations
└── logs/                 # Log files (gitignored)
```

### Frontend

```
frontend/
├── src/
│   ├── app/
│   │   ├── (auth)/       # Auth pages (login, register)
│   │   ├── patient/      # Patient routes
│   │   └── doctor/       # Doctor routes
│   ├── components/
│   │   ├── ui/           # Primitive UI components (shadcn/ui)
│   │   └── shared/       # Shared business components
│   ├── services/         # API client modules
│   ├── lib/
│   │   └── store/        # Zustand stores
│   └── types/            # TypeScript type definitions
└── public/               # Static assets
```

### Folder Rules

- Each domain folder contains files for **one domain only**.
- No circular dependencies between services (service A imports service B, and service B imports service A).
- Tests mirror the `app/` structure under `tests/`.

---

## File Naming

### Backend

| Type              | Convention                     | Example                            |
|-------------------|--------------------------------|------------------------------------|
| Route handler     | `plural_domain.py`             | `appointments.py`                  |
| Model             | `singular_model.py`            | `appointment.py`                   |
| Repository        | `singular_repository.py`       | `appointment_repository.py`        |
| Service           | `singular_service.py`          | `appointment_service.py`           |
| Schema            | `singular.py`                  | `appointment.py` (under schemas/)  |
| Agent             | `<descriptor>_agent/`          | `medical_agent/`                   |

### Frontend

| Type              | Convention                     | Example                            |
|-------------------|--------------------------------|------------------------------------|
| Page              | `page.tsx` inside route dir    | `dashboard/page.tsx`               |
| Component         | `PascalCase.tsx`               | `PatientDashboard.tsx`             |
| Service           | `kebab-case.ts`                | `auth-service.ts` (under services/)|
| Store             | `kebab-case.ts`                | `auth-store.ts`                    |
| Type definitions  | `index.ts` in types/           | `types/index.ts`                   |

### Test Files

```
tests/test_api/test_{domain}.py    # backend integration tests
src/**/*.test.tsx                   # frontend component tests
```

Special test files (conftest.py) are not prefixed with `test_`.

---

## API Naming

### URL Structure

```
{method} /api/v1/{resource}[/{resource_id}][/{sub_resource}]
```

### Rules

1. **Use plural nouns** for resources: `/appointments`, `/patients`, `/doctors`.
2. **Use kebab-case** for multi-word paths: `/patient-appointments`.
3. **Use snake_case** for query and path parameters: `?page=1&per_page=20`.
4. **HTTP methods map to CRUD**:

   | Method   | Action               | Example                          |
   |----------|----------------------|----------------------------------|
   | GET      | List or retrieve     | `GET /appointments`              |
   | POST     | Create               | `POST /appointments`             |
   | PATCH    | Partial update       | `PATCH /appointments/{id}`       |
   | DELETE   | Delete               | `DELETE /appointments/{id}`      |

5. **Action verbs** only when CRUD is insufficient:

   ```
   POST /appointments/{id}/cancel
   POST /patients/{id}/assign
   ```

6. **Version prefix**: `/api/v1/` at the router level, not per-endpoint.
7. **Response format**: Always return JSON. Success: 200/201. Client errors: 4xx. Server errors: 5xx.
8. **Error response shape**:

   ```json
   {
     "error": "Human-readable message",
     "detail": "Optional detail or validation errors"
   }
   ```

---

## Database Naming

### Tables

- **Plural snake_case**: `appointments`, `refresh_tokens`, `patient_doctor`.
- Join tables use the two table names joined by underscore: `patient_doctor`.

### Columns

- **snake_case**: `patient_id`, `full_name`, `created_at`.
- **Foreign keys**: `{referenced_table_singular}_id` (e.g., `patient_id`, `doctor_id`).
- **Timestamps**: `created_at`, `updated_at` on every table (via `TimestampMixin`).
- **Boolean flags**: `is_active`, `is_revoked`, `has_insurance`.

### Indexes

- Foreign key columns should have explicit indexes.
- Composite indexes for frequent filter pairs (e.g., `patient_id + status`).
- Unique indexes for natural keys (e.g., `email` on `patients`).

### Migration Names

- `{version}_{description}.py` (auto-generated by Alembic).
- Description in snake_case: `0002_add_appointment_indexes.py`.

---

## Environment Variable Naming

### Rules

1. **UPPER_SNAKE_CASE**.
2. **Group by domain** with prefixes:

   | Prefix     | Domain                | Example                                  |
   |------------|-----------------------|------------------------------------------|
   | (none)     | Application           | `PROJECT_NAME`, `ENVIRONMENT`, `DEBUG`   |
   | `JWT_`     | JWT tokens            | `JWT_SECRET_KEY`, `JWT_ALGORITHM`        |
   | `DATABASE_`| Database connection   | `DATABASE_URL`, `DATABASE_POOL_SIZE`     |
   | `OPENAI_`  | OpenAI API            | `OPENAI_API_KEY`, `OPENAI_MODEL`         |
   | `CHROMA_`  | ChromaDB              | `CHROMA_HOST`, `CHROMA_PORT`            |
   | `RATE_LIMIT_` | Rate limiting     | `RATE_LIMIT_PER_MINUTE`                 |
   | `REDIS_`   | Redis connection      | `REDIS_URL`                             |
   | `CORS_`    | CORS configuration    | `BACKEND_CORS_ORIGINS`                  |

3. **Always update `.env.example`** when adding a new variable.
4. **No secrets in code** — read everything from environment variables via `pydantic-settings`.
5. **Provide sensible defaults** in `config.py` for development.

### .env.example Format

```ini
# ──────────────────────────────────────────────
# Backend Environment Variables
# ──────────────────────────────────────────────

# App
PROJECT_NAME=AI Healthcare Assistant API
ENVIRONMENT=development
DEBUG=true
```

---

## Logging Standards

### Framework

We use **Loguru** for all logging (configured in `app/core/logging.py`).

### Log Levels

| Level   | When to Use                                              |
|---------|----------------------------------------------------------|
| DEBUG   | Detailed information for debugging (request params, etc.)|
| INFO    | Normal operational messages (startup, shutdown, CRUD)    |
| WARNING | Something unexpected but not an error (rate limit hit)   |
| ERROR   | A failure that needs attention (unhandled exception)     |
| CRITICAL| System is unusable (database connection lost)            |

### Format

```
2026-07-11 12:30:00.123 | INFO     | app.services.auth_service:register_patient:42 | Patient registered: user@example.com
```

Configured via the `LOG_FORMAT` in `logging.py`. Do not override this format.

### Rules

1. **Log at the appropriate level** — don't log everything at INFO.
2. **Include context** — user IDs, entity IDs, correlation IDs.
3. **Never log secrets** — passwords, tokens, API keys.
4. **Use structured data** by passing keyword arguments, not string interpolation.
5. **Log errors with traceback** using `logger.exception()`.

```python
# Correct
logger.info("Patient registered", email=patient.email, patient_id=patient.id)

# Correct — includes traceback
try:
    result = risky_operation()
except Exception:
    logger.exception("Failed to process appointment")

# Incorrect — string interpolation in log message
logger.info(f"Patient registered: {patient.email}")

# Incorrect — logging a password
logger.debug("User payload", password=payload.password)
```

### Per-Request Context

Use Loguru's context binding for request-scoped data:

```python
from loguru import logger as log

async def dispatch(self, request, call_next):
    with log.contextualize(request_id=uuid.uuid4(), client_ip=client_ip):
        return await call_next(request)
```

---

## Exception Handling

### Custom Exception Hierarchy

All application exceptions inherit from `AppException` (defined in `app/core/exceptions.py`):

```
Exception
└── AppException
    ├── NotFoundException      (404)
    ├── UnauthorizedException  (401)
    ├── ForbiddenException     (403)
    ├── ConflictException      (409)
    ├── ValidationException    (422)
    └── RateLimitException     (429)
```

### Rules

1. **Raise domain-specific exceptions** in service and repository layers.
2. **Raise HTTPException** directly in route handlers (FastAPI pattern).
3. **Use the global exception handler** in `error_handler.py` — it catches all `AppException` instances and returns structured JSON.
4. **Do not catch and silence** exceptions unless you re-raise as a more specific type.
5. **Validate inputs early** — raise `ValidationException` at the boundary.

```python
# Service layer — raise domain exception
def get_patient(self, patient_id: str) -> Patient:
    patient = self.repository.get(patient_id)
    if not patient:
        raise NotFoundException("Patient", patient_id)
    return patient

# Route handler — raise HTTPException for auth/request-specific errors
@router.get("/me")
def get_me(payload: dict = Depends(get_current_user)):
    if payload.get("role") != "patient":
        raise HTTPException(status_code=403, detail="Not a patient")
    return ...

# Incorrect — catching and silencing
try:
    patient = service.get_patient(id)
except NotFoundException:
    pass  # silently swallows the error
```

### Global Handler Behavior

The global exception handler in `app/middleware/error_handler.py`:

- Catches `AppException` → returns `{ "error": ..., "detail": ... }` with the exception's status code.
- Catches all other `Exception` → returns 500 with `{ "error": "Internal server error" }`.
- In debug mode (`__debug__`), includes the exception string in the response.

---

*Last updated: 2026-07-11*
