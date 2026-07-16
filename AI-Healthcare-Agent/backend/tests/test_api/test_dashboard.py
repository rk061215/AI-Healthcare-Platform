import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.enums import AdherenceStatus, AppointmentStatus, ReportStatus
from app.models.adherence_log import AdherenceLog
from app.models.appointment import Appointment
from app.models.chat_history import ChatHistory
from app.models.doctor import Doctor
from app.models.emergency_alert import EmergencyAlert
from app.models.medicine import Medicine
from app.models.patient import Patient
from app.models.patient_doctor import PatientDoctor
from app.models.report import Report


def _setup_test_data(db: Session, patient_id: uuid.UUID):
    doctor = Doctor(
        id=uuid.uuid4(),
        email="dr@test.com",
        password_hash="hash",
        full_name="Dr. Smith",
        specialization="Cardiology",
        license_number="LIC-001",
    )
    db.add(doctor)
    db.flush()

    pd = PatientDoctor(patient_id=patient_id, doctor_id=doctor.id, is_active=True)
    db.add(pd)

    now = datetime.now(timezone.utc)

    report = Report(
        id=uuid.uuid4(),
        patient_id=patient_id,
        title="Blood Report",
        file_path="/tmp/test.pdf",
        file_type="pdf",
        status=ReportStatus.COMPLETED,
        uploaded_at=now - timedelta(days=2),
        processed_at=now - timedelta(days=1),
    )
    db.add(report)
    db.flush()

    med = Medicine(
        id=uuid.uuid4(),
        report_id=report.id,
        patient_id=patient_id,
        name="Amoxicillin",
        dosage="500mg",
        frequency="twice daily",
        is_active=True,
    )
    db.add(med)
    db.flush()

    appt = Appointment(
        id=uuid.uuid4(),
        patient_id=patient_id,
        doctor_id=doctor.id,
        title="Checkup",
        scheduled_at=now + timedelta(days=7),
        status=AppointmentStatus.SCHEDULED,
    )
    db.add(appt)

    log = AdherenceLog(
        id=uuid.uuid4(),
        medicine_id=med.id,
        patient_id=patient_id,
        scheduled_time=now,
        taken_at=now,
        status=AdherenceStatus.TAKEN,
    )
    db.add(log)

    alert = EmergencyAlert(
        id=uuid.uuid4(),
        patient_id=patient_id,
        risk_level="low",
        symptoms="Mild headache",
        is_acknowledged=False,
    )
    db.add(alert)

    chat = ChatHistory(
        id=uuid.uuid4(),
        patient_id=patient_id,
        role="user",
        message="Hello",
    )
    db.add(chat)
    db.commit()


class TestDashboard:
    def test_overview(self, client: TestClient, patient_token: str):
        response = client.get(
            "/api/v1/dashboard/overview",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "patient_name" in data
        assert "active_medicines_count" in data
        assert "adherence_rate" in data

    def test_medicines_empty(self, client: TestClient, patient_token: str):
        response = client.get(
            "/api/v1/dashboard/medicines",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "total_pages" in data

    def test_medicines_pagination(self, client: TestClient, patient_token: str):
        response = client.get(
            "/api/v1/dashboard/medicines?page=1&per_page=10",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 10

    def test_appointments_empty(self, client: TestClient, patient_token: str):
        response = client.get(
            "/api/v1/dashboard/appointments",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_appointments_filter_by_status(self, client: TestClient, patient_token: str):
        response = client.get(
            "/api/v1/dashboard/appointments?status=scheduled",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert response.status_code == 200

    def test_reports_empty(self, client: TestClient, patient_token: str):
        response = client.get(
            "/api/v1/dashboard/reports",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_reports_filter_by_status(self, client: TestClient, patient_token: str):
        response = client.get(
            "/api/v1/dashboard/reports?status=completed",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert response.status_code == 200

    def test_schedule(self, client: TestClient, patient_token: str):
        response = client.get(
            "/api/v1/dashboard/schedule",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_timeline(self, client: TestClient, patient_token: str):
        response = client.get(
            "/api/v1/dashboard/timeline?days=30",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_timeline_invalid_days(self, client: TestClient, patient_token: str):
        response = client.get(
            "/api/v1/dashboard/timeline?days=0",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert response.status_code == 422

    def test_reminders(self, client: TestClient, patient_token: str):
        response = client.get(
            "/api/v1/dashboard/reminders",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_ai_status(self, client: TestClient, patient_token: str):
        response = client.get(
            "/api/v1/dashboard/ai-status",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "message" in data

    def test_unauthorized_access(self, client: TestClient):
        response = client.get("/api/v1/dashboard/overview")
        assert response.status_code == 401

    def test_invalid_pagination(self, client: TestClient, patient_token: str):
        response = client.get(
            "/api/v1/dashboard/medicines?page=0",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert response.status_code == 422

    def test_per_page_max_limit(self, client: TestClient, patient_token: str):
        response = client.get(
            "/api/v1/dashboard/reports?per_page=200",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert response.status_code == 422

    def test_overview_has_all_fields(self, client: TestClient, patient_token: str):
        response = client.get(
            "/api/v1/dashboard/overview",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        data = response.json()
        expected_fields = [
            "patient_name", "patient_email", "active_medicines_count",
            "total_reports_count", "upcoming_appointments_count",
            "adherence_rate", "total_doses", "taken_doses", "missed_doses",
            "pending_alerts_count", "assigned_doctors",
            "emergency_contact", "emergency_phone",
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

    def test_medicine_with_data(self, client: TestClient, patient_token: str, db_session: Session):
        patient_id = self._get_patient_id(client, patient_token)
        _setup_test_data(db_session, patient_id)
        response = client.get(
            "/api/v1/dashboard/overview",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        data = response.json()
        assert data["active_medicines_count"] >= 1
        assert data["total_reports_count"] >= 1
        assert data["upcoming_appointments_count"] >= 1
        assert data["assigned_doctors"] != []

    def test_schedule_with_data(self, client: TestClient, patient_token: str, db_session: Session):
        patient_id = self._get_patient_id(client, patient_token)
        _setup_test_data(db_session, patient_id)
        response = client.get(
            "/api/v1/dashboard/schedule",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        data = response.json()
        assert len(data) >= 1
        assert "medicine_name" in data[0]
        assert "scheduled_time" in data[0]
        assert "status" in data[0]

    def test_timeline_with_data(self, client: TestClient, patient_token: str, db_session: Session):
        patient_id = self._get_patient_id(client, patient_token)
        _setup_test_data(db_session, patient_id)
        response = client.get(
            "/api/v1/dashboard/timeline",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        data = response.json()
        assert len(data) >= 1
        assert "event_type" in data[0]
        assert "title" in data[0]
        assert "timestamp" in data[0]

    def test_ai_status_with_chats(self, client: TestClient, patient_token: str, db_session: Session):
        patient_id = self._get_patient_id(client, patient_token)
        _setup_test_data(db_session, patient_id)
        response = client.get(
            "/api/v1/dashboard/ai-status",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        data = response.json()
        assert data["total_chats"] >= 1
        assert data["last_interaction"] is not None

    def _get_patient_id(self, client: TestClient, token: str) -> uuid.UUID:
        response = client.get(
            "/api/v1/patients/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        return uuid.UUID(response.json()["id"])
