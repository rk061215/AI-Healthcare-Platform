from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.metrics import metrics
from app.database.session import get_db

APP_VERSION = "0.8.0"

router = APIRouter(tags=["Monitoring"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "degraded"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "version": APP_VERSION,
        "uptime_seconds": metrics.snapshot()["uptime_seconds"],
        "database": db_status,
    }


@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    services = {}

    try:
        db.execute(text("SELECT 1"))
        services["database"] = "ok"
    except Exception:
        services["database"] = "degraded"

    try:
        import chromadb
        from app.core.config import settings as cfg
        client = chromadb.HttpClient(
            host=cfg.CHROMA_HOST, port=cfg.CHROMA_PORT
        )
        client.heartbeat()
        services["chromadb"] = "ok"
    except Exception:
        services["chromadb"] = "degraded"

    overall = "ready" if all(v == "ok" for v in services.values()) else "degraded"

    return {"status": overall, "services": services}


@router.get("/live")
def liveness_check():
    return {"status": "alive"}
