import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.patient_doctor import PatientDoctor
from app.repositories.patient_repository import PatientRepository


class PatientService:
    def __init__(self, db: Session):
        self.db = db
        self.patient_repo = PatientRepository(db)

    def get_patient(self, patient_id: str) -> Patient:
        patient = self.patient_repo.get(uuid.UUID(patient_id))
        if not patient:
            raise NotFoundException("Patient", patient_id)
        return patient

    def update_patient(self, patient_id: str, data: dict) -> Patient:
        patient = self.get_patient(patient_id)
        for key, value in data.items():
            if value is not None and hasattr(patient, key):
                setattr(patient, key, value)
        self.db.commit()
        self.db.refresh(patient)
        return patient

    def get_patient_doctors(self, patient_id: str) -> list[Doctor]:
        patient = self.get_patient(patient_id)
        return [pd.doctor for pd in patient.doctor_assignments if pd.is_active]
