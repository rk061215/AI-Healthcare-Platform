# Environment Variable Reference

**Version:** v1.0.0
**Source:** `backend/.env.example`, `backend/app/core/config.py`, `frontend/.env.local.example`

---

## Legend
- 🔴 **Required** — Must be set for the application to start
- 🟡 **Optional** — Has a safe default but may need tuning
- 🟢 **Development Only** — Only relevant in dev/test environments
- 🔵 **Production Only** — Must be overridden in production
- ⚫ **Secret** — Contains sensitive data, never commit to version control

---

## App Core

| Variable | Default | Category | Description |
|----------|---------|----------|-------------|
| `PROJECT_NAME` | `AI Healthcare Assistant API` | 🟡 Optional | Display name shown in API docs and logs |
| `ENVIRONMENT` | `development` | 🔴 Required | `development`, `staging`, or `production` — controls debug mode, error verbosity |
| `DEBUG` | `true` | 🔴 Required | Enable/disable debug error pages and verbose logging |
| `LOG_LEVEL` | `DEBUG` | 🔴 Required | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `API_V1_PREFIX` | `/api/v1` | 🟡 Optional | URL prefix for all API v1 routes |

---

## Server

| Variable | Default | Category | Description |
|----------|---------|----------|-------------|
| `HOST` | `0.0.0.0` | 🟡 Optional | Bind address (use `0.0.0.0` for Docker, `127.0.0.1` for local) |
| `PORT` | `8000` | 🟡 Optional | HTTP listen port |
| `WORKERS` | `4` | 🟡 Optional | Number of uvicorn worker processes (production only) |

---

## Database

| Variable | Default | Category | Description |
|----------|---------|----------|-------------|
| `DATABASE_URL` | `postgresql://...` | 🔴 Required | Full PostgreSQL connection string. Format: `postgresql://user:pass@host:port/dbname` |
| `DATABASE_POOL_SIZE` | `10` | 🟡 Optional | SQLAlchemy connection pool size |
| `DATABASE_MAX_OVERFLOW` | `20` | 🟡 Optional | Max overflow connections beyond pool size |

---

## JWT Authentication

| Variable | Default | Category | Description |
|----------|---------|----------|-------------|
| `JWT_SECRET_KEY` | `change-me-to-a-random-secret-key` | 🔴 **Required** · ⚫ **Secret** | HMAC signing key for JWT tokens. Generate with: `openssl rand -hex 32` |
| `JWT_ALGORITHM` | `HS256` | 🟡 Optional | JWT signing algorithm (HS256 recommended) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | 🟡 Optional | Short-lived access token TTL |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | 🟡 Optional | Refresh token TTL |
| `JWT_REFRESH_TOKEN_REMEMBER_ME_DAYS` | `30` | 🟡 Optional | "Remember me" refresh token TTL |

---

## AI Provider (Primary)

