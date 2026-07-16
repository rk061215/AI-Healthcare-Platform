# Deployment Guide — AI Healthcare Follow-up Assistant

## Prerequisites

- Docker 24+ and Docker Compose v2 installed
- Git
- A free account on one of: Railway, Render, or Fly.io
- Domain name (optional, for production with HTTPS)

### Minimum VPS Requirements

| Resource  | Minimum   | Recommended |
|-----------|-----------|-------------|
| RAM       | 2 GB      | 4 GB        |
| CPU       | 2 vCPUs   | 4 vCPUs     |
| Disk      | 20 GB SSD | 40 GB SSD   |
| Docker    | 24+       | 24+         |

---

## Option 1: Docker Compose (VPS)

### Step 1 — Clone the Repository

```bash
git clone <repository-url> ai-healthcare
cd ai-healthcare
```

### Step 2 — Set Up Environment Variables

```bash
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
```

Edit `backend/.env` and set at minimum:

```ini
ENVIRONMENT=production
DEBUG=false
JWT_SECRET_KEY=<generate-a-strong-random-string>
BACKEND_CORS_ORIGINS=https://your-frontend-domain.com
GEMINI_API_KEY=<your-gemini-api-key>
```

Generate a secure JWT secret:

```bash
openssl rand -hex 32
```

### Step 3 — Start Services

```bash
docker compose -f docker/docker-compose.production.yml up -d
```

### Step 4 — Run Database Migrations

```bash
docker compose -f docker/docker-compose.production.yml exec backend alembic upgrade head
```

### Step 5 — Seed Demo Data (Optional)

```bash
docker compose -f docker/docker-compose.production.yml exec backend python scripts/import_datasets.py
```

### Step 6 — Verify Health

```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy", "version": "0.8.0"}

curl http://localhost:8000/ready
# Expected: {"status": "ready", ...}
```

### Useful Commands

```bash
# View logs
docker compose -f docker/docker-compose.production.yml logs -f

# Stop services
docker compose -f docker/docker-compose.production.yml down

# Restart a service
docker compose -f docker/docker-compose.production.yml restart backend

# Run a one-off command
docker compose -f docker/docker-compose.production.yml run --rm backend python scripts/check_deployment_readiness.py
```

---

## Option 2: Render (Free Tier)

Render offers a free tier with 512 MB RAM for web services and a free PostgreSQL database (1 GB storage).

### Step 1 — Create a PostgreSQL Database

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click **New +** → **PostgreSQL**
3. Fill in:
   - **Name**: `healthcare-db`
   - **Database**: `healthcare_agent`
   - **User**: `healthcare_user`
   - **Region**: Choose closest to your users
4. Click **Create Database**
5. Copy the **Internal Database URL** from the dashboard

### Step 2 — Deploy the Backend

1. Click **New +** → **Web Service**
2. Connect your repository or use a public repo
3. Fill in:
   - **Name**: `healthcare-backend`
   - **Environment**: `Docker`
   - **Root Directory**: `backend`
   - **Dockerfile Path**: `Dockerfile`
   - **Branch**: `main`
   - **Plan**: **Free** ($0/month — 512 MB RAM)
4. Set environment variables:

| Variable                     | Value                                                        |
|------------------------------|--------------------------------------------------------------|
| `ENVIRONMENT`                | `production`                                                 |
| `DEBUG`                      | `false`                                                      |
| `DATABASE_URL`               | `postgresql://...` (from Step 1 — Internal URL)              |
| `JWT_SECRET_KEY`             | `<random-hex-string>`                                        |
| `BACKEND_CORS_ORIGINS`       | `https://healthcare-frontend.onrender.com`                   |
| `GEMINI_API_KEY`             | `<your-gemini-api-key>`                                      |
| `CHROMA_HOST`                | `localhost`                                                  |
| `REDIS_URL`                  | *(leave blank — uses in-memory rate limiter)*                |

5. Click **Deploy Web Service**
6. After deployment, go to **Events** tab and verify the build succeeded
7. Run migrations (Shell tab):
   ```bash
   alembic upgrade head
   ```

### Step 3 — Deploy the Frontend

