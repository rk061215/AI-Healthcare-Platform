from __future__ import annotations

import time
from typing import Optional

from app.chat.config import ChatConfig
from app.chat.exceptions import (
    MaxQuestionsExceededError,
    SessionExpiredError,
    SessionNotFoundError,
)
from app.chat.models import ChatSession, QAPair


class SessionManager:
    """Lightweight in-memory session manager with TTL expiry.

    No persistent storage. Sessions exist only in memory and expire
    after a configurable inactivity timeout.
    """

    def __init__(self, config: Optional[ChatConfig] = None) -> None:
        self._config = config or ChatConfig()
        self._sessions: dict[str, ChatSession] = {}
        self._last_access: dict[str, float] = {}

    def create_session(
        self,
        session_id: str,
        document_id: Optional[str] = None,
        report_id: Optional[str] = None,
        document_type: Optional[str] = None,
        document_sections: Optional[list[str]] = None,
    ) -> ChatSession:
        session = ChatSession(
            session_id=session_id,
            document_id=document_id,
            report_id=report_id,
            document_type=document_type,
            document_sections=document_sections or [],
        )
        self._update_document_flags(session)
        self._sessions[session_id] = session
        self._last_access[session_id] = time.time()
        return session

    def get_session(self, session_id: str) -> ChatSession:
        if session_id not in self._sessions:
            raise SessionNotFoundError(f"Session '{session_id}' not found")

        if self._is_expired(session_id):
            self.delete_session(session_id)
            raise SessionExpiredError(
                f"Session '{session_id}' has expired due to inactivity"
            )

        self._last_access[session_id] = time.time()
        return self._sessions[session_id]

    def add_qa_pair(self, session_id: str, qa: QAPair) -> None:
        session = self.get_session(session_id)
        if len(session.questions) >= self._config.max_questions_per_session:
            raise MaxQuestionsExceededError(
                f"Session '{session_id}' has reached the maximum of "
                f"{self._config.max_questions_per_session} questions"
            )
        session.questions.append(qa)
        session.last_active_at = qa.timestamp

    def get_recent_qa(self, session_id: str, count: int = 5) -> list[QAPair]:
        session = self.get_session(session_id)
        return session.questions[-count:]

    def get_question_count(self, session_id: str) -> int:
        session = self.get_session(session_id)
        return len(session.questions)

    def update_document(
        self,
        session_id: str,
        document_id: Optional[str] = None,
        report_id: Optional[str] = None,
        document_type: Optional[str] = None,
        document_sections: Optional[list[str]] = None,
    ) -> None:
        session = self.get_session(session_id)
        if document_id is not None:
            session.document_id = document_id
        if report_id is not None:
            session.report_id = report_id
        if document_type is not None:
            session.document_type = document_type
        if document_sections is not None:
            session.document_sections = document_sections
        self._update_document_flags(session)

    def delete_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
        self._last_access.pop(session_id, None)

    def cleanup_expired(self) -> int:
        now = time.time()
        expired = [
            sid
            for sid, last in self._last_access.items()
            if (now - last) > self._config.session_timeout_minutes * 60
        ]
        for sid in expired:
            self.delete_session(sid)
        return len(expired)

    def session_count(self) -> int:
        return len(self._sessions)

    def is_follow_up_question(self, session_id: str) -> bool:
        try:
            session = self.get_session(session_id)
            return len(session.questions) > 0
        except (SessionNotFoundError, SessionExpiredError):
            return False

    def _is_expired(self, session_id: str) -> bool:
        last = self._last_access.get(session_id, 0.0)
        elapsed = time.time() - last
        return elapsed > self._config.session_timeout_minutes * 60

    def _update_document_flags(self, session: ChatSession) -> None:
        sections_lower = [s.lower() for s in session.document_sections]
        session.document_has_diagnosis = any(
            "diagnosis" in s or "assessment" in s for s in sections_lower
        )
        session.document_has_medication = any(
            "medication" in s or "prescription" in s or "medicine" in s
            for s in sections_lower
        )
        session.document_has_lab_results = any(
            "lab" in s or "result" in s or "test" in s for s in sections_lower
        )
        session.document_has_follow_up = any(
            "follow" in s or "plan" in s or "next" in s for s in sections_lower
        )
