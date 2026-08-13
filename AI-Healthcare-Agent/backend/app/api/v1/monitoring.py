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
            "actual_document_count": vh.actual_document_count,
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


@router.get("/vector-validate")
def vector_store_validate():
    """Phase D: Vector store validation endpoint."""
    import time as _time
    results = {}

    t0 = _time.perf_counter()
    try:
        vs = VectorService()
        health = vs.health_check()
        store_h = health.get("vector_store", {})
        results["collection_exists"] = store_h.get("status") == "ok"
        results["vector_count"] = store_h.get("document_count", 0)
        results["dimension"] = store_h.get("dimension")
        results["distance_function"] = store_h.get("distance_function")
    except Exception as e:
        results["error"] = str(e)
        results["collection_exists"] = False
    results["collection_check_ms"] = round((_time.perf_counter() - t0) * 1000, 1)

    t0 = _time.perf_counter()
    try:
        from app.database.session import SessionLocal
        db = SessionLocal()
        try:
            indexed = db.execute(
                text("SELECT COUNT(*) FROM vector_index_state WHERE index_status = 'indexed'")
            ).scalar()
            total = db.execute(text("SELECT COUNT(*) FROM reports")).scalar()
            results["indexed_reports"] = indexed
            results["total_reports"] = total
            results["coverage"] = f"{indexed}/{total}" if total else "0/0"
        finally:
            db.close()
    except Exception as e:
        results["db_error"] = str(e)
    results["db_check_ms"] = round((_time.perf_counter() - t0) * 1000, 1)

    t0 = _time.perf_counter()
    try:
        vs = VectorService()
        search_results = vs.search(query="health check", k=1)
        results["search_latency_ms"] = round((_time.perf_counter() - t0) * 1000, 1)
        results["search_works"] = True
    except Exception as e:
        results["search_works"] = False
        results["search_error"] = str(e)
        results["search_latency_ms"] = round((_time.perf_counter() - t0) * 1000, 1)

    results["overall"] = "ok" if results.get("collection_exists") and results.get("search_works") else "degraded"
    return results


@router.get("/health-dashboard")
def full_health_dashboard():
    """Phase G: Full health dashboard with all subsystem checks."""
    from app.observability.health_dashboard import HealthDashboard
    dashboard = HealthDashboard()
    report = dashboard.get_full_health_report()
    return report.to_dict()
