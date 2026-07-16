import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.chat_history import ChatHistory
from app.repositories.base import BaseRepository


class ChatRepository(BaseRepository[ChatHistory]):
    def __init__(self, db: Session):
        super().__init__(db, ChatHistory)

    def get_by_patient(self, patient_id: uuid.UUID, limit: int = 50) -> list[ChatHistory]:
        query = (
            select(ChatHistory)
            .where(ChatHistory.patient_id == patient_id)
            .order_by(ChatHistory.created_at.asc())
            .limit(limit)
        )
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_recent_context(self, patient_id: uuid.UUID, limit: int = 10) -> list[ChatHistory]:
        query = (
            select(ChatHistory)
            .where(ChatHistory.patient_id == patient_id)
            .order_by(ChatHistory.created_at.desc())
            .limit(limit)
        )
        result = self.db.execute(query)
        return list(reversed(result.scalars().all()))

    def clear_patient_history(self, patient_id: uuid.UUID) -> None:
        query = delete(ChatHistory).where(ChatHistory.patient_id == patient_id)
        self.db.execute(query)
        self.db.commit()

    def count_by_patient(self, patient_id: uuid.UUID) -> int:
        query = select(func.count()).select_from(ChatHistory).where(
            ChatHistory.patient_id == patient_id
        )
        result = self.db.execute(query)
        return result.scalar() or 0
