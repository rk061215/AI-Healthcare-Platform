# Render CLI Guide — AI Healthcare Platform v1.0.0

> Render CLI is an **optional developer tool** for deployment automation,
> debugging, and CI/CD. It is NOT a runtime dependency.
> The application remains fully cloud-provider independent.

## Table of Contents

1. [Installation](#1-installation)
2. [Authentication](#2-authentication)
3. [Project Configuration](#3-project-configuration)
4. [Common Commands](#4-common-commands)
5. [Deployment Workflow](#5-deployment-workflow)
6. [Health Verification](#6-health-verification)
7. [Environment Validation](#7-environment-validation)
8. [Logging & Troubleshooting](#8-logging--troubleshooting)
9. [CI/CD Integration](#9-cicd-integration)
10. [Rollback](#10-rollback)
11. [FAQ](#11-faq)

---

## 1. Installation

### Windows (PowerShell)

```powershell
# Install using winget
winget install Render.CLI

# Or using npm (requires Node.js)
npm install -g @renderinc/cli

# Verify
render --version
```

### Linux

```bash
# Install using npm (requires Node.js)
npm install -g @renderinc/cli

# Or download binary directly
curl -fsSL https://render.com/install.sh | sh

# Verify
render --version
```

### macOS

```bash
# Install using Homebrew
brew install render-cli

# Or using npm
npm install -g @renderinc/cli

# Verify
render --version
```

### Upgrade

```bash
# npm global
npm update -g @renderinc/cli

# Homebrew (macOS)
brew upgrade render-cli

# Windows (winget)
winget upgrade Render.CLI
```

### Uninstall

```bash
# npm
npm uninstall -g @renderinc/cli

# Homebrew (macOS)
brew uninstall render-cli

# Windows (winget)
winget uninstall Render.CLI
```

---

## 2. Authentication

### Interactive Login (recommended)

```bash
render login
```

Opens a browser window to authenticate with your Render account.
Generates an API key scoped to your user account.

### Non-Interactive (CI/CD)

Set the `RENDER_API_KEY` environment variable:

```bash
export RENDER_API_KEY="rnd_xxxxxxxxxxxx"
```

> **Security**: Never hardcode tokens in source code or configuration files.
> API keys are available in: Render Dashboard → Account Settings → API Keys.

### Least-Privilege Practices

| Practice | Recommendation |
|----------|---------------|
| **Scope** | Use API keys with minimal required permissions (deploy, read logs) |
| **Rotation** | Rotate API keys every 90 days |
| **Secrets** | Store API keys in GitHub Secrets / Render Dashboard, never in code |
| **Sharing** | Do not share personal login sessions — each developer authenticates independently |

---

## 3. Project Configuration

### Repository Structure

```
AI-Healthcare-Platform/
├── render.yaml              # Render Blueprint (root — required by spec)
├── AI-Healthcare-Agent/
│   ├── backend/             # FastAPI backend (Docker)
│   ├── frontend/            # Next.js frontend (Docker)
│   ├── Makefile             # `make deploy`, `make logs`, etc.
│   └── scripts/
│       ├── render.ps1       # PowerShell equivalent
│       ├── migrate.sh       # DB migration helper
│       └── setup.ps1        # Environment setup
├── docker/
└── .github/workflows/       # CI only — deployment via Blueprint
```

### How Render CLI Maps to render.yaml

The `render.yaml` file at the repository root defines:

| CLI Command | Blueprint Equivalent |
|-------------|---------------------|
| `render blueprint deploy` | Reads `render.yaml`, creates/updates all services |
| `render services list` | Lists services defined under `services:` |
| `render logs --service <name>` | Tails logs for the named service |
| `render open dashboard` | Opens the web UI to inspect your Blueprint |

### Services Defined

| Service | Type | Plan | Health Check |
|---------|------|------|--------------|
| `healthcare-backend` | Web (Docker) | Free | `GET /health` |
| `healthcare-frontend` | Web (Docker) | Free | `GET /` |

### Environment

| Variable | Source | Set Via |
|----------|--------|---------|
| `DATABASE_URL` | Neon PostgreSQL | Render Dashboard secret (`sync: false`) |
| `JWT_SECRET_KEY` | Developer generates | Render Dashboard secret (`sync: false`) |
| `GEMINI_API_KEY` | Google AI Studio | Render Dashboard secret (`sync: false`) |
| Other env vars | Code defaults / render.yaml static values | `render.yaml` `value:` |

---

## 4. Common Commands

### Using Make (Unix / WSL / Git Bash)

```bash
# Deploy
make deploy

# Stream logs
make logs

# Check status
make status

# Full verification
make verify

# Environment check
make env-check
```

### Using PowerShell

```powershell
.\scripts\render.ps1 deploy
.\scripts\render.ps1 logs
.\scripts\render.ps1 status
.\scripts\render.ps1 verify
.\scripts\render.ps1 env-check
```

### Target Reference

| Command | Make Target | PowerShell | Description |
|---------|-----------|------------|-------------|
| Deploy | `make deploy` | `render.ps1 deploy` | Deploy entire Blueprint |
| Redeploy | `make redeploy` | `render.ps1 redeploy` | Trigger Blueprint redeploy |
| Logs | `make logs` | `render.ps1 logs` | Stream backend logs |
| Status | `make status` | `render.ps1 status` | List all services |
| Dashboard | `make dashboard` | `render.ps1 dashboard` | Open Render Dashboard |
| Restart | `make restart` | `render.ps1 restart` | Restart backend service |
| Verify | `make verify` | `render.ps1 verify` | Health checks + service status |
| Env Check | `make env-check` | `render.ps1 env-check` | Verify secrets configured |

---

## 5. Deployment Workflow

### First Deployment

```bash
# 1. Authenticate
render login

# 2. Set required secrets in Render Dashboard
#    - DATABASE_URL (Neon connection string)
#    - JWT_SECRET_KEY (openssl rand -hex 32)
#    - GEMINI_API_KEY

# 3. Deploy
render blueprint deploy
```

### Subsequent Deployments

```bash
# Option A: Deploy entire Blueprint
make deploy

# Option B: Trigger redeploy via API
make redeploy
```

### Post-Deployment Verification

```bash
make verify
```

Expected output:
- `/health` → `{"status": "healthy", "version": "1.0.0", ...}`
- `/ready` → HTTP 200 (accepts traffic)
- `/live` → HTTP 200 (alive)

### Automated Deployment

Render automatically deploys when you push to the `main` branch
(the Blueprint is connected to the repository via GitHub integration).
Deployment is also triggered by:

1. **Git push** → automatic (if connected via Render Dashboard)
2. **Manual** → `render blueprint deploy` or Render Dashboard "Deploy" button
3. **Scheduled** → Render Dashboard → Service → Settings → Auto-Deploy

---

## 6. Health Verification

```bash
# Quick health check
make health

# Readiness check
make ready

# Liveness check
make live

# Full suite
make verify
```

### What Each Endpoint Checks

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `GET /health` | General health + vector store status | `{"status": "healthy", "version": "1.0.0"}` |
| `GET /api/v1/monitoring/health` | Detailed component-by-component health | Full health report |
| `GET /api/v1/monitoring/ready` | Readiness — accept traffic? | HTTP 200 OK |
| `GET /api/v1/monitoring/live` | Liveness — process alive? | HTTP 200 OK |

### Response Time

| Endpoint | Expected Latency |
|----------|-----------------|
| `/health` | < 200ms |
| `/ready` | < 500ms |
| `/live` | < 100ms |

---

## 7. Environment Validation

```bash
make env-check
```

Checks that required Render secrets are configured for the backend service:

| Secret | Required | Notes |
|--------|----------|-------|
| `DATABASE_URL` | Yes | Neon PostgreSQL connection string |
| `JWT_SECRET_KEY` | Yes | Generate with `openssl rand -hex 32` |
| `GEMINI_API_KEY` | Yes | From Google AI Studio |

The command reports each secret as **Configured** or **Missing** without exposing their values.

> **Note**: These secrets are defined in `render.yaml` with `sync: false`,
> meaning they must be set manually in the Render Dashboard or via the Render CLI.
> They are NOT stored in version control.

---

## 8. Logging & Troubleshooting

### Stream Backend Logs

```bash
make logs
# or
render logs --service healthcare-backend --tail
```

### Inspect Deployment Logs

```bash
render deployments list --service healthcare-backend
render deployments logs <deployment-id>
```

### Common Failure Patterns

| Symptom | Likely Cause | Check |
|---------|-------------|-------|
| Container crashes on startup | Missing secret | `make env-check` |
| Migration fails | Wrong `DATABASE_URL` | Check secret value in Dashboard |
| Health check fails (502) | App not ready in time | Check startup logs for errors |
| Vector search returns empty | ChromaDB not rebuilt | Check recovery startup log |
| Frontend can't reach backend | CORS or URL mismatch | Verify `BACKEND_CORS_ORIGINS` |

### Diagnostic Commands

```bash
# View deployment history
render deployments list --service healthcare-backend

# Inspect specific deployment
render deployments logs <deployment-id>

# Restart service (does NOT redeploy — keeps same image)
make restart

# Check service status
make status
```

### Identifying Failures in Logs

```bash
# Search for startup failures
render logs --service healthcare-backend --tail | grep -i error

# Search for migration failures
render logs --service healthcare-backend --tail | grep -i migrate

# Search for health check failures
render logs --service healthcare-backend --tail | grep -i health

# Search for container crashes
render logs --service healthcare-backend --tail | grep -i "exit\|crash\|killed"
```

---

## 9. CI/CD Integration

### Current CI Pipeline

The project uses two GitHub Actions workflows:

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `backend-ci.yml` | Push/PR on `backend/**` | Lint + test Python backend |
| `frontend-ci.yml` | Push/PR on `frontend/**` | Lint + test Next.js frontend |

### Deployment Automation

Deployment is handled **entirely by Render Blueprint** via the GitHub integration.
Render CLI is NOT used in CI/CD — the Blueprint auto-deploys on push to `main`.

### Optional Render CLI Usage in CI/CD

If you want manual deployment verification or ad-hoc deployments from CI:

```yaml
# Example: Add to an existing workflow for deployment verification
- name: Verify deployment
  run: |
    npm install -g @renderinc/cli
    export RENDER_API_KEY=${{ secrets.RENDER_API_KEY }}
    render blueprint deploy
  # ⚠️ This is optional — Blueprint auto-deploy is the primary method
```

> **Recommendation**: Keep Blueprint auto-deploy as the primary mechanism.
> Render CLI in CI should only be used for:
> - Manual deployment approval gates
> - Post-deployment health verification
> - Emergency rollback automation

---

## 10. Rollback

```bash
# List recent deployments to find the rollback target
render deployments list --service healthcare-backend

# Roll back to a specific deployment
render deployments rollback <deployment-id>

# Or redeploy a previous Blueprint version
git checkout <previous-commit>
make deploy
git checkout main  # restore
```

> **Note**: Rollback via Render CLI reverts the service to a previous image.
> For database-related rollbacks, you must also restore the database
> (Neon supports point-in-time recovery).

---

## 11. FAQ

**Q: Does the application require Render CLI to run?**

No. Render CLI is strictly a developer productivity tool. The application
runs identically on any platform (Render, Docker, local, cloud VM).

**Q: Is there vendor lock-in?**

No. The application has zero runtime dependencies on Render. The Blueprint
(`render.yaml`) is a deployment configuration — the same Docker images can
be deployed anywhere (Kubernetes, ECS, Nomad, manual Docker).

**Q: Can I deploy without Render CLI?**

Yes. Push to `main` — the Render GitHub integration auto-deploys via Blueprint.
You can also deploy directly from the Render Dashboard.

**Q: What if I don't have `make` on Windows?**

Use the PowerShell script instead:

```powershell
.\scripts\render.ps1 deploy
```

**Q: How do I set secrets?**

In the Render Dashboard:
1. Select the service (healthcare-backend)
2. Go to Environment → Secrets Files
3. Add each secret: DATABASE_URL, JWT_SECRET_KEY, GEMINI_API_KEY

Or via CLI (for development):

```bash
render secrets set --service healthcare-backend DATABASE_URL "postgresql://..."
```

**Q: How does vector recovery work after deployment?**

See [ADR-028: Index as Derived State](ADR-028_VECTOR_STORAGE_STRATEGY.md)
and [Automatic Vector Recovery Report](project_memory/AUTOMATIC_VECTOR_RECOVERY_REPORT.md).

The RecoveryManager automatically compares `document_count` vs `indexed_reports`
on startup and triggers a rebuild if ChromaDB is stale.
