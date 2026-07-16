import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.models.medicine import Medicine
from app.repositories.medicine_repository import MedicineRepository


class MedicineService:
    def __init__(self, db: Session):
        self.db = db
        self.medicine_repo = MedicineRepository(db)

    def create_medicine(self, data: dict) -> Medicine:
        medicine = Medicine(**data)
        self.db.add(medicine)
        self.db.commit()
        self.db.refresh(medicine)
        return medicine

    def get_medicine(self, medicine_id: str) -> Medicine:
        medicine = self.medicine_repo.get(uuid.UUID(medicine_id))
        if not medicine:
            raise NotFoundException("Medicine", medicine_id)
        return medicine

    def get_patient_medicines(self, patient_id: str) -> list[Medicine]:
        return self.medicine_repo.get_by_patient(uuid.UUID(patient_id))

    def get_active_medicines(self, patient_id: str) -> list[Medicine]:
        return self.medicine_repo.get_active_by_patient(uuid.UUID(patient_id))

    def update_medicine(self, medicine_id: str, data: dict) -> Medicine:
        medicine = self.get_medicine(medicine_id)
        for key, value in data.items():
            if value is not None and hasattr(medicine, key):
                setattr(medicine, key, value)
        self.db.commit()
        self.db.refresh(medicine)
        return medicine
