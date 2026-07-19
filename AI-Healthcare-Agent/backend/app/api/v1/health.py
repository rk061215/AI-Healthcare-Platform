"""Enhanced health check endpoint with comprehensive database diagnostics."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.health import DatabaseHealthChecker, HealthResult
from app.database.session import get_db

router = APIRouter()


@router.get("")
def health_check(db: Session = Depends(get_db)):
    checker = DatabaseHealthChecker(db)
    db_health = checker.check_all()
    tables = checker.verify_tables_exist()
    migration = checker.run_migration_check()

    overall = "healthy"
    if db_health.status == "down":
        overall = "degraded"

    return HealthResult(
        status=overall,
        services={
            "database": {
                "status": db_health.status,
                "latency_ms": db_health.latency_ms,
                "pool_size": db_health.pool_size,
                "table_count": db_health.table_count,
                "index_count": db_health.index_count,
                "tables": tables,
                "migration": migration,
                "error": db_health.error,
            }
        },
    }


@router.get("/details")
def health_details(db: Session = Depends(get_db)):
    checker = DatabaseHealthChecker(db)
    db_health = checker.check_all()
    tables = checker.get_table_details()
    migration = checker.run_migration_check()

    return {
        "status": db_health.status,
        "latency_ms": db_health.latency_ms,
        "migration": migration,
        "tables": tables,
        "pg_version": _get_pg_version(db),
    }


def _get_pg_version(db: Session) -> str | None:
    try:
        result = db.execute(
            "SELECT version()"
        )
        return result.scalar()
    except Exception:
        return None
