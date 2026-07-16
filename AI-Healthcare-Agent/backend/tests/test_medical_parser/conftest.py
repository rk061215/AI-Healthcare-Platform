from typing import AsyncIterator, Optional

import pytest

from app.ai.base_provider import BaseProvider
from app.medical_parser.schemas import MedicalReportSchema


class MockProvider(BaseProvider):
    name = "mock"

    def __init__(self, return_value: Optional[dict] = None, fail_count: int = 0):
        super().__init__()
        self._return_value = return_value
        self._fail_count = fail_count
        self._call_count = 0

    def initialize(self) -> None:
        pass

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        return "mock response"

    def generate_structured_output(
        self, prompt: str, output_schema: dict, system_prompt: Optional[str] = None
    ) -> dict:
        self._call_count += 1
        if self._call_count <= self._fail_count:
            raise RuntimeError(f"Simulated failure #{self._call_count}")
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
                {
                    "name": "Lisinopril",
                    "dosage": "10mg",
                    "frequency": "once daily",
                    "duration": "30 days",
                    "route": "oral",
                    "instructions": "Take with food",
                }
            ],
            "lab_results": [
                {
                    "test_name": "Blood Pressure",
                    "value": "120/80",
                    "unit": "mmHg",
                    "reference_range": "",
                }
            ],
            "follow_up_date": "2026-02-15",
            "doctor_instructions": "Monitor blood pressure daily",
            "notes": "",
        }

    async def stream_response(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> AsyncIterator[str]:
        yield "mock"

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3]]

    def count_tokens(self, text: str) -> int:
        return len(text.split())

    def health_check(self) -> dict:
        return {"status": "healthy"}

    def close(self) -> None:
        pass


@pytest.fixture
def mock_provider():
    return MockProvider()


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
def multi_page_ocr_text() -> str:
    return """
Patient Name: Jane Smith
DOB: 1985-08-12
Date: 2026-03-01
Dr. Robert Brown
City Medical Center

Diagnosis: Asthma, Allergic Rhinitis

Medications:
Albuterol 90mcg 2 puffs as needed for wheezing
Fluticasone 250mcg once daily

--- Page 2 ---

Lab Results:
IgE 250 IU/mL
Eosinophil count 0.5 10^9/L

Follow-up: 2026-06-01
Notes: Avoid known triggers. Use peak flow meter daily.
"""


@pytest.fixture
def empty_ocr_text() -> str:
    return ""


@pytest.fixture
def low_quality_ocr_text() -> str:
    return "Pat1ent N@me: J0hn D0e\nD1agn0s1s: Hyp3rt3ns10n"
