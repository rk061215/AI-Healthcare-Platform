# ──────────────────────────────────────────────────────────────
# Render CLI Developer Workflow — PowerShell
# AI Healthcare Platform v1.0.0
# ──────────────────────────────────────────────────────────────
# Render CLI is fully optional — it is NOT a runtime dependency.
# All deployment automation uses Render Blueprint (render.yaml).
# ──────────────────────────────────────────────────────────────
# Requirements:
#   - Render CLI installed (https://render.com/docs/cli)
#   - Authenticated:  render login  or  $env:RENDER_API_KEY
# ──────────────────────────────────────────────────────────────

param (
    [string]$Command = "help",
    [string]$Service = "healthcare-backend",
    [string]$BackendUrl = "https://healthcare-backend.onrender.com"
)

$ErrorActionPreference = "Stop"

function Show-Help {
    Write-Host @"
Render CLI Developer Commands (PowerShell)
─────────────────────────────────────────────
All commands are optional — Render CLI is NOT required for development.

Usage:  .\scripts\render.ps1 <command>

Commands:
  deploy        Deploy entire Blueprint (render.yaml)
  redeploy      Trigger a Blueprint redeploy
  logs          Stream backend service logs
  status        Show service status overview
  list          List all services
  dashboard     Open Render dashboard in browser
  tail          Tail backend logs (alias for logs)
  restart       Restart backend service
  verify        Full deployment verification
  health        GET /health (backend)
  ready         GET /api/v1/monitoring/ready
  live          GET /api/v1/monitoring/live
  env-check     Verify required Render secrets exist
  help          Show this help message

Examples:
  .\scripts\render.ps1 deploy
  .\scripts\render.ps1 logs
  .\scripts\render.ps1 verify -BackendUrl "https://your-app.onrender.com"
"@
}

function Invoke-RenderCLI {
    param([string]$Arguments)
    try {
        $output = & render $Arguments 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Render CLI returned exit code $LASTEXITCODE"
        }
        $output | ForEach-Object { Write-Host $_ }
    } catch {
        Write-Error "Render CLI not found. Install from https://render.com/docs/cli"
        exit 1
    }
}

function Invoke-HealthCheck {
    param([string]$Path)
    $url = "$BackendUrl$Path"
    try {
        $response = Invoke-WebRequest -Uri $url -Method GET -TimeoutSec 10 -UseBasicParsing
        $elapsed = [math]::Round(($response.RawContentLength -eq 0 ? 0 : 0), 3)
        Write-Host "HTTP $($response.StatusCode) / $elapsed`s"
    } catch {
        $statusCode = if ($_.Exception.Response) { $_.Exception.Response.StatusCode.value__ } else { "FAIL" }
        Write-Host "[$statusCode] $($_.Exception.Message)"
    }
}

# ── Dispatch ─────────────────────────────────────────────────

switch ($Command.ToLower()) {
    "deploy"    { Invoke-RenderCLI "blueprint deploy" }
    "redeploy"  { Invoke-RenderCLI "deployments create --blueprint" }
    "logs"      { Invoke-RenderCLI "logs --service $Service --tail" }
    "tail"      { Invoke-RenderCLI "logs --service $Service --tail" }
    "status"    { Invoke-RenderCLI "services list" }
    "list"      { Invoke-RenderCLI "services list" }
    "dashboard" { Invoke-RenderCLI "open dashboard" }
    "restart"   { Invoke-RenderCLI "services restart $Service" }

    "health" {
        Write-Host "=== /health ==="
        Invoke-HealthCheck "/health"
    }
    "ready" {
        Write-Host "=== /api/v1/monitoring/ready ==="
        Invoke-HealthCheck "/api/v1/monitoring/ready"
    }
    "live" {
        Write-Host "=== /api/v1/monitoring/live ==="
        Invoke-HealthCheck "/api/v1/monitoring/live"
    }

    "verify" {
        Write-Host "=== Deployment Verification ==="
        Write-Host ""
        Write-Host "--- Health ---"
        Invoke-HealthCheck "/health"
        Write-Host ""
        Write-Host "--- Monitoring Health ---"
        Invoke-HealthCheck "/api/v1/monitoring/health"
        Write-Host ""
        Write-Host "--- Ready ---"
        Invoke-HealthCheck "/api/v1/monitoring/ready"
        Write-Host ""
        Write-Host "--- Live ---"
        Invoke-HealthCheck "/api/v1/monitoring/live"
        Write-Host ""
        Write-Host "--- Services ---"
        Invoke-RenderCLI "services list"
    }

    "env-check" {
        Write-Host "=== Render Secrets: $Service ==="
        try {
            & render secrets list --service $Service 2>&1 | ForEach-Object { Write-Host $_ }
        } catch {
            Write-Error "Not authenticated — run 'render login' first"
        }
        Write-Host ""
        Write-Host "Note: Secrets DATABASE_URL, JWT_SECRET_KEY, GEMINI_API_KEY"
        Write-Host "      are defined in render.yaml with 'sync: false' and"
        Write-Host "      must be set manually in the Render Dashboard."
    }

    default { Show-Help }
}
