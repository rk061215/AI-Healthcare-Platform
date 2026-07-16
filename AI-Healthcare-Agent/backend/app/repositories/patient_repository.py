from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.repositories.base import BaseRepository


class PatientRepository(BaseRepository[Patient]):
    def __init__(self, db: Session):
        super().__init__(db, Patient)

    def get_by_email(self, email: str) -> Patient | None:
        query = select(Patient).where(Patient.email == email)
        result = self.db.execute(query)
        return result.scalar_one_or_none()

    def get_active_patients(self, skip: int = 0, limit: int = 100) -> list[Patient]:
        return self.get_multi(
            skip=skip, limit=limit, filters={"is_active": True}
        )
