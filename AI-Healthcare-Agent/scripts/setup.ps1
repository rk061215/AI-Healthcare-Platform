# ──────────────────────────────────────────────
# Project Setup Script (Windows PowerShell)
# ──────────────────────────────────────────────

Write-Host "AI Healthcare Follow-up Assistant - Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check prerequisites
$hasPython = Get-Command python -ErrorAction SilentlyContinue
$hasNode = Get-Command node -ErrorAction SilentlyContinue
$hasDocker = Get-Command docker -ErrorAction SilentlyContinue

if (-not $hasPython) {
    Write-Host "ERROR: Python 3.12+ is required" -ForegroundColor Red
    exit 1
}

if (-not $hasNode) {
    Write-Host "ERROR: Node.js 20+ is required" -ForegroundColor Red
    exit 1
}

# Setup backend
Write-Host "`nSetting up backend..." -ForegroundColor Yellow
Set-Location backend

if (-not (Test-Path -Path ".venv")) {
    python -m venv .venv
    Write-Host "Python virtual environment created" -ForegroundColor Green
}

& .\.venv\Scripts\pip install -r requirements.txt
Write-Host "Backend dependencies installed" -ForegroundColor Green

if (-not (Test-Path -Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Backend .env created from .env.example" -ForegroundColor Green
}

Set-Location ..

# Setup frontend
Write-Host "`nSetting up frontend..." -ForegroundColor Yellow
Set-Location frontend

npm install
Write-Host "Frontend dependencies installed" -ForegroundColor Green

if (-not (Test-Path -Path ".env.local")) {
    Copy-Item ".env.local.example" ".env.local"
    Write-Host "Frontend .env.local created from .env.local.example" -ForegroundColor Green
}

Set-Location ..

# Docker setup
if ($hasDocker) {
    Write-Host "`nDocker is available. You can start services with:" -ForegroundColor Yellow
    Write-Host "  docker compose -f docker/docker-compose.yml up -d" -ForegroundColor Cyan
}

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host "`nTo start development:" -ForegroundColor Cyan
Write-Host "  1. Start PostgreSQL: docker compose -f docker/docker-compose.yml up postgres -d" -ForegroundColor White
Write-Host "  2. Run migrations:   cd backend && alembic upgrade head" -ForegroundColor White
Write-Host "  3. Start backend:    cd backend && uvicorn app.main:app --reload" -ForegroundColor White
Write-Host "  4. Start frontend:   cd frontend && npm run dev" -ForegroundColor White
