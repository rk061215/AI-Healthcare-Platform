import pytest

from app.core.database_reset import DatabaseReset


def test_reset_schema_creates_tables(db_session):
    reset = DatabaseReset(db_session)
    result = reset.reset_schema()

    assert result["status"] == "success"
    assert result["tables_created"] >= 10
    assert "patients" in result["tables"]


def test_seed_data_creates_admin(db_session):
    reset = DatabaseReset(db_session)
    reset.reset_schema()

    from app.models.doctor import Doctor
    admin = db_session.query(Doctor).filter_by(email="admin@healthcare.com").first()
    assert admin is None

    reset.seed_data()

    admin = db_session.query(Doctor).filter_by(email="admin@healthcare.com").first()
    assert admin is not None
    assert admin.full_name == "System Admin"


def test_seed_data_idempotent(db_session):
    reset = DatabaseReset(db_session)
    reset.reset_schema()
    reset.seed_data()
    reset.seed_data()

    from app.models.doctor import Doctor
    admins = db_session.query(Doctor).filter_by(email="admin@healthcare.com").all()
    assert len(admins) == 1


def test_seed_creates_all_entities(db_session):
    from app.models.patient import Patient
    from app.models.doctor import Doctor
    from app.models.patient_doctor import PatientDoctor

    reset = DatabaseReset(db_session)
    reset.reset_schema()
    reset.seed_data()

    assert db_session.query(Patient).count() >= 3
    assert db_session.query(Doctor).count() >= 3
    assert db_session.query(PatientDoctor).count() >= 3


def test_verify_schema(db_session):
    reset = DatabaseReset(db_session)
    reset.reset_schema()

    result = reset.verify_schema()
    assert result["valid"] is True
    assert result["total_tables"] >= 10
    assert len(result["missing_tables"]) == 0
