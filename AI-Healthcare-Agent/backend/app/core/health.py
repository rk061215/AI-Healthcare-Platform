"""Production database health check service.

Works with both PostgreSQL (production) and SQLite (testing).
"""

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.database.base import Base


@dataclass
class HealthResult:
    status: str = "healthy"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    services: dict = field(default_factory=dict)
    version: str = "0.8.0"


@dataclass
class DatabaseHealth:
    status: str = "up"
    latency_ms: float = 0.0
    pool_size: int = 0
    active_connections: int = 0
    table_count: int = 0
    index_count: int = 0
    error: str | None = None


class DatabaseHealthChecker:
    """Performs comprehensive health checks on the database."""

    def __init__(self, db: Session):
        self.db = db
        self.engine = db.get_bind()
        self._is_postgres = "postgresql" in str(self.engine.url)

    def check_all(self) -> DatabaseHealth:
        start = time.perf_counter()
        result = DatabaseHealth()
        try:
            self.db.execute(text("SELECT 1"))
            result.latency_ms = round((time.perf_counter() - start) * 1000, 2)
            result.table_count = self._get_table_count()
            if self._is_postgres:
                result.pool_size = self._get_pool_size()
                result.index_count = self._get_index_count()
        except Exception as e:
            result.status = "down"
            result.error = str(e)
        return result

    def _get_pool_size(self) -> int:
        try:
            result = self.db.execute(
                text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
            )
            return result.scalar() or 0
        except Exception:
            return 0

    def _get_table_count(self) -> int:
        inspector = inspect(self.engine)
        return len(inspector.get_table_names())

    def _get_index_count(self) -> int:
        try:
            result = self.db.execute(
                text("SELECT count(*) FROM pg_indexes WHERE schemaname = 'public'")
            )
            return result.scalar() or 0
        except Exception:
            return 0

    def get_table_details(self) -> list[dict]:
        inspector = inspect(self.engine)
        tables = inspector.get_table_names()
        details = []
        for table in tables:
            pk = inspector.get_pk_constraint(table)
            columns = len(inspector.get_columns(table))
            details.append({
                "name": table,
                "columns": columns,
                "primary_key": list(pk.get("constrained_columns", [])),
            })
        return details

    def verify_tables_exist(self) -> dict[str, bool]:
        expected = set(Base.metadata.tables.keys())
        inspector = inspect(self.engine)
        existing = set(inspector.get_table_names())
        return {t: t in existing for t in sorted(expected)}

    def run_migration_check(self) -> dict:
        try:
            result = self.db.execute(
                text("SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1")
            )
            row = result.fetchone()
            return {"current_revision": row[0] if row else None, "applied": row is not None}
        except Exception:
            return {"current_revision": None, "applied": False, "error": "alembic_version table not found"}
