from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

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
    logger.info(f"Starting {settings.PROJECT_NAME} v0.8.0")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    setup_sentry(app)
    setup_langsmith()

    logger.info("Bootstrapping LangGraph runtime...")
    bootstrap_result = GraphBootstrap.run_full_bootstrap()
    set_bootstrap_result(bootstrap_result)
    if bootstrap_result.success:
        logger.info("LangGraph runtime ready")
    else:
        logger.warning(
            f"LangGraph runtime started with {len(bootstrap_result.validation_errors)} issues"
        )

    yield

    logger.info("Shutting down application")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered healthcare follow-up assistant for post-discharge patient monitoring",
    version="0.8.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
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


@app.get("/health")
def root_health():
    return {"status": "healthy", "version": "0.8.0"}


@app.get("/")
def root():
    return {
        "message": "AI Healthcare Follow-up Assistant API",
        "docs": "/docs",
        "health": "/health",
        "version": "0.8.0",
    }


@app.get("/metrics", include_in_schema=False)
def app_metrics():
    from starlette.responses import JSONResponse
    return JSONResponse(metrics.snapshot())
