from __future__ import annotations

import os
import time
import uuid
from collections.abc import AsyncIterator, Generator
from typing import Any, Optional

import pytest

os.environ["OCR_USE_MOCK"] = "True"
os.environ["OCR_ENABLED"] = "True"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["GEMINI_API_KEY"] = "fake-key-for-integration-tests"

import app.ai.providers.gemini_provider  # noqa: F401 - registers GeminiProvider
import app.embeddings.providers.gemini_embedding  # noqa: F401 - registers GeminiEmbedding
import app.ocr.engines.tesseract_ocr  # noqa: F401 - registers TesseractEngine
import app.tools  # noqa: F401 - registers all tools into global registry
import app.agents  # noqa: F401 - registers all agents

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.ai.base_provider import BaseProvider
from app.database.base import Base
from app.database.session import get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///./test_integration.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class MockAIProvider(BaseProvider):
    name = "mock_integration"

    def __init__(self, return_value: Optional[dict] = None):
        super().__init__()
        self._return_value = return_value
        self._call_count = 0

    def initialize(self) -> None:
        pass

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        return "This is a mock response. Based on the medical context, Paracetamol 500mg is prescribed for fever management. Always consult your doctor."

    def generate_structured_output(
        self, prompt: str, output_schema: dict, system_prompt: Optional[str] = None
    ) -> dict:
        self._call_count += 1
        if self._return_value is not None:
            return self._return_value
        return {
            "document_type": "PRESCRIPTION",
            "patient_name": "John Doe",
            "date_of_birth": "1990-05-20",
            "document_date": "2026-01-15",
            "doctor_name": "Dr. Smith",
            "hospital_name": "General Hospital",
            "diagnosis": "Hypertension",
            "medications": [
                {"name": "Lisinopril", "dosage": "10mg", "frequency": "once daily", "duration": "30 days", "route": "oral", "instructions": "Take with food"},
            ],
            "lab_results": [{"test_name": "Blood Pressure", "value": "120/80", "unit": "mmHg", "reference_range": ""}],
            "follow_up_date": "2026-02-15",
            "doctor_instructions": "Monitor blood pressure daily",
            "notes": "",
        }

    async def stream_response(self, prompt: str, system_prompt: Optional[str] = None) -> AsyncIterator[str]:
        yield "mock"

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 128 for _ in texts]

    def count_tokens(self, text: str) -> int:
        return len(text.split())

    def health_check(self) -> dict:
        return {"status": "healthy"}

    def close(self) -> None:
        pass


class MockEmbeddingService:
    def __init__(self, dimension: int = 128):
        self._dimension = dimension

    def embed(self, text: str) -> tuple[list[float], Any]:
        class MockMeta:
            embedding_version = "1.0"
            model = "mock"
            tokens_used = len(text.split())
        return [0.1] * self._dimension, MockMeta()

    def embed_query(self, text: str) -> tuple[list[float], Any]:
        return self.embed(text)

    def embed_batch(self, texts: list[str]) -> tuple[list[list[float]], list[Any]]:
        vectors = []
        metas = []
        for t in texts:
            v, m = self.embed(t)
            vectors.append(v)
            metas.append(m)
        return vectors, metas

    def health_check(self) -> dict:
        return {"status": "healthy", "dimension": self._dimension}


class MockVectorStore:
    def __init__(self):
        self._documents: dict[str, dict] = {}
        self._initialized = False

    def initialize(self) -> None:
        self._initialized = True

    def add_documents(self, documents: list[Any]) -> list[str]:
        ids = []
        for doc in documents:
            doc_id = doc.id if hasattr(doc, "id") else str(uuid.uuid4())
            self._documents[doc_id] = {"doc": doc, "text": doc.text if hasattr(doc, "text") else ""}
            ids.append(doc_id)
        return ids

    def similarity_search(self, query_vector: list[float], k: int = 10, filter: Optional[dict] = None) -> list[Any]:
        class MockSearchResult:
            def __init__(self, id, text, score=0.85):
                self.id = id
                self.text = text
                self.score = score
                self.metadata = {"patient_id": "test-patient", "section": "medication"}
        results = []
        for doc_id, doc_data in list(self._documents.items())[:k]:
            results.append(MockSearchResult(doc_id, doc_data["text"]))
        return results

    def metadata_search(self, filter: Optional[dict] = None, k: int = 50) -> list[Any]:
        return self.similarity_search([0.1] * 128, k=k, filter=filter)

    def delete_documents(self, ids: list[str]) -> None:
        for did in ids:
            self._documents.pop(did, None)

    def list_collections(self) -> list[Any]:
        return []

    def health_check(self) -> dict:
        return {"status": "healthy", "document_count": len(self._documents)}

    def close(self) -> None:
        pass


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=engine)
    session: Session = TestingSessionLocal()
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


@pytest.fixture
def patient_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/register/patient",
        json={
            "email": f"int-patient-{uuid.uuid4().hex[:8]}@test.com",
            "password": "TestPass123!",
            "confirm_password": "TestPass123!",
            "full_name": "Integration Patient",
            "terms_accepted": True,
        },
    )
    assert response.status_code in (200, 201), f"Patient registration failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture
def doctor_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/register/doctor",
        json={
            "email": f"int-doctor-{uuid.uuid4().hex[:8]}@test.com",
            "password": "DocPass456!",
            "confirm_password": "DocPass456!",
            "full_name": "Integration Doctor",
            "specialization": "Cardiology",
            "license_number": "LIC-INT-12345",
            "years_of_experience": 10,
        },
    )
    assert response.status_code in (200, 201), f"Doctor registration failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture
def mock_ai_provider() -> MockAIProvider:
    return MockAIProvider()


@pytest.fixture
def mock_embedding_service() -> MockEmbeddingService:
    return MockEmbeddingService()


@pytest.fixture
def mock_vector_store() -> MockVectorStore:
    return MockVectorStore()


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    return b"%PDF-1.4 fake PDF content for integration testing"


@pytest.fixture
def sample_image_bytes() -> bytes:
    return b"\x89PNG\r\n\x1a\nfake PNG content for integration testing"


class PerfTimer:
    def __init__(self):
        self._marks: dict[str, float] = {}
        self._order: list[str] = []

    def mark(self, name: str) -> None:
        self._marks[name] = time.perf_counter()
        self._order.append(name)

    def elapsed(self, from_name: str, to_name: str) -> float:
        return (self._marks[to_name] - self._marks[from_name]) * 1000

    def report_line(self, label: str, ms: float) -> str:
        return f"  {label}: {ms:.1f}ms"


@pytest.fixture
def perf_timer() -> PerfTimer:
    return PerfTimer()



@pytest.fixture
def sample_ocr_text() -> str:
    return """
Patient Name: John Doe
DOB: 1990-05-20
Date: 2026-01-15
Dr. Sarah Smith
General Hospital
Diagnosis: Type 2 Diabetes Mellitus

Medications:
Metformin 500mg twice daily with meals
Lisinopril 10mg once daily

Lab Results:
Blood Glucose 126 mg/dL
HbA1c 7.2 %

Follow-up: 2026-04-15
Notes: Monitor blood sugar levels
"""


@pytest.fixture
def patient_auth_headers(patient_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {patient_token}"}


@pytest.fixture
def doctor_auth_headers(doctor_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {doctor_token}"}
