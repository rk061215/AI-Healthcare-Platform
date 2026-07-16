from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.doctor import Doctor
from app.repositories.base import BaseRepository


class DoctorRepository(BaseRepository[Doctor]):
    def __init__(self, db: Session):
        super().__init__(db, Doctor)

    def get_by_email(self, email: str) -> Doctor | None:
        query = select(Doctor).where(Doctor.email == email)
        result = self.db.execute(query)
        return result.scalar_one_or_none()
