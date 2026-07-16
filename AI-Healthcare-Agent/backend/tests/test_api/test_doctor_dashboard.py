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


def _setup_test_data(db: Session, doctor_id: uuid.UUID):
    patient = Patient(
        id=uuid.uuid4(),
        email="testpatient@test.com",
        password_hash="hash",
        full_name="Test Patient",
        phone="+1-555-0100",
    )
    db.add(patient)
    db.flush()

    pd = PatientDoctor(patient_id=patient.id, doctor_id=doctor_id, is_active=True)
    db.add(pd)
    db.flush()

    now = datetime.now(timezone.utc)

    report = Report(
        id=uuid.uuid4(),
        patient_id=patient.id,
        title="Blood Report",
        file_path="/tmp/test.pdf",
        file_type="pdf",
        status=ReportStatus.COMPLETED,
        uploaded_at=now - timedelta(days=2),
        processed_at=now - timedelta(days=1),
    )
    db.add(report)
    db.flush()

    pending_report = Report(
        id=uuid.uuid4(),
        patient_id=patient.id,
        title="Pending X-Ray",
        file_path="/tmp/xray.pdf",
        file_type="pdf",
        status=ReportStatus.PENDING,
        uploaded_at=now - timedelta(hours=1),
    )
    db.add(pending_report)
    db.flush()

    med = Medicine(
        id=uuid.uuid4(),
        report_id=report.id,
        patient_id=patient.id,
        name="Amoxicillin",
        dosage="500mg",
        frequency="twice daily",
        is_active=True,
    )
    db.add(med)
    db.flush()

    appt = Appointment(
        id=uuid.uuid4(),
        patient_id=patient.id,
        doctor_id=doctor_id,
        title="Checkup",
        scheduled_at=now + timedelta(days=7),
        status=AppointmentStatus.SCHEDULED,
    )
    db.add(appt)
    db.flush()

    past_appt = Appointment(
        id=uuid.uuid4(),
        patient_id=patient.id,
        doctor_id=doctor_id,
        title="Past Visit",
        scheduled_at=now - timedelta(days=30),
        status=AppointmentStatus.COMPLETED,
    )
    db.add(past_appt)
    db.flush()

    log = AdherenceLog(
        id=uuid.uuid4(),
        medicine_id=med.id,
        patient_id=patient.id,
        scheduled_time=now,
        taken_at=now,
        status=AdherenceStatus.TAKEN,
    )
    db.add(log)
    db.flush()

    alert = EmergencyAlert(
        id=uuid.uuid4(),
        patient_id=patient.id,
        risk_level="high",
        symptoms="Severe chest pain",
        analysis="Possible cardiac event",
        is_acknowledged=False,
    )
    db.add(alert)
    db.flush()

    acknowledged_alert = EmergencyAlert(
        id=uuid.uuid4(),
        patient_id=patient.id,
        risk_level="low",
        symptoms="Mild headache",
        is_acknowledged=True,
        acknowledged_by=doctor_id,
    )
    db.add(acknowledged_alert)
    db.flush()

    chat = ChatHistory(
        id=uuid.uuid4(),
        patient_id=patient.id,
        role="user",
        message="Hello doctor",
    )
    db.add(chat)
    db.commit()

    return patient


