from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.database.session import get_db
from app.langgraph.graph_checkpoint import BaseCheckpointStore
from app.models.checkpoint_entry import CheckpointEntry


class PostgresCheckpointStore(BaseCheckpointStore):
    def __init__(self, session: Optional[Session] = None) -> None:
        self._session = session or next(get_db())

    def save(self, checkpoint_id: str, state: dict[str, Any]) -> None:
        snapshot = dict(state)
        snapshot["_saved_at"] = datetime.now(timezone.utc).isoformat()
        entry = CheckpointEntry(
            checkpoint_id=checkpoint_id,
            session_id=state.get("session_id", ""),
            state=snapshot,
        )
        self._session.add(entry)
        self._session.commit()

    def load(self, checkpoint_id: str) -> Optional[dict[str, Any]]:
        entry = (
            self._session.query(CheckpointEntry)
            .filter(CheckpointEntry.checkpoint_id == checkpoint_id)
            .first()
        )
        if entry is None:
            return None
        return dict(entry.state)

    def list_checkpoints(self, session_id: str) -> list[dict[str, Any]]:
        entries = (
            self._session.query(CheckpointEntry)
            .filter(CheckpointEntry.session_id == session_id)
            .order_by(CheckpointEntry.saved_at.desc())
            .all()
        )
        return [
            {"checkpoint_id": e.checkpoint_id, "saved_at": e.saved_at.isoformat()}
            for e in entries
        ]

    def delete(self, checkpoint_id: str) -> bool:
        entry = (
            self._session.query(CheckpointEntry)
            .filter(CheckpointEntry.checkpoint_id == checkpoint_id)
            .first()
        )
        if entry is None:
            return False
        self._session.delete(entry)
        self._session.commit()
        return True

    def health_check(self) -> dict[str, Any]:
        try:
            count = self._session.query(CheckpointEntry).count()
            return {
                "provider": "postgresql",
                "checkpoint_count": count,
                "healthy": True,
            }
        except Exception as exc:
            return {
                "provider": "postgresql",
                "healthy": False,
                "error": str(exc),
            }