1. Click **New +** → **Static Site**
2. Connect your repository
3. Fill in:
   - **Name**: `healthcare-frontend`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm ci && npm run build`
   - **Publish Directory**: `.next`
   - **Branch**: `main`
4. Set environment variables:

| Variable               | Value                                              |
|------------------------|----------------------------------------------------|
| `NEXT_PUBLIC_API_URL`  | `https://healthcare-backend.onrender.com/api/v1`   |
| `NEXT_PUBLIC_WS_URL`   | `wss://healthcare-backend.onrender.com/ws`         |
| `NEXT_PUBLIC_APP_URL`  | `https://healthcare-frontend.onrender.com`         |

5. Click **Deploy Static Site**

### Step 4 — Update CORS (Important!)

After deployment, update the backend environment variable:

```
BACKEND_CORS_ORIGINS = https://healthcare-frontend.onrender.com
```

Then go to the backend service dashboard and click **Manual Deploy** → **Clear Build Cache & Deploy**.

---

## Option 3: Railway (Free Tier)

Railway offers $5 USD of free credits monthly (no credit card required for free tier).

### Step 1 — Create a PostgreSQL Database

1. Go to [railway.app](https://railway.app) and log in
2. Click **New Project** → **Provision PostgreSQL**
3. Once created, click on the PostgreSQL service
4. Copy the **Connection URL** from the **Connect** tab

### Step 2 — Deploy the Backend

1. Click **New Project** → **Deploy from GitHub repo**
2. Select your repository
3. Add a **New Service** → select **Backend** root directory
4. Set the **Start Command**:
   ```bash
   alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
5. Add environment variables (same table as Render above)
6. Under **Settings** → **Service Type**, ensure it's set to `web`
7. Set **Port** to `8000`
8. Click **Deploy**

### Step 3 — Deploy the Frontend

1. Add another **New Service** → select **Frontend** root directory
2. Set **Build Command**: `npm ci && npm run build`
3. Set **Start Command**: `node server.js`
4. Add environment variables (same as Render frontend)
5. Under **Settings** → **Service Type**, set to `web`
6. Set **Port** to `3000`

---

## Environment Variables

### Backend (`backend/.env`)

| Variable                        | Required | Default                                          | Description                                    |
|---------------------------------|----------|--------------------------------------------------|------------------------------------------------|
| `ENVIRONMENT`                   | No       | `development`                                    | Runtime environment (`production`, `development`) |
| `DEBUG`                         | No       | `true`                                           | Enable debug mode (`true`/`false`)             |
| `LOG_LEVEL`                     | No       | `DEBUG`                                          | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `HOST`                          | No       | `0.0.0.0`                                        | Bind address                                   |
| `PORT`                          | No       | `8000`                                           | Application port                               |
| `WORKERS`                       | No       | `4`                                              | Number of uvicorn workers                      |
| `DATABASE_URL`                  | **Yes**  | `postgresql://...`                                | PostgreSQL connection string                   |
| `DATABASE_POOL_SIZE`            | No       | `10`                                             | SQLAlchemy pool size                           |
| `DATABASE_MAX_OVERFLOW`         | No       | `20`                                             | SQLAlchemy max overflow                        |
| `JWT_SECRET_KEY`                | **Yes**  | `change-me-to-a-random-secret-key`                | Secret for JWT token signing (change in prod!) |
| `JWT_ALGORITHM`                 | No       | `HS256`                                          | JWT signing algorithm                          |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | No     | `15`                                             | Access token TTL                               |
| `OPENAI_API_KEY`                | No*      | `""`                                             | OpenAI API key (if using OpenAI provider)      |
| `GEMINI_API_KEY`                | No*      | `""`                                             | Google Gemini API key (if using Gemini)        |
| `AI_PROVIDER`                   | No       | `gemini`                                         | Primary AI provider (`gemini`, `openai`)       |
| `EMBEDDING_PROVIDER`            | No       | `gemini`                                         | Embedding provider                             |
| `CHROMA_HOST`                   | No       | `localhost`                                      | ChromaDB host                                  |
| `CHROMA_PORT`                   | No       | `8001`                                           | ChromaDB port                                  |
| `BACKEND_CORS_ORIGINS`          | **Yes**  | `http://localhost:3000,http://localhost:5173`     | Comma-separated allowed CORS origins           |
| `RATE_LIMIT_PER_MINUTE`         | No       | `60`                                             | Global rate limit (requests/minute)            |
| `RATE_LIMIT_LOGIN_PER_MINUTE`   | No       | `5`                                              | Login rate limit (attempts/minute)             |
| `REDIS_URL`                     | No       | `""`                                             | Redis URL (optional, for production rate limiting) |
| `SENTRY_DSN`                    | No       | `""`                                             | Sentry DSN for error tracking                  |
| `OTEL_EXPORTER_OTLP_ENDPOINT`   | No       | `http://localhost:4317`                           | OpenTelemetry collector endpoint               |
| `OCR_ENGINE`                    | No       | `tesseract`                                      | OCR engine (`tesseract`, `google_vision`)      |
| `UPLOAD_DIR`                    | No       | `./uploads`                                      | File upload directory                          |
| `MAX_UPLOAD_SIZE_MB`            | No       | `10`                                             | Maximum upload file size (MB)                  |
| `BACKUP_DIR`                    | No       | `./backups`                                      | Database backup directory                      |
| `BACKUP_RETENTION_DAYS`         | No       | `30`                                             | Backup retention period                        |

> *No* at least one AI provider API key is required (`OPENAI_API_KEY` or `GEMINI_API_KEY`).

### Frontend (`frontend/.env.local`)

| Variable                  | Required | Default                                | Description                     |
|---------------------------|----------|----------------------------------------|---------------------------------|
| `NEXT_PUBLIC_API_URL`     | **Yes**  | `http://localhost:8000/api/v1`          | Backend API base URL            |
| `NEXT_PUBLIC_WS_URL`      | No       | `ws://localhost:8000/ws`               | WebSocket URL                   |
| `NEXT_PUBLIC_APP_URL`     | No       | `http://localhost:3000`                | Public app URL                  |
| `NEXT_PUBLIC_APP_NAME`    | No       | `AI Healthcare Assistant`              | Application display name        |
| `NEXT_PUBLIC_ENABLE_CHAT` | No       | `true`                                 | Enable chat feature             |
| `NEXT_PUBLIC_ENABLE_EMERGENCY` | No  | `true`                                 | Enable emergency feature        |
| `NEXT_PUBLIC_ENABLE_REMINDERS` | No  | `true`                                 | Enable reminders feature        |
| `NEXT_PUBLIC_GA_ID`       | No       | `""`                                   | Google Analytics measurement ID |

---

## Database Setup

### Running Migrations

After the database service is running:

```bash
# Docker Compose (VPS)
docker compose -f docker/docker-compose.production.yml exec backend alembic upgrade head

# Railway / Render (through Shell tab)
alembic upgrade head

# Local development
cd backend
alembic upgrade head
```

### Rolling Back Migrations

```bash
# Roll back one step
alembic downgrade -1

# Roll back to initial state
alembic downgrade 0001
```

### Seeding Demo Data

```bash
docker compose -f docker/docker-compose.production.yml exec backend python scripts/import_datasets.py
```

This populates the database with sample patients, doctors, appointments, and medical reports.

### Database Backup & Restore

```bash
# Backup
docker compose -f docker/docker-compose.production.yml exec postgres pg_dump -U healthcare_user healthcare_agent > backup_$(date +%Y%m%d).sql

# Restore
cat backup.sql | docker compose -f docker/docker-compose.production.yml exec -T postgres psql -U healthcare_user healthcare_agent
```

---

## Verification

### Health Check Endpoint

```bash
curl http://<your-domain>/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.8.0"
}
```

### Readiness Probe

```bash
curl http://<your-domain>/ready
```

Expected response:
```json
{
  "status": "ready",
  "checks": {
    "database": "pass",
    "migrations": "pass",
    "graph_registry": "pass",
    "tool_registry": "pass (8 tools)",
    "memory_framework": "pass",
    "ai_provider": "pass",
    "embedding_provider": "pass",
    "vector_store": "pass",
    "retriever": "pass",
    "prompt_manager": "pass",
    "graph_bootstrap": "pass"
  },
  "unready_services": []
}
```

### Liveness Probe

```bash
curl http://<your-domain>/live
```

Expected response:
```json
{
  "status": "alive",
  "timestamp": "2026-07-16T12:00:00.000000+00:00"
}
```

### Deployment Readiness Script

Run the built-in checker for a comprehensive validation:

```bash
docker compose -f docker/docker-compose.production.yml run --rm backend python scripts/check_deployment_readiness.py
```

---

## Production Checklist

- [ ] **Set strong `JWT_SECRET_KEY`** — at least 32 hex characters (`openssl rand -hex 32`)
- [ ] **Configure CORS origins** — set `BACKEND_CORS_ORIGINS` to your frontend domain only
- [ ] **Enable HTTPS** — use a reverse proxy (Caddy, Nginx, or platform-managed TLS)
- [ ] **Disable debug mode** — set `DEBUG=false` and `LOG_LEVEL=INFO`
- [ ] **Configure logging** — set `LOG_FORMAT=json` for structured logging
- [ ] **Set rate limits** — adjust `RATE_LIMIT_PER_MINUTE` and `RATE_LIMIT_LOGIN_PER_MINUTE`
- [ ] **Set up monitoring** — configure Sentry (`SENTRY_DSN`) and OpenTelemetry
- [ ] **Database backups** — verify `BACKUP_DIR` and `BACKUP_RETENTION_DAYS`
- [ ] **Enable CSRF protection** — the `CSRFTokenMiddleware` is already enabled by default
- [ ] **Secrets management** — use environment variables or a vault (never hardcode secrets)
- [ ] **Resource limits** — verify Docker resource limits in `docker-compose.production.yml`
- [ ] **Health checks** — confirm all health check endpoints return `200 OK`
- [ ] **Static file serving** — ensure uploads directory is backed up regularly

### Recommended Caddy Reverse Proxy Setup

Create `Caddyfile`:

```
your-domain.com {
    reverse_proxy localhost:8000
}

frontend.your-domain.com {
    reverse_proxy localhost:3000
}
```

Then run:

```bash
docker run -d -p 80:80 -p 443:443 -v $PWD/Caddyfile:/etc/caddy/Caddyfile -v caddy_data:/data caddy:2
```

---

## Troubleshooting

### Common Issues

| Issue                          | Likely Cause                                | Solution                                                    |
|--------------------------------|---------------------------------------------|-------------------------------------------------------------|
| Backend won't start            | Database not ready / wrong DATABASE_URL     | Check `docker compose logs postgres`; verify `DATABASE_URL` |
| `relation "alembic_version" does not exist` | Migrations not run               | Run `alembic upgrade head`                                  |
| CORS errors in browser         | `BACKEND_CORS_ORIGINS` not set correctly    | Set to exact frontend URL (no trailing slash)               |
| Frontend shows blank page      | Wrong `NEXT_PUBLIC_API_URL`                 | Verify the frontend can reach the backend URL               |
| Rate limiting too strict       | Low `RATE_LIMIT_PER_MINUTE`                 | Increase to `120` or higher for production                  |
| File upload fails              | Missing `uploads` directory / permissions   | Check volume mounts and `UPLOAD_DIR`                     |
| ChromaDB connection refused    | ChromaDB not running / wrong host           | Use `CHROMA_HOST=localhost` to disable external ChromaDB     |
| Out of memory                  | Docker containers lack resource limits      | Add `deploy.resources.limits` to services                   |
| `JWT_SECRET_KEY` warning       | Using default insecure secret               | Generate and set a strong random secret                     |

### Logs Location

- **Docker Compose (VPS):** `docker compose -f docker/docker-compose.production.yml logs -f`
- **Backend logs (container):** `docker compose exec backend tail -f /app/logs/*.log`
- **Render:** Dashboard → Service → **Logs** tab
- **Railway:** Dashboard → Service → **Deployments** → Click deployment → **Logs**

### Health Check Failures

If the readiness probe returns `not_ready`:

1. Check which services are failing from the `unready_services` list
2. **database failure**: Verify `DATABASE_URL` and that PostgreSQL is running
3. **migrations failure**: Run `alembic upgrade head`
4. **ai_provider failure**: Check `GEMINI_API_KEY` or `OPENAI_API_KEY` is valid
5. **vector_store failure**: ChromaDB is unreachable — either start it or set `CHROMA_HOST=localhost` to skip
6. **graph_bootstrap failure**: Check logs for detailed LangGraph bootstrap errors

### Resetting the Application

```bash
# Full reset (WARNING: deletes all data)
docker compose -f docker/docker-compose.production.yml down -v
docker compose -f docker/docker-compose.production.yml up -d
docker compose -f docker/docker-compose.production.yml exec backend alembic upgrade head
```