| Variable | Default | Category | Description |
|----------|---------|----------|-------------|
| `AI_PROVIDER` | `gemini` | 🔴 Required | Active AI provider: `gemini`, `openai` |
| `GEMINI_API_KEY` | (empty) | 🔴 **Required** · ⚫ **Secret** | Google Gemini API key from [aistudio.google.com](https://aistudio.google.com) |
| `GEMINI_MODEL` | `gemini-2.0-flash` | 🟡 Optional | Gemini model ID |
| `GEMINI_BASE_URL` | (empty) | 🟡 Optional | Custom API base URL (for proxies or self-hosted) |
| `EMBEDDING_PROVIDER` | `gemini` | 🟡 Optional | Embedding provider: `gemini`, `openai` |
| `EMBEDDING_MODEL` | `text-embedding-004` | 🟡 Optional | Embedding model ID |

---

## OpenAI (Legacy / Fallback)

| Variable | Default | Category | Description |
|----------|---------|----------|-------------|
| `OPENAI_API_KEY` | (empty) | 🟡 Optional · ⚫ Secret | OpenAI API key (required if AI_PROVIDER=`openai`) |
| `OPENAI_MODEL` | `gpt-4o-mini` | 🟡 Optional | OpenAI model ID |
| `OPENAI_TEMPERATURE` | `0.3` | 🟡 Optional | LLM temperature (lower = more deterministic) |
| `OPENAI_MAX_TOKENS` | `2048` | 🟡 Optional | Max tokens per response |

---

## OCR — Optical Character Recognition

| Variable | Default | Category | Description |
|----------|---------|----------|-------------|
| `OCR_ENGINE` | `tesseract` | 🟡 Optional | Active OCR engine |
| `OCR_PRIMARY_PROVIDER` | `tesseract` | 🟡 Optional | Primary provider: `tesseract`, `google_vision` |
| `OCR_FALLBACK_PROVIDER` | `tesseract` | 🟡 Optional | Fallback if primary fails |
| `OCR_ENABLED` | `true` | 🟡 Optional | Enable/disable OCR processing |
| `OCR_USE_MOCK` | `false` | 🟢 Dev Only | Use mock OCR results (no external dependency) |
| `OCR_RETRY_MAX_ATTEMPTS` | `3` | 🟡 Optional | Max retries on OCR failure |
| `OCR_RETRY_BACKOFF_SECONDS` | `2.0` | 🟡 Optional | Exponential backoff base delay |
| `OCR_MIN_CONFIDENCE` | `0.5` | 🟡 Optional | Minimum confidence score to accept OCR result |
| `OCR_GOOGLE_VISION_TIMEOUT` | `60` | 🟡 Optional | Google Vision API timeout in seconds |
| `OCR_IMAGE_DPI` | `300` | 🟡 Optional | Target DPI for image preprocessing |
| `OCR_PREPROCESS_ENABLE` | `true` | 🟡 Optional | Enable image preprocessing pipeline |
| `OCR_PREPROCESS_DENOISE` | `true` | 🟡 Optional | Apply denoising filter |
| `OCR_PREPROCESS_DESKEW` | `true` | 🟡 Optional | Correct skew/rotation |
| `OCR_PREPROCESS_BINARIZE` | `true` | 🟡 Optional | Convert to binary (black/white) |
| `TESSERACT_CMD` | (empty) | 🟡 Optional | Custom tesseract binary path |
| `OCR_LANGUAGE` | `eng` | 🟡 Optional | Tesseract language pack (`eng`, `hin+eng`, etc.) |
| `OCR_TIMEOUT` | `120` | 🟡 Optional | Tesseract process timeout in seconds |

---

## Google Cloud Vision

| Variable | Default | Category | Description |
|----------|---------|----------|-------------|
| `GOOGLE_APPLICATION_CREDENTIALS` | (empty) | 🟡 Optional · ⚫ Secret | Path to GCP service account JSON key file |

---

## ChromaDB (Vector Store)

| Variable | Default | Category | Description |
|----------|---------|----------|-------------|
| `CHROMA_HOST` | `localhost` | 🔴 Required | ChromaDB server hostname |
| `CHROMA_PORT` | `8001` | 🔴 Required | ChromaDB HTTP port (⚠️ `.env`: 8001, `render.yaml`: 8000) |
| `CHROMA_COLLECTION_NAME` | `report_embeddings` | 🟡 Optional | Default collection name |
| `CHROMA_EMBEDDING_MODEL` | `text-embedding-3-small` | 🟡 Optional | Model used for embedding dimension matching |

---

## Security

| Variable | Default | Category | Description |
|----------|---------|----------|-------------|
| `SECURITY_HEADERS_ENABLED` | `true` | 🟡 Optional | Enable security headers middleware |
| `ENABLE_CSRF_PROTECTION` | `true` | 🟡 Optional | Enable CSRF protection middleware |
| `BACKEND_CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | 🔴 **Required** | Comma-separated allowed CORS origins. **In production:** set to frontend domain |

---

## Upload & Document Storage

| Variable | Default | Category | Description |
|----------|---------|----------|-------------|
| `UPLOAD_DIR` | `./uploads` | 🟡 Optional | Directory for file uploads (use absolute path in Docker) |
| `MAX_UPLOAD_SIZE_MB` | `10` | 🟡 Optional | Max single upload file size in MB |
| `ALLOWED_EXTENSIONS` | `.pdf,.jpg,.jpeg,.png,.dicom` | 🟡 Optional | Comma-separated allowed file extensions |
| `DOCUMENT_STORAGE_DIR` | `./documents` | 🟡 Optional | Directory for processed documents |
| `DOCUMENT_MAX_SIZE_MB` | `20` | 🟡 Optional | Max document file size in MB |
| `DOCUMENT_ALLOWED_EXTENSIONS` | `.pdf,.png,.jpg,.jpeg` | 🟡 Optional | Comma-separated allowed document extensions |

---

## Rate Limiting

| Variable | Default | Category | Description |
|----------|---------|----------|-------------|
| `RATE_LIMIT_ENABLED` | `true` | 🟡 Optional | Enable rate limiting middleware |
| `RATE_LIMIT_PROVIDER` | `in_memory` | 🟡 Optional | Backend: `in_memory`, `postgres`. PostgreSQL recommended for multi-worker |
| `RATE_LIMIT_PER_MINUTE` | `60` | 🟡 Optional | Max general API requests per minute per IP |
| `RATE_LIMIT_LOGIN_PER_MINUTE` | `5` | 🔴 **Required** | Max login attempts per minute — critical for brute force prevention |
| `RATE_LIMIT_MAX_REQUESTS` | `100` | 🟡 Optional | Absolute max requests per window |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | 🟡 Optional | Rate limit window duration |
| `REDIS_URL` | (empty) | 🟡 Optional | Redis connection string for production rate limiting (requires Redis) |

---

## Appointment Management

| Variable | Default | Category | Description |
|----------|---------|----------|-------------|
| `APPOINTMENT_DURATION_MINUTES` | `30` | 🟡 Optional | Default appointment slot duration |
| `APPOINTMENT_MIN_ADVANCE_HOURS` | `1` | 🟡 Optional | Min hours before booking allowed |
| `APPOINTMENT_MAX_DAYS_AHEAD` | `90` | 🟡 Optional | Max days in the future for booking |
| `APPOINTMENT_CANCELLATION_WINDOW_HOURS` | `24` | 🟡 Optional | Hours before appointment to allow cancellation |
| `APPOINTMENT_REMINDER_HOURS_BEFORE` | `24,2` | 🟡 Optional | Comma-separated reminder intervals |
| `DEFAULT_TIMEZONE` | `UTC` | 🟡 Optional | System timezone |

---

## Checkpoint & Memory

| Variable | Default | Category | Description |
|----------|---------|----------|-------------|
| `CHECKPOINT_PROVIDER` | `in_memory` | 🟡 Optional | LangGraph checkpoint backend: `in_memory`, `postgres` |

---

## Observability — Logging

| Variable | Default | Category | Description |
|----------|---------|----------|-------------|
| `LOG_FORMAT` | `console` | 🟡 Optional | Log format: `console` (human-readable), `json` (structured, recommended for production) |

---

## Observability — Sentry

| Variable | Default | Category | Description |
|----------|---------|----------|-------------|
| `SENTRY_DSN` | (empty) | 🟡 Optional · ⚫ Secret | Sentry SDK DSN for error tracking |
| `SENTRY_ENVIRONMENT` | (empty) | 🟡 Optional | Sentry environment tag (e.g., `production`) |

---

## Observability — LangSmith

| Variable | Default | Category | Description |
|----------|---------|----------|-------------|
| `LANGSMITH_API_KEY` | (empty) | 🟡 Optional · ⚫ Secret | LangSmith API key for LLM tracing |
| `LANGSMITH_PROJECT` | `ai-healthcare-dev` | 🟡 Optional | LangSmith project name |
| `LANGSMITH_TRACING_SAMPLING_RATE` | `0.1` | 🟡 Optional | Tracing sampling rate (0.0–1.0) |

---

## Observability — OpenTelemetry

| Variable | Default | Category | Description |
|----------|---------|----------|-------------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | 🟡 Optional | OTLP gRPC endpoint for trace export |
| `OTEL_SERVICE_NAME` | `ai-healthcare-backend` | 🟡 Optional | Service name in trace data |
| `OTEL_TRACE_SAMPLING_RATE` | `0.1` | 🟡 Optional | Trace sampling rate |

---

## Observability — Prometheus

| Variable | Default | Category | Description |
|----------|---------|----------|-------------|
| `PROMETHEUS_MULTIPROC_DIR` | `/tmp/prometheus` | 🟡 Optional | Temp dir for multiprocess prometheus metrics |

---

## Backup

| Variable | Default | Category | Description |
|----------|---------|----------|-------------|
| `BACKUP_DIR` | `./backups` | 🟡 Optional | Directory for database and file backups |
| `BACKUP_RETENTION_DAYS` | `30` | 🟡 Optional | Days to retain backups |
| `BACKUP_SCHEDULE_CRON` | `0 3 * * *` | 🟡 Optional | Cron expression for automated backups (daily at 3 AM) |

---

## Background Tasks

| Variable | Default | Category | Description |
|----------|---------|----------|-------------|
| `REMINDER_CHECK_INTERVAL_MINUTES` | `15` | 🟡 Optional | Interval for checking appointment reminders |

---

## Frontend (Next.js) Variables

These are set in `frontend/.env.local` and exposed at build time (prefix `NEXT_PUBLIC_*`).

| Variable | Default | Category | Description |
|----------|---------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | 🔴 Required | Backend API base URL (publicly exposed to browser) |
| `NEXT_PUBLIC_WS_URL` | `ws://localhost:8000/ws` | 🟡 Optional | WebSocket endpoint (if chat streaming is enabled) |
| `NEXT_PUBLIC_APP_URL` | `http://localhost:3000` | 🔴 Required | Self-referencing app URL for OAuth/callbacks |
| `NEXT_PUBLIC_ENABLE_CHAT` | `true` | 🟡 Optional | Show/hide AI chat feature |
| `NEXT_PUBLIC_ENABLE_EMERGENCY` | `true` | 🟡 Optional | Show/hide emergency triage feature |
| `NEXT_PUBLIC_ENABLE_REMINDERS` | `true` | 🟡 Optional | Show/hide appointment reminders |

---

## Render-Specific (set in render.yaml, not .env)

| Variable | Notes |
|----------|-------|
| `CHROMA_HOST` | Set to `localhost` + run ChromaDB as sidecar, OR use external service |
| `CHROMA_PORT` | `8000` (ChromaDB default — note mismatch with `.env.example` `8001`) |
| `RATE_LIMIT_PER_MINUTE` | Set to `120` (more permissive for Render free tier) |
| `RATE_LIMIT_LOGIN_PER_MINUTE` | Set to `10` |

---

## Quick Override Table (Dev → Production)

| Variable | Dev Value | Production Value |
|----------|-----------|-----------------|
| `ENVIRONMENT` | `development` | `production` |
| `DEBUG` | `true` | `false` |
| `LOG_LEVEL` | `DEBUG` | `INFO` or `WARNING` |
| `JWT_SECRET_KEY` | `change-me-...` | `openssl rand -hex 32` output |
| `BACKEND_CORS_ORIGINS` | `http://localhost:3000` | `https://your-frontend-domain.com` |
| `GEMINI_API_KEY` | (empty) | Your real Gemini API key |
| `CHROMA_HOST` | `localhost` | ChromaDB container/external host |
| `DATABASE_URL` | Local PostgreSQL | Render/Neon PostgreSQL connection string |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | `https://your-backend.onrender.com/api/v1` |
| `RATE_LIMIT_PROVIDER` | `in_memory` | `postgres` (multi-worker safety) |
| `LOG_FORMAT` | `console` | `json` (structured logging) |
| `REDIS_URL` | (empty) | Redis connection string (if Redis used) |
