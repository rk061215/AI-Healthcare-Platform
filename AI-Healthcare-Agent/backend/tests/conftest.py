import os
import uuid
from collections.abc import Generator

import pytest

os.environ.setdefault("OCR_USE_MOCK", "True")
os.environ.setdefault("OCR_ENABLED", "True")
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.database.session import get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


PATIENT_PASSWORD = "TestPass123!"
DOCTOR_PASSWORD = "DocPass456!"


@pytest.fixture
def patient_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/register/patient",
        json={
            "email": "test@patient.com",
            "password": PATIENT_PASSWORD,
            "confirm_password": PATIENT_PASSWORD,
            "full_name": "Test Patient",
            "terms_accepted": True,
        },
    )
    return response.json()["access_token"]


@pytest.fixture
def patient_refresh_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/register/patient",
        json={
            "email": "refresh@patient.com",
            "password": PATIENT_PASSWORD,
            "confirm_password": PATIENT_PASSWORD,
            "full_name": "Refresh Patient",
            "terms_accepted": True,
        },
    )
    return response.json()["refresh_token"]


@pytest.fixture
def doctor_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/register/doctor",
        json={
            "email": "test@doctor.com",
            "password": DOCTOR_PASSWORD,
            "confirm_password": DOCTOR_PASSWORD,
            "full_name": "Test Doctor",
            "specialization": "Cardiology",
            "license_number": "LIC-12345",
            "years_of_experience": 10,
        },
    )
    return response.json()["access_token"]
