import uuid

from sqlalchemy.orm import Session

from app.repositories.adherence_repository import AdherenceRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.emergency_repository import EmergencyRepository
from app.repositories.medicine_repository import MedicineRepository


class SummaryService:
    def __init__(self, db: Session):
        self.db = db
        self.medicine_repo = MedicineRepository(db)
        self.adherence_repo = AdherenceRepository(db)
        self.chat_repo = ChatRepository(db)
        self.emergency_repo = EmergencyRepository(db)

    def get_patient_summary_data(self, patient_id: str) -> dict:
        patient_uuid = uuid.UUID(patient_id)
        medicines = self.medicine_repo.get_active_by_patient(patient_uuid)
        alerts = self.emergency_repo.get_by_patient(patient_uuid)
        chat_history = self.chat_repo.get_by_patient(patient_uuid, limit=20)

        return {
            "medicines": medicines,
            "alerts": alerts,
            "chat_history": chat_history,
        }
