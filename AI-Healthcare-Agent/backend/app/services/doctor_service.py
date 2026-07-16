import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.patient_doctor import PatientDoctor
from app.repositories.doctor_repository import DoctorRepository


class DoctorService:
    def __init__(self, db: Session):
        self.db = db
        self.doctor_repo = DoctorRepository(db)

    def get_doctor(self, doctor_id: str) -> Doctor:
        doctor = self.doctor_repo.get(uuid.UUID(doctor_id))
        if not doctor:
            raise NotFoundException("Doctor", doctor_id)
        return doctor

    def get_doctor_patients(self, doctor_id: str) -> list[Patient]:
        doctor = self.get_doctor(doctor_id)
        return [
            pd.patient
            for pd in doctor.patient_assignments
            if pd.is_active
        ]

    def assign_patient(self, doctor_id: str, patient_id: str) -> PatientDoctor:
        doctor = self.get_doctor(doctor_id)
        patient_uuid = uuid.UUID(patient_id)

        existing = (
            self.db.query(PatientDoctor)
            .filter(
                PatientDoctor.doctor_id == doctor.id,
                PatientDoctor.patient_id == patient_uuid,
            )
            .first()
        )
        if existing:
            if not existing.is_active:
                existing.is_active = True
                self.db.commit()
            return existing

        assignment = PatientDoctor(
            doctor_id=doctor.id,
            patient_id=patient_uuid,
        )
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment
