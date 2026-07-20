import subprocess
import time as _time
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
    _startup_t0 = _time.perf_counter()
    _timings = {}

    setup_loguru_logging()
    setup_stdlib_logging()

    import os
    import platform as _platform
    from datetime import datetime, timezone as _tz

    logger.info("=" * 58)
    logger.info(f"BUILD {os.environ.get('RENDER_GIT_COMMIT', 'local-dev')}")
    logger.info(f"STARTUP {datetime.now(_tz.utc).isoformat()}")
    logger.info(f"PLATFORM {_platform.platform()}")
    logger.info(f"PYTHON {_platform.python_version()}")
    logger.info(f"PID {os.getpid()}")
    logger.info("=" * 58)

    logger.info(f"Starting {settings.PROJECT_NAME} v1.0.0")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Resolved CORS origins: {settings.cors_origins}")
    logger.info("CORS origin regex: https://.*\\.vercel\\.app")

    _t = _time.perf_counter()
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5
        ).stdout.strip()
        logger.info(f"Deployed commit: {sha}")
    except Exception:
        logger.info("Deployed commit: unknown (git not available)")
    _timings["git_commit"] = _time.perf_counter() - _t

    _t = _time.perf_counter()
    setup_sentry(app)
    _timings["sentry"] = _time.perf_counter() - _t

    _t = _time.perf_counter()
    setup_langsmith()
    _timings["langsmith"] = _time.perf_counter() - _t

    _t = _time.perf_counter()
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
    _timings["ocr_check"] = _time.perf_counter() - _t

    _t = _time.perf_counter()
    logger.info("Bootstrapping LangGraph runtime...")
    bootstrap_result = GraphBootstrap.run_full_bootstrap()
    set_bootstrap_result(bootstrap_result)
    if bootstrap_result.success:
        logger.info("LangGraph runtime ready")
    else:
        logger.warning(
            f"LangGraph runtime started with {len(bootstrap_result.validation_errors)} issues"
        )
    _timings["langgraph"] = _time.perf_counter() - _t

    _t = _time.perf_counter()
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
    _timings["db_reset"] = _time.perf_counter() - _t

    _t = _time.perf_counter()
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
    _timings["vector_recovery"] = _time.perf_counter() - _t

    logger.info("=" * 58)
    logger.info("EMBEDDING DIAGNOSTICS")
    logger.info(f"EMBEDDING_PROVIDER={settings.EMBEDDING_PROVIDER!r}")
    logger.info(f"EMBEDDING_MODEL={settings.EMBEDDING_MODEL!r}")
    logger.info(f"GEMINI_API_KEY_EXISTS={bool(settings.GEMINI_API_KEY)}")
    logger.info(f"GEMINI_API_KEY_LENGTH={len(settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else 0}")
    logger.info(f"GEMINI_API_KEY_FIRST4={settings.GEMINI_API_KEY[:4] if settings.GEMINI_API_KEY else '(none)'}")
    logger.info(f"CHROMA_HOST={settings.CHROMA_HOST!r}")
    logger.info(f"CHROMA_PORT={settings.CHROMA_PORT!r}")
    logger.info(f"CHROMA_COLLECTION_NAME={settings.CHROMA_COLLECTION_NAME!r}")
    logger.info("=" * 58)

    _total = _time.perf_counter() - _startup_t0
    logger.info("=" * 58)
    logger.info("STARTUP TIMELINE")
    for name, secs in sorted(_timings.items(), key=lambda x: -x[1]):
        logger.info(f"  {name:25s} {secs:.3f}s")
    logger.info(f"  {'TOTAL':25s} {_total:.3f}s")
    logger.info("=" * 58)

    yield

    logger.info("Closing vector store...")
    try:
        from app.vector_store.vector_service import VectorService
        vs = VectorService()
        vs.close()
    except Exception:
        pass

    logger.info("Shutting down application")


logger.info(f"[STARTUP TIMING] Module imports completed at T+{_time.perf_counter():.3f}s")

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


_t0_init = _time.perf_counter()
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

_t_otel = _time.perf_counter()
setup_opentelemetry(app)
logger.info(f"[STARTUP TIMING] Middleware+routers+otel T+{_time.perf_counter() - _t0_init:.3f}s (otel={_time.perf_counter() - _t_otel:.3f}s)")


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
