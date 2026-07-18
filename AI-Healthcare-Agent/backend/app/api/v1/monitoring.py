from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.metrics import metrics
from app.database.session import get_db
from app.vector_recovery.recovery_manager import RecoveryManager
from app.vector_store.vector_service import VectorService

APP_VERSION = "1.0.0"

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
        vs = VectorService()
        health = vs.health_check()
        store_health = health.get("vector_store", {})
        embed_health = health.get("embedding_service", {})
        services["vector_store"] = store_health.get("status", "degraded")
        services["embedding_service"] = embed_health.get("status", "degraded")
        services["vector_store_details"] = {
            "provider": store_health.get("provider"),
            "collection": store_health.get("collection"),
            "document_count": store_health.get("document_count"),
            "distance_function": store_health.get("distance_function"),
        }
    except Exception:
        services["vector_store"] = "degraded"
        services["embedding_service"] = "degraded"

    try:
        mgr = RecoveryManager()
        vh = mgr.check_health()
        services["vector_recovery"] = vh.status
        services["vector_recovery_details"] = {
            "indexed_reports": vh.indexed_reports,
            "total_reports": vh.total_reports,
            "pending_rebuild": vh.pending_rebuild_count,
            "failed_rebuild": vh.failed_rebuild_count,
            "rebuild_in_progress": vh.rebuild_in_progress,
            "embedding_model_version": vh.embedding_model_version,
            "collection_exists": vh.collection_exists,
        }
    except Exception:
        services["vector_recovery"] = "degraded"

    status_keys = {k: v for k, v in services.items() if not k.endswith("_details")}
    overall = "ready" if all(v in ("ok", "healthy") for v in status_keys.values()) else "degraded"

    return {"status": overall, "services": services}


@router.get("/live")
def liveness_check():
    return {"status": "alive"}
