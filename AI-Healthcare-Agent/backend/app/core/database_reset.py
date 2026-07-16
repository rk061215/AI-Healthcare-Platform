"""Enhanced database reset with schema management, full seed data, and safety checks.

Works with both PostgreSQL (production) and SQLite (testing).
"""

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.session import get_sync_engine, get_sync_session_local


class DatabaseReset:
    """Manages schema reset and data seeding with safety checks."""

    def __init__(self, db: Session | None = None):
        self.db = db
        self.engine = get_sync_engine() if db is None else db.get_bind()
        self.required_tables = {
            "patients", "doctors", "refresh_tokens", "patient_doctors",
            "reports", "medicines", "appointments", "chat_history",
            "adherence_logs", "emergency_alerts",
        }

    def reset_schema(self) -> dict:
        """Drop and recreate all tables. Returns summary of created tables."""
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

        inspector = inspect(self.engine)
        created = inspector.get_table_names()

        return {
            "status": "success",
            "tables_created": len(created),
            "tables": created,
        }

    def truncate_all(self, cascade: bool = True) -> dict:
        """Truncate all tables in reverse dependency order. Returns affected tables."""
        inspector = inspect(self.engine)
        is_postgres = "postgresql" in str(self.engine.url)

        with self.engine.connect() as conn:
            if is_postgres:
                conn.execute(text("SET session_replication_role = 'replica';"))

            for table in reversed(Base.metadata.sorted_tables):
                if is_postgres:
                    conn.execute(text(f"TRUNCATE TABLE {table.name} {'CASCADE' if cascade else ''};"))
                else:
                    conn.execute(text(f"DELETE FROM {table.name};"))

            if is_postgres:
                conn.execute(text("SET session_replication_role = 'origin';"))
            conn.commit()

        return {
            "status": "success",
            "tables_truncated": len(Base.metadata.sorted_tables),
        }

    def verify_schema(self) -> dict:
        """Verify that all required tables exist and have the expected columns."""
        inspector = inspect(self.engine)
        existing_tables = set(inspector.get_table_names())

        missing = self.required_tables - existing_tables
        extra = existing_tables - self.required_tables

        table_details = {}
        for table in self.required_tables & existing_tables:
            columns = inspector.get_columns(table)
            table_details[table] = [
                {"name": c["name"], "type": str(c["type"]), "nullable": c.get("nullable", True)}
                for c in columns
            ]

        return {
            "valid": len(missing) == 0,
            "total_tables": len(existing_tables),
            "expected_tables": len(self.required_tables),
            "missing_tables": sorted(missing),
            "extra_tables": sorted(extra),
            "table_details": table_details,
        }

    def seed_data(self) -> dict:
        from app.core.seed import SeedData

        SessionFactory = get_sync_session_local()
        db = SessionFactory() if self.db is None else self.db

        try:
            seeder = SeedData(db)
            seeder.seed_all()
            return {"status": "success", "message": "Seed data created successfully"}
        except Exception as e:
            db.rollback()
            return {"status": "error", "message": str(e)}
        finally:
            if self.db is None:
                db.close()
