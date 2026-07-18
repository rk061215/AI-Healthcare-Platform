# ──────────────────────────────────────────────────────────────
# Render CLI Developer Workflow
# AI Healthcare Platform v1.0.0
# ──────────────────────────────────────────────────────────────
# Render CLI is fully optional — it is NOT a runtime dependency.
# All deployment automation uses Render Blueprint (render.yaml).
# ──────────────────────────────────────────────────────────────
# Requirements:
#   - Render CLI installed (https://render.com/docs/cli)
#   - Authenticated:  render login  or  RENDER_API_KEY env var
# ──────────────────────────────────────────────────────────────

RENDER              ?= render
RENDER_SERVICE      ?= healthcare-backend
RENDER_FRONTEND     ?= healthcare-frontend
RENDER_BACKEND_URL  ?= https://healthcare-backend.onrender.com

.PHONY: deploy redeploy logs status list dashboard tail restart \
        verify health ready live env-check help

help:
	@echo "Render CLI Developer Commands"
	@echo "─────────────────────────────"
	@echo "Available targets (all optional — Render CLI not required for dev):"
	@echo ""
	@echo "  deploy        Deploy entire Blueprint (render.yaml)"
	@echo "  redeploy      Trigger a Blueprint redeploy"
	@echo "  logs          Stream backend service logs"
	@echo "  status        Show service status overview"
	@echo "  list          List all services"
	@echo "  dashboard     Open Render dashboard in browser"
	@echo "  tail          Tail backend logs (alias for logs)"
	@echo "  restart       Restart backend service"
	@echo "  verify        Full deployment verification"
	@echo "  health        GET /health (backend)"
	@echo "  ready         GET /api/v1/monitoring/ready"
	@echo "  live          GET /api/v1/monitoring/live"
	@echo "  env-check     Verify required Render secrets exist"
	@echo ""
	@echo "Variables (override with e.g. 'make deploy RENDER_BACKEND_URL=...'):"
	@echo "  RENDER            Render CLI binary path  (default: render)"
	@echo "  RENDER_SERVICE    Backend service name     (default: healthcare-backend)"
	@echo "  RENDER_FRONTEND   Frontend service name    (default: healthcare-frontend)"
	@echo "  RENDER_BACKEND_URL  Backend URL for health checks (default: https://...onrender.com)"

# ── Deployment ───────────────────────────────────────────────

deploy:
	$(RENDER) blueprint deploy

redeploy:
	$(RENDER) deployments create --blueprint

# ── Observability ────────────────────────────────────────────

logs:
	$(RENDER) logs --service $(RENDER_SERVICE) --tail

status:
	$(RENDER) services list

list:
	$(RENDER) services list

dashboard:
	$(RENDER) open dashboard

tail: logs

restart:
	$(RENDER) services restart $(RENDER_SERVICE)

# ── Health Verification ──────────────────────────────────────

verify: health ready live status

health:
	@echo "=== /health ==="
	@curl -s --max-time 10 "$(RENDER_BACKEND_URL)/health" | python -m json.tool || echo "[FAIL]"

ready:
	@echo "=== /api/v1/monitoring/ready ==="
	@curl -s -o /dev/null -w "HTTP %{http_code} / %{time_total}s\n" --max-time 10 "$(RENDER_BACKEND_URL)/api/v1/monitoring/ready" || echo "[FAIL]"

live:
	@echo "=== /api/v1/monitoring/live ==="
	@curl -s -o /dev/null -w "HTTP %{http_code} / %{time_total}s\n" --max-time 10 "$(RENDER_BACKEND_URL)/api/v1/monitoring/live" || echo "[FAIL]"

# ── Environment Validation ───────────────────────────────────

env-check:
	@echo "=== Render Secrets: $(RENDER_SERVICE) ==="
	@$(RENDER) secrets list --service $(RENDER_SERVICE) 2>/dev/null || echo "[AUTH REQUIRED] Run 'render login' first"
	@echo ""
	@echo "Note: Secrets DATABASE_URL, JWT_SECRET_KEY, GEMINI_API_KEY"
	@echo "      are defined in render.yaml with 'sync: false' and"
	@echo "      must be set manually in the Render Dashboard."
