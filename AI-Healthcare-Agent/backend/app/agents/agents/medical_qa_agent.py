from __future__ import annotations

from typing import Any, Optional

from app.agents.agent_context import AgentContext
from app.agents.agent_response import AgentResponse
from app.agents.base_agent import BaseAgent
from app.agents.config import AgentConfig
from app.agents.exceptions import AgentValidationError
from app.chat.chat_service import ChatService
from app.chat.chat_session import SessionManager
from app.chat.config import ChatConfig as ChatModuleConfig
from app.chat.confidence import ConfidenceCalculator
from app.chat.exceptions import EmptyQuestionError
from app.chat.models import ChatRequest
from app.chat.question_suggester import QuestionSuggester
from app.chat.response_formatter import ResponseFormatter
from app.memory.exceptions import MemoryNotFoundError
from app.memory.memory_service import MemoryService
from app.rag import RAGEngine, RAGEngineConfig


class MedicalQAAgent(BaseAgent):
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        chat_config: Optional[ChatModuleConfig] = None,
        rag_config: Optional[RAGEngineConfig] = None,
        rag_engine: Optional[RAGEngine] = None,
        session_manager: Optional[SessionManager] = None,
        confidence_calculator: Optional[ConfidenceCalculator] = None,
        question_suggester: Optional[QuestionSuggester] = None,
        response_formatter: Optional[ResponseFormatter] = None,
        memory_service: Optional[MemoryService] = None,
    ) -> None:
        super().__init__(config=config)
        self._chat_service: Optional[ChatService] = None
        self._chat_config = chat_config or ChatModuleConfig()
        self._rag_config = rag_config or RAGEngineConfig(
            enable_guardrails_pre=True,
            enable_guardrails_post=True,
            enable_citations=True,
            enable_query_classification=True,
            enable_query_rewriting=False,
        )
        self._rag_engine = rag_engine
        self._session_manager = session_manager
        self._confidence_calculator = confidence_calculator
        self._question_suggester = question_suggester
        self._response_formatter = response_formatter
        self._memory_service = memory_service
        self._turn_counter: int = 0

    def initialize(self) -> None:
        self._chat_service = ChatService(
            rag_engine=self._rag_engine,
            session_manager=self._session_manager,
            confidence_calculator=self._confidence_calculator,
            question_suggester=self._question_suggester,
            response_formatter=self._response_formatter,
            config=self._chat_config,
            rag_config=self._rag_config,
        )
        if self._memory_service is None:
            self._memory_service = MemoryService()

    def can_handle(self, context: AgentContext) -> bool:
        return bool(context.query and context.query.strip())

    def prepare_context(self, context: AgentContext) -> AgentContext:
        if self._chat_service is None:
            self.initialize()
        return context

    def retrieve_memory(self, context: AgentContext) -> AgentContext:
        if self._memory_service is None:
            return context
        try:
            entries = self._memory_service.recall(
                session_id=context.session_id,
                limit=20,
            )
            context.memory_entries = [e.model_dump() for e in entries]
        except Exception:
            context.memory_entries = []
        return context

    def retrieve_documents(self, context: AgentContext) -> AgentContext:
        return context

    def invoke_rag(self, context: AgentContext) -> AgentResponse:
        if self._chat_service is None:
            self.initialize()
        try:
            conversation_history = self._format_memory_entries(context.memory_entries)
            chat_request = ChatRequest(
                query=context.query,
                session_id=context.session_id,
                patient_id=context.patient_id,
                report_id=context.report_id,
                document_type=context.document_type,
                document_sections=context.document_sections,
            )
            chat_response = self._chat_service.ask(
                chat_request,
                conversation_history=conversation_history,
            )
            self._persist_memory(context, chat_response)
            return AgentResponse.ok(
                answer=chat_response.answer,
                session_id=chat_response.session_id or context.session_id,
                citations=chat_response.citations,
                metadata={
                    "query_type": chat_response.query_type,
                    "is_follow_up": chat_response.is_follow_up,
                    "confidence": chat_response.confidence.model_dump() if hasattr(chat_response.confidence, "model_dump") else {},
                    "suggested_questions": [
                        sq.model_dump() if hasattr(sq, "model_dump") else {"question": sq.question}
                        for sq in chat_response.suggested_questions
                    ],
                    "processing_time_ms": chat_response.processing_time_ms,
                },
            )
        except EmptyQuestionError as exc:
            return AgentResponse.error(error=str(exc), session_id=context.session_id)
        except Exception as exc:
            return AgentResponse.error(error=str(exc), session_id=context.session_id)

    def post_process(self, response: AgentResponse, context: AgentContext) -> AgentResponse:
        return response

    def validate_response(self, response: AgentResponse) -> AgentResponse:
        if response.success and not response.answer.strip():
            raise AgentValidationError("Agent returned an empty answer")
        return response

    def cleanup(self) -> None:
        pass

    @property
    def chat_service(self) -> Optional[ChatService]:
        return self._chat_service

    @property
    def memory_service(self) -> Optional[MemoryService]:
        return self._memory_service

    def _format_memory_entries(self, entries: list[dict[str, Any]]) -> str:
        if not entries:
            return ""
        lines: list[str] = []
        for entry in entries[-10:]:
            content = entry.get("content", {})
            q = content.get("query", "")
            a = content.get("answer", "")
            if q and a:
                lines.append(f"User: {q}")
                lines.append(f"Assistant: {a}")
        return "\n".join(lines)

    def _persist_memory(
        self,
        context: AgentContext,
        chat_response: Any,
    ) -> None:
        if self._memory_service is None:
            return
        try:
            self._turn_counter += 1
            confidence_val = 0.0
            if hasattr(chat_response, "confidence") and chat_response.confidence:
                confidence_val = getattr(chat_response.confidence, "overall", 0.0) or 0.0
            self._memory_service.extract_from_chat(
                session_id=context.session_id,
                query=context.query,
                answer=chat_response.answer,
                query_type=getattr(chat_response, "query_type", "unknown"),
                confidence=confidence_val,
                turn_number=self._turn_counter,
                follow_up=getattr(chat_response, "is_follow_up", False),
            )
        except (MemoryNotFoundError, Exception):
            pass

    def create_session(
        self,
        session_id: Optional[str] = None,
        document_id: Optional[str] = None,
        report_id: Optional[str] = None,
        document_type: Optional[str] = None,
        document_sections: Optional[list[str]] = None,
    ) -> str:
        if self._chat_service is None:
            self.initialize()
        return self._chat_service.create_session(
            session_id=session_id,
            document_id=document_id,
            report_id=report_id,
            document_type=document_type,
            document_sections=document_sections,
        )

    def get_suggestions(
        self,
        session_id: str,
        document_sections: Optional[list[str]] = None,
    ) -> Any:
        if self._chat_service is None:
            self.initialize()
        return self._chat_service.get_suggestions(
            session_id=session_id,
            document_sections=document_sections,
        )
