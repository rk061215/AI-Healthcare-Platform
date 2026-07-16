"""Tests for Alembic migration."""
from pathlib import Path

import pytest


def test_migration_file_exists():
    """Initial migration file must exist."""
    versions_dir = Path(__file__).parents[3] / "backend" / "alembic" / "versions"
    migration_files = list(versions_dir.glob("*.py"))
    assert len(migration_files) > 0, "No migration files found in alembic/versions/"


def test_migration_has_upgrade():
    """Migration file must define upgrade() function."""
    versions_dir = Path(__file__).parents[3] / "backend" / "alembic" / "versions"
    migration_files = sorted(versions_dir.glob("*.py"))
    assert len(migration_files) > 0

    content = migration_files[0].read_text()
    assert "def upgrade()" in content, "Migration missing upgrade() function"


def test_migration_has_downgrade():
    """Migration file must define downgrade() function."""
    versions_dir = Path(__file__).parents[3] / "backend" / "alembic" / "versions"
    migration_files = sorted(versions_dir.glob("*.py"))
    assert len(migration_files) > 0

    content = migration_files[0].read_text()
    assert "def downgrade()" in content, "Migration missing downgrade() function"


def test_migration_creates_refresh_tokens():
    """Migration must create the refresh_tokens table."""
    versions_dir = Path(__file__).parents[3] / "backend" / "alembic" / "versions"
    migration_files = sorted(versions_dir.glob("*.py"))
    content = migration_files[0].read_text()
    assert "refresh_tokens" in content, "Migration missing refresh_tokens table"
    assert "jti" in content, "Migration missing jti column"


def test_migration_creates_all_tables():
    """Migration must create all required tables."""
    versions_dir = Path(__file__).parents[3] / "backend" / "alembic" / "versions"
    migration_files = sorted(versions_dir.glob("*.py"))
    content = migration_files[0].read_text()

    required_tables = [
        "patients",
        "doctors",
        "refresh_tokens",
        "patient_doctor",
        "reports",
        "medicines",
        "appointments",
        "chat_history",
        "adherence_logs",
        "emergency_alerts",
    ]
    for table in required_tables:
        assert f'"{table}"' in content or f"'{table}'" in content or f"_{table}" in content, (
            f"Migration missing table: {table}"
        )


def test_migration_has_terms_accepted():
    """Migration must include terms_accepted on patients."""
    versions_dir = Path(__file__).parents[3] / "backend" / "alembic" / "versions"
    migration_files = sorted(versions_dir.glob("*.py"))
    content = migration_files[0].read_text()
    assert "terms_accepted" in content, "Migration missing terms_accepted column"


def test_migration_has_hospital_name():
    """Migration must include hospital_name on doctors."""
    versions_dir = Path(__file__).parents[3] / "backend" / "alembic" / "versions"
    migration_files = sorted(versions_dir.glob("*.py"))
    content = migration_files[0].read_text()
    assert "hospital_name" in content, "Migration missing hospital_name column"


def test_migration_has_years_of_experience():
    """Migration must include years_of_experience on doctors."""
    versions_dir = Path(__file__).parents[3] / "backend" / "alembic" / "versions"
    migration_files = sorted(versions_dir.glob("*.py"))
    content = migration_files[0].read_text()
    assert "years_of_experience" in content, "Migration missing years_of_experience column"
