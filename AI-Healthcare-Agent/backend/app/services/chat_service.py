import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.chat_history import ChatHistory
from app.repositories.chat_repository import ChatRepository


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.chat_repo = ChatRepository(db)

    def save_message(
        self,
        patient_id: str,
        role: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> ChatHistory:
        chat = ChatHistory(
            patient_id=uuid.UUID(patient_id),
            role=role,
            message=message,
            metadata=metadata,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(chat)
        self.db.commit()
        self.db.refresh(chat)
        return chat

    def get_history(self, patient_id: str, limit: int = 50) -> list[ChatHistory]:
        return self.chat_repo.get_by_patient(uuid.UUID(patient_id), limit=limit)

    def get_recent_context(self, patient_id: str, limit: int = 10) -> list[ChatHistory]:
        return self.chat_repo.get_recent_context(uuid.UUID(patient_id), limit=limit)

    def clear_history(self, patient_id: str) -> None:
        self.chat_repo.clear_patient_history(uuid.UUID(patient_id))
