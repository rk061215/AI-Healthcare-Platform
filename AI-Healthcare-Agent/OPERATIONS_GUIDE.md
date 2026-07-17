# Operations Guide

**v1.0.0** — AI Healthcare Follow-up Assistant

---

## 1. Startup Sequence

```
1. PostgreSQL starts and becomes healthy
2. ChromaDB starts (if configured)
3. Backend starts:
   a. Loguru + stdlib logging initialized
   b. Sentry SDK configured (if DSN set)
   c. LangSmith tracing configured (if API key set)
   d. LangGraph runtime bootstrapped (graph compilation + tool registration)
   e. Middleware stack loaded (RequestID → Tracing → Metrics → CSRF → RateLimit → SecurityHeaders)
   f. OpenTelemetry instrumentation applied
   g. Server listens on port 8000
4. Frontend starts (Next.js standalone server on port 3000)
5. Nginx starts (reverse proxy on ports 80/443)
```

**Expected startup time:** ~30–60s (backend), ~10s (frontend)

---

## 2. Health Endpoints

| Endpoint | Method | Purpose | Expected Response |
|----------|--------|---------|-------------------|
| `/health` | GET | Overall health | `{"status": "healthy", "version": "1.0.0"}` |
| `/ready` | GET | Readiness (all services) | `{"status": "ready", "checks": {...}}` |
| `/live` | GET | Liveness (process alive) | `{"status": "alive", "timestamp": "..."}` |
| `/metrics` | GET | Prometheus metrics | JSON metrics snapshot |

### /ready Checks

| Service | Description | Failure Impact |
|---------|-------------|---------------|
| `database` | PostgreSQL query | Complete app failure |
| `migrations` | Alembic revision applied | Schema mismatch |
| `graph_registry` | LangGraph graphs registered | AI pipeline unavailable |
| `tool_registry` | Tools registered | AI tool execution disabled |
| `memory_framework` | Memory service ready | Conversation history lost |
| `ai_provider` | Gemini/OpenAI provider | AI responses unavailable |
| `embedding_provider` | Embedding service | Document processing fails |
| `vector_store` | ChromaDB | RAG retrieval fails |
| `retriever` | Retrieval service | Context builder fails |
| `prompt_manager` | Prompts loaded | AI prompt missing |
| `graph_bootstrap` | LangGraph compiled | AI workflow fails |

---

## 3. Logging

### Log Format (console)
```
2026-07-16 12:00:00.123 | INFO     | app.main:lifespan:33 - Starting AI Healthcare Assistant API v1.0.0
```

### Log Format (json — production)
```json
{"timestamp": "2026-07-16T12:00:00.123Z", "level": "INFO", "module": "app.main", "function": "lifespan", "line": 33, "message": "Starting AI Healthcare Assistant API v1.0.0", "environment": "production", "request_id": "abc-123"}
```

### Log Levels

| Level | Usage |
|-------|-------|
| `DEBUG` | Detailed diagnostic info (dev only) |
| `INFO` | Normal operation events (startup, shutdown, request summary) |
| `WARNING` | Degraded but recoverable states (LangGraph bootstrap issues) |
| `ERROR` | Failed operations (DB disconnect, AI provider error) |
| `CRITICAL` | Unrecoverable failures |

### Setting Log Level
```bash
# Environment variable
LOG_LEVEL=INFO

# Production recommendation
LOG_LEVEL=WARNING
LOG_FORMAT=json
```

---

## 4. Monitoring Stack (Optional Docker)

The observability stack in `docker/docker-compose.observability.yml` includes:

| Service | Port | Purpose |
|---------|------|---------|
| Prometheus | 9090 | Metrics collection & alerting |
| Grafana | 3000 | Dashboards (admin/admin) |
| OpenTelemetry Collector | 4317 | Trace collection |
| Tempo | 3200 | Trace storage |
| Loki | 3100 | Log aggregation |
| Alertmanager | 9093 | Alert routing |

**Start:**
```bash
docker compose -f docker/docker-compose.observability.yml up -d
```

---

## 5. Metrics

Available at `/metrics` endpoint. Key metrics:

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests by method, path, status |
| `http_request_duration_seconds` | Histogram | Request latency distribution |
| `active_connections` | Gauge | Current active DB connections |
| `ai_requests_total` | Counter | AI provider calls |
| `rag_retrieval_duration_seconds` | Histogram | RAG retrieval latency |
| `ocr_processing_duration_seconds` | Histogram | OCR processing latency |

---

## 6. Shutdown Sequence

```
1. Health endpoint returns "not_ready"
2. In-flight requests complete (graceful timeout: 30s)
3. LangGraph runtime persists pending memory
4. Database connections closed
5. OpenTelemetry flush (if configured)
6. Process exits
```

**Docker:**
```bash
docker compose -f docker/docker-compose.production.yml down --timeout 30
```

---

## 7. Backup & Recovery

See `BACKUP_RECOVERY.md` for detailed procedures.

---

## 8. Troubleshooting

### Backend won't start
```bash
# Check logs
docker logs healthcare-backend

# Verify database connection
docker exec healthcare-backend python -c "from app.database.session import SessionLocal; db = SessionLocal(); db.execute(text('SELECT 1'))"

# Run migrations manually
docker exec healthcare-backend alembic upgrade head
```

### AI provider errors
```bash
# Verify API key
docker exec healthcare-backend env | grep GEMINI_API_KEY

# Test provider
docker exec healthcare-backend python -c "from app.ai import AIProviderFactory; p = AIProviderFactory.create('gemini'); print(p.health_check())"
```

### ChromaDB connection refused
```bash
# Verify ChromaDB is running
docker ps | grep chroma

# Check ChromaDB logs
docker logs healthcare-chroma

# Test connection
docker exec healthcare-backend python -c "import chromadb; c = chromadb.HttpClient(host='chromadb', port=8000); print(c.heartbeat())"
```

### Database migration errors
```bash
# Check current revision
alembic current

# View migration history
alembic history

# Force downgrade and retry
alembic downgrade -1
alembic upgrade head
```

---

## 9. Production Health Checks

```bash
# Kubernetes / Docker health check config
livenessProbe:
  httpGet:
    path: /live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 15

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 60
  periodSeconds: 30

# Render uses /health (configured in render.yaml)
```

---

## 10. Resource Requirements

| Service | Memory | CPU | Disk |
|---------|--------|-----|------|
| PostgreSQL | 256–512 MB | 0.5–1.0 | 1–10 GB |
| Backend | 512 MB – 1 GB | 1.0–1.5 | 500 MB + uploads |
| Frontend | 256–512 MB | 0.5–1.0 | 200 MB |
| ChromaDB | 256–512 MB | 0.5–1.0 | 1–5 GB |
| Nginx | 64–128 MB | 0.1–0.2 | 50 MB |
