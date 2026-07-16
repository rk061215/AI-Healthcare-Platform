from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.tools.exceptions import ToolValidationError
from app.tools.tool_context import ToolContext
from app.tools.tool_result import ToolResult
from app.tools.tools.appointment import AppointmentTool
from app.tools.tools.doctor import DoctorTool
from app.tools.tools.medication import MedicationTool
from app.tools.tools.patient import PatientTool
from app.tools.tools.report import ReportTool


class TestAppointmentTool:
    def setup_method(self):
        self.tool = AppointmentTool()

    def test_validate_valid_action(self):
        ctx = ToolContext(tool_name="appointment", action="book")
        self.tool.validate(ctx)

    def test_validate_invalid_action(self):
        ctx = ToolContext(tool_name="appointment", action="invalid")
        with pytest.raises(ToolValidationError, match="Invalid action"):
            self.tool.validate(ctx)

    def test_validate_missing_action(self):
        ctx = ToolContext(tool_name="appointment", action="")
        with pytest.raises(ToolValidationError, match="action is required"):
            self.tool.validate(ctx)

    def test_authorize_with_user(self):
        ctx = ToolContext(tool_name="appointment", action="book", user_id="u1", user_role="patient")
        assert self.tool.authorize(ctx) is True

    def test_authorize_no_user(self):
        ctx = ToolContext(tool_name="appointment", action="book")
        assert self.tool.authorize(ctx) is False

    def test_execute_no_db_session(self):
        ctx = ToolContext(tool_name="appointment", action="book", user_id="u1")
        result = self.tool.execute(ctx)
        assert result.success is False
        assert "db_session" in (result.error or "")

    def test_execute_book(self):
        mock_appointment = MagicMock()
        mock_appointment.id = "appt_1"
        mock_appointment.status.value = "scheduled"

        mock_service = MagicMock()
        mock_service.create_appointment.return_value = mock_appointment

        ctx = ToolContext(
            tool_name="appointment", action="book", user_id="u1", user_role="patient",
            parameters={
                "db_session": MagicMock(),
                "doctor_id": "doc_1",
                "scheduled_at": "2026-07-16T10:00:00Z",
            },
        )
        with patch("app.services.appointment_service.AppointmentService", return_value=mock_service):
            result = self.tool.execute(ctx)
        assert result.success is True

    def test_execute_cancel(self):
        mock_appointment = MagicMock()
        mock_appointment.id = "appt_1"
        mock_appointment.status.value = "cancelled"

        mock_service = MagicMock()
        mock_service.cancel_appointment.return_value = mock_appointment

        ctx = ToolContext(
            tool_name="appointment", action="cancel", user_id="u1", user_role="patient",
            parameters={"db_session": MagicMock(), "appointment_id": "appt_1"},
        )
        with patch("app.services.appointment_service.AppointmentService", return_value=mock_service):
            result = self.tool.execute(ctx)
        assert result.success is True

    def test_execute_list(self):
        mock_service = MagicMock()
        mock_service.list_appointments.return_value = MagicMock(items=[])

        ctx = ToolContext(
            tool_name="appointment", action="list", user_id="u1", user_role="patient",
            parameters={"db_session": MagicMock()},
        )
        with patch("app.services.appointment_service.AppointmentService", return_value=mock_service):
            result = self.tool.execute(ctx)
        assert result.success is True
        assert result.data["total"] == 0


class TestPatientTool:
    def setup_method(self):
        self.tool = PatientTool()

    def test_validate_valid_action(self):
        ctx = ToolContext(tool_name="patient", action="get_profile")
        self.tool.validate(ctx)

    def test_validate_invalid_action(self):
        ctx = ToolContext(tool_name="patient", action="invalid")
        with pytest.raises(ToolValidationError, match="Invalid action"):
            self.tool.validate(ctx)

    def test_authorize_no_user(self):
        ctx = ToolContext(tool_name="patient", action="get_profile")
        assert self.tool.authorize(ctx) is False

    def test_authorize_with_user(self):
        ctx = ToolContext(tool_name="patient", action="get_profile", user_id="u1")
        assert self.tool.authorize(ctx) is True

    def test_execute_no_db_session(self):
        ctx = ToolContext(tool_name="patient", action="get_profile", user_id="u1")
        result = self.tool.execute(ctx)
        assert result.success is False
        assert "db_session" in (result.error or "")

    def test_execute_get_profile(self):
        mock_patient = MagicMock()
        mock_patient.id = "pat_1"
        mock_patient.full_name = "John Doe"
        mock_patient.email = "john@test.com"
        mock_patient.phone = "1234567890"
        mock_patient.date_of_birth = None
        mock_patient.gender = None
        mock_patient.blood_group = None

        mock_service = MagicMock()
        mock_service.get_patient.return_value = mock_patient

        ctx = ToolContext(
            tool_name="patient", action="get_profile", user_id="u1",
            parameters={"db_session": MagicMock(), "patient_id": "pat_1"},
        )
        with patch("app.services.patient_service.PatientService", return_value=mock_service):
            result = self.tool.execute(ctx)
        assert result.success is True
        assert result.data["full_name"] == "John Doe"


