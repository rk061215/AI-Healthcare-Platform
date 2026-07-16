"""Comprehensive seed data for development and testing."""

from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database.enums import (
    AdherenceStatus,
    AppointmentStatus,
    ChatRole,
    MedicineRoute,
    ReportStatus,
    RiskLevel,
)


class SeedData:
    """Seeds the database with realistic test data across all 10 tables."""

    PATIENTS = [
        {
            "email": "alice@example.com",
            "password_hash": hash_password("TestPass123!"),
            "full_name": "Alice Johnson",
            "phone": "+12025551234",
            "date_of_birth": date(1985, 6, 15),
            "gender": "female",
            "blood_group": "O+",
            "address": "123 Main St, Springfield, IL 62701",
            "emergency_contact": "Bob Johnson",
            "emergency_phone": "+12025555678",
            "terms_accepted": True,
            "terms_accepted_at": datetime.now(timezone.utc),
            "is_active": True,
        },
        {
            "email": "bob@example.com",
            "password_hash": hash_password("TestPass123!"),
            "full_name": "Bob Smith",
            "phone": "+14155551234",
            "date_of_birth": date(1978, 11, 2),
            "gender": "male",
            "blood_group": "A+",
            "address": "456 Oak Ave, Portland, OR 97201",
            "emergency_contact": "Carol Smith",
            "emergency_phone": "+14155555678",
            "terms_accepted": True,
            "terms_accepted_at": datetime.now(timezone.utc),
            "is_active": True,
        },
        {
            "email": "carol@example.com",
            "password_hash": hash_password("TestPass123!"),
            "full_name": "Carol Williams",
            "phone": "+13105551234",
            "date_of_birth": date(1992, 3, 28),
            "gender": "female",
            "blood_group": "B-",
            "address": "789 Pine Rd, Denver, CO 80201",
            "emergency_contact": "David Williams",
            "emergency_phone": "+13105555678",
            "terms_accepted": True,
            "terms_accepted_at": datetime.now(timezone.utc),
            "is_active": True,
        },
    ]

    DOCTORS = [
        {
            "email": "admin@healthcare.com",
            "password_hash": hash_password("Admin123!"),
            "full_name": "System Admin",
            "specialization": "Administration",
            "license_number": "ADMIN-001",
            "is_active": True,
        },
        {
            "email": "drsarah@example.com",
            "password_hash": hash_password("DocPass456!"),
            "full_name": "Dr. Sarah Chen",
            "specialization": "Cardiology",
            "license_number": "MED-12345-CA",
            "phone": "+12125551234",
            "hospital_name": "City General Hospital",
            "years_of_experience": 15,
            "is_active": True,
        },
        {
            "email": "drmike@example.com",
            "password_hash": hash_password("DocPass456!"),
            "full_name": "Dr. Mike Patel",
            "specialization": "Internal Medicine",
            "license_number": "MED-67890-NY",
            "phone": "+19175551234",
            "hospital_name": "University Medical Center",
            "years_of_experience": 8,
            "is_active": True,
        },
    ]

    REPORTS = [
        {
            "title": "Annual Physical Blood Work",
            "file_path": "/uploads/reports/blood_work_alice_2026.pdf",
            "file_type": "application/pdf",
            "file_size": 245760,
            "original_filename": "blood_work_2026.pdf",
            "ocr_text": "Patient: Alice Johnson\nDate: 2026-01-15\nHemoglobin: 14.2 g/dL\nWBC: 6.5 K/uL\nPlatelets: 250 K/uL\nGlucose: 95 mg/dL\nCholesterol: 180 mg/dL\nHDL: 55 mg/dL\nLDL: 110 mg/dL",
            "status": ReportStatus.COMPLETED,
            "uploaded_at": datetime(2026, 1, 15, 10, 30, tzinfo=timezone.utc),
            "processed_at": datetime(2026, 1, 15, 10, 32, tzinfo=timezone.utc),
        },
        {
            "title": "Chest X-Ray Report",
            "file_path": "/uploads/reports/chest_xray_bob_2026.pdf",
            "file_type": "application/pdf",
            "file_size": 512000,
            "original_filename": "chest_xray_2026.pdf",
            "ocr_text": "Patient: Bob Smith\nDate: 2026-02-20\nProcedure: Chest X-Ray, 2 Views\nFindings: Clear lung fields. No consolidation, effusion, or pneumothorax. Cardiac silhouette within normal limits.",
            "status": ReportStatus.COMPLETED,
            "uploaded_at": datetime(2026, 2, 20, 14, 0, tzinfo=timezone.utc),
            "processed_at": datetime(2026, 2, 20, 14, 5, tzinfo=timezone.utc),
        },
        {
            "title": "Lipid Panel Results",
            "file_path": "/uploads/reports/lipid_panel_carol_2026.pdf",
            "file_type": "application/pdf",
            "file_size": 102400,
            "original_filename": "lipid_panel_2026.pdf",
            "ocr_text": "Patient: Carol Williams\nDate: 2026-03-10\nTotal Cholesterol: 240 mg/dL (High)\nLDL: 160 mg/dL (High)\nHDL: 45 mg/dL\nTriglycerides: 175 mg/dL (High)",
            "status": ReportStatus.COMPLETED,
            "uploaded_at": datetime(2026, 3, 10, 9, 15, tzinfo=timezone.utc),
            "processed_at": datetime(2026, 3, 10, 9, 17, tzinfo=timezone.utc),
        },
    ]

    MEDICINES = [
        {"name": "Lisinopril", "dosage": "10 mg", "frequency": "Once daily", "duration": "90 days", "route": MedicineRoute.ORAL, "instructions": "Take in the morning with food", "start_date": date(2026, 1, 20), "end_date": date(2026, 4, 20), "is_active": True},
        {"name": "Atorvastatin", "dosage": "20 mg", "frequency": "Once daily at bedtime", "duration": "90 days", "route": MedicineRoute.ORAL, "instructions": "Take at bedtime", "start_date": date(2026, 1, 20), "end_date": date(2026, 4, 20), "is_active": True},
        {"name": "Metformin", "dosage": "500 mg", "frequency": "Twice daily with meals", "duration": "180 days", "route": MedicineRoute.ORAL, "instructions": "Take with breakfast and dinner", "start_date": date(2026, 2, 1), "end_date": date(2026, 7, 31), "is_active": True},
    ]

    APPOINTMENTS = [
        {"title": "Cardiology Follow-up", "description": "Review blood work and adjust medications", "status": AppointmentStatus.COMPLETED, "scheduled_at": datetime(2026, 1, 22, 10, 0, tzinfo=timezone.utc)},
        {"title": "Medication Review", "description": "Discuss new cholesterol medications", "status": AppointmentStatus.CONFIRMED, "scheduled_at": datetime(2026, 7, 20, 14, 30, tzinfo=timezone.utc)},
        {"title": "Annual Physical", "description": "Comprehensive annual checkup", "status": AppointmentStatus.SCHEDULED, "scheduled_at": datetime(2026, 8, 15, 9, 0, tzinfo=timezone.utc)},
        {"title": "Follow-up on Chest X-Ray", "description": "Review X-Ray results and next steps", "status": AppointmentStatus.COMPLETED, "scheduled_at": datetime(2026, 2, 25, 11, 0, tzinfo=timezone.utc)},
        {"title": "Lipid Panel Consultation", "description": "Discuss high cholesterol results and treatment plan", "status": AppointmentStatus.SCHEDULED, "scheduled_at": datetime(2026, 7, 25, 15, 0, tzinfo=timezone.utc)},
    ]

    CHAT_MESSAGES = [
        {"role": ChatRole.USER, "message": "Good morning! I took my Lisinopril today but I feel a bit dizzy."},
        {"role": ChatRole.ASSISTANT, "message": "I'm sorry to hear you're feeling dizzy. Dizziness can sometimes occur with Lisinopril, especially when starting. Please make sure you're drinking enough water and avoid sudden position changes. If the dizziness persists or becomes severe, please contact your doctor."},
        {"role": ChatRole.USER, "message": "When should I take my Atorvastatin? I forgot the instructions."},
        {"role": ChatRole.ASSISTANT, "message": "You should take Atorvastatin at bedtime, as cholesterol production is highest during the night. Taking it at the same time each day will help you remember."},
        {"role": ChatRole.USER, "message": "My blood pressure was 135/85 this morning. Is that OK?"},
        {"role": ChatRole.ASSISTANT, "message": "A reading of 135/85 is slightly elevated but generally acceptable while on treatment. The goal is usually below 130/80. Continue monitoring and stay consistent with your medication. We'll review the trends at your next appointment."},
    ]

    ADHERENCE_LOGS = [
        {"scheduled_time": datetime(2026, 7, 14, 8, 0, tzinfo=timezone.utc), "taken_at": datetime(2026, 7, 14, 8, 15, tzinfo=timezone.utc), "status": AdherenceStatus.TAKEN},
        {"scheduled_time": datetime(2026, 7, 14, 21, 0, tzinfo=timezone.utc), "taken_at": datetime(2026, 7, 14, 21, 10, tzinfo=timezone.utc), "status": AdherenceStatus.TAKEN},
        {"scheduled_time": datetime(2026, 7, 13, 8, 0, tzinfo=timezone.utc), "taken_at": datetime(2026, 7, 13, 8, 5, tzinfo=timezone.utc), "status": AdherenceStatus.TAKEN},
        {"scheduled_time": datetime(2026, 7, 13, 21, 0, tzinfo=timezone.utc), "taken_at": None, "status": AdherenceStatus.MISSED, "notes": "Forgot to take before bed"},
        {"scheduled_time": datetime(2026, 7, 12, 8, 0, tzinfo=timezone.utc), "taken_at": datetime(2026, 7, 12, 8, 30, tzinfo=timezone.utc), "status": AdherenceStatus.TAKEN},
    ]

    EMERGENCY_ALERTS = [
        {"symptoms": "Chest pain and shortness of breath for 30 minutes", "risk_level": RiskLevel.HIGH, "analysis": "Symptoms suggest possible cardiac event. Immediate attention recommended.", "is_acknowledged": False},
        {"symptoms": "Mild headache after taking medication", "risk_level": RiskLevel.LOW, "analysis": "Likely medication side effect. Monitor and report if persists.", "is_acknowledged": True, "resolved_at": None},
    ]

    def __init__(self, db: Session):
        self.db = db
        self.patients: dict[str, UUID] = {}
        self.doctors: dict[str, UUID] = {}
        self.reports: dict[str, UUID] = {}
        self.medicines: dict[str, UUID] = {}

    def seed_all(self) -> None:
        self._seed_patients()
        self._seed_doctors()
        self._seed_assignments()
        self._seed_reports()
        self._seed_medicines()
        self._seed_appointments()
        self._seed_chat()
        self._seed_adherence()
        self._seed_emergency_alerts()
        self.db.commit()

    def _get_or_create(self, model, lookup: dict, defaults: dict):
        instance = self.db.query(model).filter_by(**lookup).first()
        if instance:
            return instance
        instance = model(**defaults)
        self.db.add(instance)
        self.db.flush()
        return instance

    def _seed_patients(self) -> None:
        from app.models.patient import Patient
        for p in self.PATIENTS:
            patient = self._get_or_create(Patient, {"email": p["email"]}, p)
            self.patients[p["email"]] = patient.id

    def _seed_doctors(self) -> None:
        from app.models.doctor import Doctor
        for d in self.DOCTORS:
            doctor = self._get_or_create(Doctor, {"email": d["email"]}, d)
            self.doctors[d["email"]] = doctor.id

    def _seed_assignments(self) -> None:
        from app.models.patient_doctor import PatientDoctor
        assignments = [
            ("alice@example.com", "drsarah@example.com"),
            ("bob@example.com", "drsarah@example.com"),
            ("carol@example.com", "drmike@example.com"),
        ]
        for patient_email, doctor_email in assignments:
            self._get_or_create(
                PatientDoctor,
                {
                    "patient_id": self.patients[patient_email],
                    "doctor_id": self.doctors[doctor_email],
                },
                {
                    "patient_id": self.patients[patient_email],
                    "doctor_id": self.doctors[doctor_email],
                    "is_active": True,
                },
            )

    def _seed_reports(self) -> None:
        from app.models.report import Report
        report_assignments = [
            ("alice@example.com", None, 0),
            ("bob@example.com", "drsarah@example.com", 1),
            ("carol@example.com", "drmike@example.com", 2),
        ]
        for patient_email, doctor_email, idx in report_assignments:
            data = dict(self.REPORTS[idx])
            data["patient_id"] = self.patients[patient_email]
            if doctor_email:
                data["doctor_id"] = self.doctors[doctor_email]
            r = self._get_or_create(Report, {"file_path": data["file_path"]}, data)
            self.reports[patient_email] = r.id

    def _seed_medicines(self) -> None:
        from app.models.medicine import Medicine
        alice_id = self.patients["alice@example.com"]
        report_id = self.reports["alice@example.com"]

        for i, med in enumerate(self.MEDICINES):
            data = dict(med)
            data["patient_id"] = alice_id
            data["report_id"] = report_id
            lookup_key = f"{alice_id}_{med['name']}"
            m = self._get_or_create(Medicine, {"name": med["name"], "patient_id": alice_id}, data)
            self.medicines[lookup_key] = m.id

    def _seed_appointments(self) -> None:
        from app.models.appointment import Appointment
        appointment_data = [
            ("alice@example.com", "drsarah@example.com", 0),
            ("alice@example.com", "drsarah@example.com", 1),
            ("bob@example.com", "drsarah@example.com", 2),
            ("bob@example.com", "drsarah@example.com", 3),
            ("carol@example.com", "drmike@example.com", 4),
        ]
        for patient_email, doctor_email, idx in appointment_data:
            data = dict(self.APPOINTMENTS[idx])
            data["patient_id"] = self.patients[patient_email]
            data["doctor_id"] = self.doctors[doctor_email]
            self._get_or_create(
                Appointment,
                {
                    "patient_id": self.patients[patient_email],
                    "doctor_id": self.doctors[doctor_email],
                    "scheduled_at": data["scheduled_at"],
                },
                data,
            )

    def _seed_chat(self) -> None:
        from app.models.chat_history import ChatHistory
        alice_id = self.patients["alice@example.com"]
        base_time = datetime(2026, 7, 14, 8, 0, tzinfo=timezone.utc)
        for i, msg in enumerate(self.CHAT_MESSAGES):
            data = dict(msg)
            data["patient_id"] = alice_id
            self._get_or_create(
                ChatHistory,
                {
                    "patient_id": alice_id,
                    "message": msg["message"],
                },
                data,
            )

    def _seed_adherence(self) -> None:
        from app.models.adherence_log import AdherenceLog
        alice_id = self.patients["alice@example.com"]
        med_id = self.medicines.get(f"{alice_id}_Lisinopril")
        if not med_id:
            return
        for log in self.ADHERENCE_LOGS:
            data = dict(log)
            data["patient_id"] = alice_id
            data["medicine_id"] = med_id
            self._get_or_create(
                AdherenceLog,
                {
                    "patient_id": alice_id,
                    "medicine_id": med_id,
                    "scheduled_time": data["scheduled_time"],
                },
                data,
            )

    def _seed_emergency_alerts(self) -> None:
        from app.models.emergency_alert import EmergencyAlert
        alice_id = self.patients["alice@example.com"]
        for alert in self.EMERGENCY_ALERTS:
            data = dict(alert)
            data["patient_id"] = alice_id
            self._get_or_create(
                EmergencyAlert,
                {
                    "patient_id": alice_id,
                    "symptoms": alert["symptoms"],
                },
                data,
            )
