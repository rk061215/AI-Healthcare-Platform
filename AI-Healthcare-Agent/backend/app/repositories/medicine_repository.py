import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.medicine import Medicine
from app.repositories.base import BaseRepository


class MedicineRepository(BaseRepository[Medicine]):
    def __init__(self, db: Session):
        super().__init__(db, Medicine)

    def get_by_patient(self, patient_id: uuid.UUID) -> list[Medicine]:
        query = (
            select(Medicine)
            .where(Medicine.patient_id == patient_id)
            .order_by(Medicine.created_at.desc())
        )
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_active_by_patient(self, patient_id: uuid.UUID) -> list[Medicine]:
        query = (
            select(Medicine)
            .where(Medicine.patient_id == patient_id, Medicine.is_active == True)
            .order_by(Medicine.created_at.desc())
        )
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_by_report(self, report_id: uuid.UUID) -> list[Medicine]:
        query = select(Medicine).where(Medicine.report_id == report_id)
        result = self.db.execute(query)
        return list(result.scalars().all())