class TestDoctorTool:
    def setup_method(self):
        self.tool = DoctorTool()

    def test_validate_valid_action(self):
        ctx = ToolContext(tool_name="doctor", action="assigned_doctor")
        self.tool.validate(ctx)

    def test_validate_invalid_action(self):
        ctx = ToolContext(tool_name="doctor", action="invalid")
        with pytest.raises(ToolValidationError, match="Invalid action"):
            self.tool.validate(ctx)

    def test_authorize_no_user(self):
        ctx = ToolContext(tool_name="doctor", action="assigned_doctor")
        assert self.tool.authorize(ctx) is False

    def test_execute_no_db_session(self):
        ctx = ToolContext(tool_name="doctor", action="assigned_doctor", user_id="u1")
        result = self.tool.execute(ctx)
        assert result.success is False

    def test_execute_specialization(self):
        mock_doctor = MagicMock()
        mock_doctor.id = "doc_1"
        mock_doctor.full_name = "Dr. Smith"
        mock_doctor.specialization = "Cardiology"
        mock_doctor.hospital_name = "City Hospital"
        mock_doctor.years_of_experience = 15

        mock_service = MagicMock()
        mock_service.get_doctor.return_value = mock_doctor

        ctx = ToolContext(
            tool_name="doctor", action="specialization", user_id="u1",
            parameters={"db_session": MagicMock(), "doctor_id": "doc_1"},
        )
        with patch("app.services.doctor_service.DoctorService", return_value=mock_service):
            result = self.tool.execute(ctx)
        assert result.success is True
        assert result.data["specialization"] == "Cardiology"


class TestReportTool:
    def setup_method(self):
        self.tool = ReportTool()

    def test_validate_valid_action(self):
        ctx = ToolContext(tool_name="report", action="list")
        self.tool.validate(ctx)

    def test_validate_invalid_action(self):
        ctx = ToolContext(tool_name="report", action="invalid")
        with pytest.raises(ToolValidationError, match="Invalid action"):
            self.tool.validate(ctx)

    def test_execute_no_db_session(self):
        ctx = ToolContext(tool_name="report", action="list", user_id="u1")
        result = self.tool.execute(ctx)
        assert result.success is False

    def test_execute_metadata(self):
        mock_report = MagicMock()
        mock_report.id = "rep_1"
        mock_report.title = "Blood Test"
        mock_report.file_type = "pdf"
        mock_report.file_size = 1024
        mock_report.status = "completed"
        mock_report.uploaded_at = "2026-07-01"
        mock_report.processed_at = "2026-07-01"
        mock_report.ocr_confidence = 0.95
        mock_report.ocr_provider = "tesseract"
        mock_report.patient_id = "pat_1"

        mock_service = MagicMock()
        mock_service.get_report.return_value = mock_report

        ctx = ToolContext(
            tool_name="report", action="metadata", user_id="u1",
            parameters={"db_session": MagicMock(), "report_id": "rep_1"},
        )
        with patch("app.services.report_service.ReportService", return_value=mock_service):
            result = self.tool.execute(ctx)
        assert result.success is True
        assert result.data["title"] == "Blood Test"


class TestMedicationTool:
    def setup_method(self):
        self.tool = MedicationTool()

    def test_validate_valid_action(self):
        ctx = ToolContext(tool_name="medication", action="schedule")
        self.tool.validate(ctx)

    def test_validate_invalid_action(self):
        ctx = ToolContext(tool_name="medication", action="invalid")
        with pytest.raises(ToolValidationError, match="Invalid action"):
            self.tool.validate(ctx)

    def test_execute_no_db_session(self):
        ctx = ToolContext(tool_name="medication", action="schedule", user_id="u1")
        result = self.tool.execute(ctx)
        assert result.success is False

    def test_execute_schedule(self):
        mock_medicine = MagicMock()
        mock_medicine.id = "med_1"
        mock_medicine.name = "Aspirin"
        mock_medicine.dosage = "100mg"
        mock_medicine.frequency = "once daily"
        mock_medicine.duration = "30 days"
        mock_medicine.route = None
        mock_medicine.instructions = "Take after food"
        mock_medicine.start_date = None
        mock_medicine.end_date = None

        mock_service = MagicMock()
        mock_service.get_active_medicines.return_value = [mock_medicine]

        ctx = ToolContext(
            tool_name="medication", action="schedule", user_id="u1",
            parameters={"db_session": MagicMock(), "patient_id": "pat_1"},
        )
        with patch("app.services.medicine_service.MedicineService", return_value=mock_service):
            result = self.tool.execute(ctx)
        assert result.success is True
        assert result.data["total"] == 1
        assert result.data["medications"][0]["name"] == "Aspirin"
