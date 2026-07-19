import subprocess
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html
from loguru import logger
from pydantic import BaseModel

from app.api.v1.live import router as live_router
from app.api.v1.metrics import router as metrics_router
from app.api.v1.monitoring import router as monitoring_router
from app.api.v1.ready import router as ready_router
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.langsmith import setup_langsmith
from app.core.logging import setup_logging as setup_loguru_logging
from app.core.logging_config import setup_logging as setup_stdlib_logging
from app.core.metrics import metrics
from app.core.telemetry import setup_opentelemetry
from app.langgraph.bootstrap import GraphBootstrap, set_bootstrap_result
from app.vector_recovery.recovery_manager import RecoveryManager
from app.middleware.cors import setup_cors
from app.middleware.csrf import CSRFTokenMiddleware
from app.middleware.error_handler import setup_error_handlers
from app.middleware.metrics import MetricsMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.sentry import setup_sentry
from app.middleware.tracing import TracingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_loguru_logging()
    setup_stdlib_logging()
    logger.info(f"Starting {settings.PROJECT_NAME} v1.0.0")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Resolved CORS origins: {settings.cors_origins}")
    logger.info("CORS origin regex: https://.*\\.vercel\\.app")

    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5
        ).stdout.strip()
        logger.info(f"Deployed commit: {sha}")
    except Exception:
        logger.info("Deployed commit: unknown (git not available)")

    setup_sentry(app)
    setup_langsmith()

    logger.info("Checking OCR subsystem...")
    import shutil
    if shutil.which("tesseract"):
        import subprocess
        try:
            ver = subprocess.run(["tesseract", "--version"], capture_output=True, text=True, timeout=5)
            logger.info(f"OCR: tesseract available — {ver.stdout.split(chr(10))[0] if ver.stdout else 'unknown'}")
        except Exception:
            logger.warning("OCR: tesseract binary found but version check failed")
    else:
        logger.warning("OCR: tesseract not found — document processing may fail")

    logger.info("Bootstrapping LangGraph runtime...")
    bootstrap_result = GraphBootstrap.run_full_bootstrap()
    set_bootstrap_result(bootstrap_result)
    if bootstrap_result.success:
        logger.info("LangGraph runtime ready")
    else:
        logger.warning(
            f"LangGraph runtime started with {len(bootstrap_result.validation_errors)} issues"
        )

    logger.info("Resetting reports stuck in PROCESSING state...")
    try:
        from app.database.enums import ReportStatus
        from app.database.session import SessionLocal
        from app.models.report import Report
        db_session = SessionLocal()
        stuck = db_session.query(Report).filter(Report.status == ReportStatus.PROCESSING.value).all()
        for r in stuck:
            r.status = ReportStatus.FAILED.value
            r.error_message = "Server restarted during processing — report was in incomplete state"
            r.processed_at = datetime.now(timezone.utc)
        db_session.commit()
        if stuck:
            logger.warning(f"Reset {len(stuck)} reports from PROCESSING to FAILED")
        db_session.close()
    except Exception as exc:
        logger.warning(f"Failed to reset PROCESSING reports: {exc}")

    logger.info("Running vector index recovery...")
    try:
        recovery_mgr = RecoveryManager()
        vector_health = recovery_mgr.run_startup_recovery()
        logger.info(f"Vector index status: {vector_health.status} "
                    f"({vector_health.indexed_reports}/{vector_health.total_reports} reports indexed)")
        app.state.vector_health = vector_health
    except Exception as exc:
        logger.warning(f"Vector index recovery failed: {exc}")
        app.state.vector_health = None

    yield

    logger.info("Closing vector store...")
    try:
        from app.vector_store.vector_service import VectorService
        vs = VectorService()
        vs.close()
    except Exception:
        pass

    logger.info("Shutting down application")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered healthcare follow-up assistant for post-discharge patient monitoring",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
    lifespan=lifespan,
    servers=[{"url": "/"}],
)

REDOC_CDN_URL = "https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"


@app.get("/redoc", include_in_schema=False)
def overridden_redoc():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url=REDOC_CDN_URL,
    )


setup_cors(app)
setup_error_handlers(app)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(TracingMiddleware)
app.add_middleware(MetricsMiddleware)

if settings.ENABLE_CSRF_PROTECTION:
    app.add_middleware(CSRFTokenMiddleware)

if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(RateLimitMiddleware)

if settings.SECURITY_HEADERS_ENABLED:
    app.add_middleware(SecurityHeadersMiddleware)

app.include_router(api_router)
app.include_router(ready_router)
app.include_router(live_router)
app.include_router(metrics_router)

setup_opentelemetry(app)


class HealthResponse(BaseModel):
    status: str
    version: str
    vector_store: str


@app.get("/health", response_model=HealthResponse)
def root_health():
    vector_status = "unknown"
    try:
        vh = getattr(app.state, "vector_health", None)
        if vh:
            vector_status = vh.status
    except Exception:
        pass
    return {"status": "healthy", "version": "1.0.0", "vector_store": vector_status}


@app.get("/")
def root():
    return {
        "message": "AI Healthcare Follow-up Assistant API",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0",
    }


@app.get("/metrics", include_in_schema=False)
def app_metrics():
    from starlette.responses import JSONResponse
    return JSONResponse(metrics.snapshot())