class TestDoctorDashboard:
    def test_overview(self, client: TestClient, doctor_token: str):
        response = client.get(
            "/api/v1/doctor-dashboard/overview",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "doctor" in data
        assert "analytics" in data
        assert "recent_alerts" in data
        assert data["doctor"]["email"] is not None

    def test_overview_has_all_analytics_fields(self, client: TestClient, doctor_token: str):
        response = client.get(
            "/api/v1/doctor-dashboard/overview",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        data = response.json()
        analytics = data["analytics"]
        expected = [
            "total_patients", "active_patients", "total_appointments",
            "upcoming_appointments", "pending_reports", "unread_alerts",
            "pending_follow_ups",
        ]
        for field in expected:
            assert field in analytics, f"Missing analytics field: {field}"

    def test_overview_with_data(self, client: TestClient, doctor_token: str, db_session: Session):
        doctor_id = self._get_doctor_id(client, doctor_token)
        _setup_test_data(db_session, doctor_id)
        response = client.get(
            "/api/v1/doctor-dashboard/overview",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        data = response.json()
        assert data["analytics"]["total_patients"] >= 1
        assert data["analytics"]["total_appointments"] >= 2
        assert data["analytics"]["upcoming_appointments"] >= 1
        assert data["analytics"]["pending_reports"] >= 1
        assert data["analytics"]["unread_alerts"] >= 1
        assert len(data["recent_alerts"]) >= 1
        assert data["recent_alerts"][0]["risk_level"] == "high"

    def test_patients_empty(self, client: TestClient, doctor_token: str):
        response = client.get(
            "/api/v1/doctor-dashboard/patients",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 0

    def test_patients_with_data(self, client: TestClient, doctor_token: str, db_session: Session):
        doctor_id = self._get_doctor_id(client, doctor_token)
        _setup_test_data(db_session, doctor_id)
        response = client.get(
            "/api/v1/doctor-dashboard/patients",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        patient = data["items"][0]
        assert patient["full_name"] is not None
        assert patient["email"] is not None

    def test_patients_search(self, client: TestClient, doctor_token: str, db_session: Session):
        doctor_id = self._get_doctor_id(client, doctor_token)
        _setup_test_data(db_session, doctor_id)
        response = client.get(
            "/api/v1/doctor-dashboard/patients?search=Test",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        data = response.json()
        assert data["total"] >= 1

        response = client.get(
            "/api/v1/doctor-dashboard/patients?search=NonExistent",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        data = response.json()
        assert data["total"] == 0

    def test_patients_sorting(self, client: TestClient, doctor_token: str, db_session: Session):
        doctor_id = self._get_doctor_id(client, doctor_token)
        _setup_test_data(db_session, doctor_id)
        response = client.get(
            "/api/v1/doctor-dashboard/patients?sort_by=email&sort_order=desc",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert response.status_code == 200

    def test_patients_pagination(self, client: TestClient, doctor_token: str):
        response = client.get(
            "/api/v1/doctor-dashboard/patients?page=1&per_page=10",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 10

    def test_appointments_empty(self, client: TestClient, doctor_token: str):
        response = client.get(
            "/api/v1/doctor-dashboard/appointments",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert "items" in data

    def test_appointments_with_data(self, client: TestClient, doctor_token: str, db_session: Session):
        doctor_id = self._get_doctor_id(client, doctor_token)
        _setup_test_data(db_session, doctor_id)
        response = client.get(
            "/api/v1/doctor-dashboard/appointments",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        data = response.json()
        assert data["total"] >= 2

    def test_appointments_filter_by_status(self, client: TestClient, doctor_token: str, db_session: Session):
        doctor_id = self._get_doctor_id(client, doctor_token)
        _setup_test_data(db_session, doctor_id)
        response = client.get(
            "/api/v1/doctor-dashboard/appointments?status=scheduled",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        data = response.json()
        assert data["total"] >= 1

        response = client.get(
            "/api/v1/doctor-dashboard/appointments?status=completed",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        data = response.json()
        assert data["total"] >= 1

    def test_reports_empty(self, client: TestClient, doctor_token: str):
        response = client.get(
            "/api/v1/doctor-dashboard/reports",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_reports_with_data(self, client: TestClient, doctor_token: str, db_session: Session):
        doctor_id = self._get_doctor_id(client, doctor_token)
        _setup_test_data(db_session, doctor_id)
        response = client.get(
            "/api/v1/doctor-dashboard/reports",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        data = response.json()
        assert data["total"] >= 1

    def test_reports_filter_by_status(self, client: TestClient, doctor_token: str, db_session: Session):
        doctor_id = self._get_doctor_id(client, doctor_token)
        _setup_test_data(db_session, doctor_id)
        response = client.get(
            "/api/v1/doctor-dashboard/reports?status=completed",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        data = response.json()
        assert data["total"] >= 1

    def test_summaries_empty(self, client: TestClient, doctor_token: str):
        response = client.get(
            "/api/v1/doctor-dashboard/summaries",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_summaries_with_data(self, client: TestClient, doctor_token: str, db_session: Session):
        doctor_id = self._get_doctor_id(client, doctor_token)
        _setup_test_data(db_session, doctor_id)
        response = client.get(
            "/api/v1/doctor-dashboard/summaries",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        data = response.json()
        assert data["total"] >= 1
        summary = data["items"][0]
        assert "patient_name" in summary
        assert "overall_adherence_rate" in summary
        assert "medicines_count" in summary

    def test_alerts_empty(self, client: TestClient, doctor_token: str):
        response = client.get(
            "/api/v1/doctor-dashboard/alerts",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] == 0

    def test_alerts_with_data(self, client: TestClient, doctor_token: str, db_session: Session):
        doctor_id = self._get_doctor_id(client, doctor_token)
        _setup_test_data(db_session, doctor_id)
        response = client.get(
            "/api/v1/doctor-dashboard/alerts",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        data = response.json()
        assert data["total"] >= 2

    def test_alerts_filter_by_risk(self, client: TestClient, doctor_token: str, db_session: Session):
        doctor_id = self._get_doctor_id(client, doctor_token)
        _setup_test_data(db_session, doctor_id)
        response = client.get(
            "/api/v1/doctor-dashboard/alerts?risk_level=high",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        data = response.json()
        assert data["total"] >= 1

    def test_alerts_filter_by_acknowledged(self, client: TestClient, doctor_token: str, db_session: Session):
        doctor_id = self._get_doctor_id(client, doctor_token)
        _setup_test_data(db_session, doctor_id)
        response = client.get(
            "/api/v1/doctor-dashboard/alerts?is_acknowledged=false",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["is_acknowledged"] is False

    def test_unauthorized_access(self, client: TestClient):
        response = client.get("/api/v1/doctor-dashboard/overview")
        assert response.status_code == 401

    def test_patient_token_rejected(self, client: TestClient, patient_token: str):
        response = client.get(
            "/api/v1/doctor-dashboard/overview",
            headers={"Authorization": f"Bearer {patient_token}"},
        )
        assert response.status_code == 403

    def test_invalid_pagination(self, client: TestClient, doctor_token: str):
        response = client.get(
            "/api/v1/doctor-dashboard/patients?page=0",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert response.status_code == 422

    def test_per_page_max_limit(self, client: TestClient, doctor_token: str):
        response = client.get(
            "/api/v1/doctor-dashboard/patients?per_page=200",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert response.status_code == 422

    def test_alerts_high_first(self, client: TestClient, doctor_token: str, db_session: Session):
        doctor_id = self._get_doctor_id(client, doctor_token)
        _setup_test_data(db_session, doctor_id)
        response = client.get(
            "/api/v1/doctor-dashboard/alerts",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        data = response.json()
        if data["total"] >= 2:
            risk_levels = [item["risk_level"] for item in data["items"]]
            high_idx = risk_levels.index("high") if "high" in risk_levels else len(risk_levels)
            low_idx = risk_levels.index("low") if "low" in risk_levels else len(risk_levels)
            assert high_idx < low_idx, "High risk alerts should appear before low risk"

    def test_appointments_has_patient_info(self, client: TestClient, doctor_token: str, db_session: Session):
        doctor_id = self._get_doctor_id(client, doctor_token)
        _setup_test_data(db_session, doctor_id)
        response = client.get(
            "/api/v1/doctor-dashboard/appointments",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        data = response.json()
        if data["total"] > 0:
            appt = data["items"][0]
            assert "patient_name" in appt
            assert "patient_id" in appt
            assert "scheduled_at" in appt
            assert "status" in appt

    def _get_doctor_id(self, client: TestClient, token: str) -> uuid.UUID:
        response = client.get(
            "/api/v1/doctors/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        return uuid.UUID(response.json()["id"])
