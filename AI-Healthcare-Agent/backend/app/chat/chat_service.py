from __future__ import annotations

import time
import uuid
from typing import TYPE_CHECKING, Any, Optional

from app.chat.chat_session import SessionManager
from app.chat.config import ChatConfig
from app.chat.confidence import ConfidenceCalculator
from app.chat.exceptions import (
    ChatError,
    EmptyQuestionError,
    NoDocumentInSessionError,
    QuestionGenerationError,
)
from app.chat.models import (
    CHAT_SCHEMA_VERSION,
    ChatRequest,
    ChatResponse,
    ConfidenceScore,
    QAPair,
    SuggestedQuestion,
)
from app.chat.question_suggester import QuestionSuggester
from app.chat.response_formatter import ResponseFormatter
from app.rag import RAGEngine, RAGEngineConfig, RAGRequest, RAGResponse

if TYPE_CHECKING:
    from app.langgraph.graphs.medical_qa_graph import MedicalQAGraph


class ChatService:
    def __init__(
        self,
        rag_engine: Optional[RAGEngine] = None,
        session_manager: Optional[SessionManager] = None,
        confidence_calculator: Optional[ConfidenceCalculator] = None,
        question_suggester: Optional[QuestionSuggester] = None,
        response_formatter: Optional[ResponseFormatter] = None,
        config: Optional[ChatConfig] = None,
        rag_config: Optional[RAGEngineConfig] = None,
        medical_qa_graph: Optional[MedicalQAGraph] = None,
    ) -> None:
        self._config = config or ChatConfig()
        self._rag_config = rag_config or RAGEngineConfig(
            enable_guardrails_pre=True,
            enable_guardrails_post=True,
            enable_citations=True,
            enable_query_classification=True,
            enable_query_rewriting=False,
        )
        self._rag_engine = rag_engine or RAGEngine(config=self._rag_config)
        self._sessions = session_manager or SessionManager(config=self._config)
        self._confidence = confidence_calculator or ConfidenceCalculator(
            min_chunks=self._config.confidence_min_chunks,
            min_score=self._config.confidence_min_score,
            citation_coverage_min=self._config.confidence_citation_coverage_min,
        )
        self._suggester = question_suggester or QuestionSuggester(
            max_suggestions=self._config.max_suggested_questions,
        )
        self._formatter = response_formatter or ResponseFormatter()
        self._graph: Optional[MedicalQAGraph] = medical_qa_graph
        self._graph_available = medical_qa_graph is not None

    def ask(self, request: ChatRequest, conversation_history: str = "", document_text: Optional[str] = None) -> ChatResponse:
        overall_start = time.perf_counter()

        if not request.query or not request.query.strip():
            raise EmptyQuestionError("Question cannot be empty")

        session_id = request.session_id or self._create_session_id()
        session = self._get_or_create_session(session_id, request)
        is_follow_up = self._sessions.is_follow_up_question(session_id)

        if self._graph_available:
            try:
                return self._ask_via_graph(
                    request, session_id, session, is_follow_up, conversation_history, overall_start
                )
            except Exception as exc:
                raise ChatError(f"Graph execution failed: {exc}") from exc
        else:
            return self._ask_direct(
                request, session_id, session, is_follow_up, conversation_history, overall_start, document_text
            )

    def _ask_via_graph(
        self,
        request: ChatRequest,
        session_id: str,
        session: Any,
        is_follow_up: bool,
        conversation_history: str,
        overall_start: float,
    ) -> ChatResponse:
        from app.langgraph.graph_state import GraphState
        graph_state = GraphState(
            query=request.query,
            session_id=session_id,
            patient_id=request.patient_id or "",
            report_id=request.report_id or session.report_id,
            document_id=request.report_id,
            document_type=request.document_type or session.document_type,
            document_sections=request.document_sections or session.document_sections,
            conversation_history=conversation_history,
            language="en",
        )
        graph_state.services["rag_engine"] = self._rag_engine
        graph_state.services["session_manager"] = self._sessions

        memory_svc = getattr(self, "_memory_service", None)
        if memory_svc is not None:
            graph_state.services["memory_service"] = memory_svc

        context_builder_svc = getattr(self, "_context_builder", None)
        if context_builder_svc is not None:
            graph_state.services["context_builder"] = context_builder_svc

        result_state = self._graph.execute(graph_state)

        agent_resp = result_state.agent_response or {}
        rag_resp = result_state.rag_response or {}

        if agent_resp.get("success"):
            answer_text = agent_resp.get("answer", result_state.final_response or "")
            raw_citations = agent_resp.get("citations", [])
        else:
            answer_text = result_state.final_response or rag_resp.get("answer", "")
            raw_citations = result_state.retrieved_evidence or []

        confidence = self._calculate_confidence_from_graph(result_state)

        suggested = self._generate_suggestions(session, request.query)

        formatted = self._formatter.format_answer(
            answer=answer_text,
            confidence=confidence,
            citations=raw_citations,
            suggested_questions=suggested,
            query_type=rag_resp.get("query_type", "unknown"),
            is_follow_up=is_follow_up,
        )

        qa = QAPair(
            question=request.query,
            answer=formatted["answer"],
            citations=formatted["citations"],
            confidence=confidence,
            query_type=rag_resp.get("query_type", "unknown"),
            processing_time_ms=(time.perf_counter() - overall_start) * 1000,
        )
        self._sessions.add_qa_pair(session_id, qa)

        total_ms = round((time.perf_counter() - overall_start) * 1000, 2)

        return ChatResponse(
            answer=formatted["answer"],
            citations=formatted["citations"],
            confidence=confidence,
            suggested_questions=formatted["suggested_questions"],
            session_id=session_id,
            query_type=rag_resp.get("query_type", "unknown"),
            is_follow_up=is_follow_up,
            processing_time_ms=total_ms,
        )

    def _ask_direct(
        self,
        request: ChatRequest,
        session_id: str,
        session: Any,
        is_follow_up: bool,
        conversation_history: str,
        overall_start: float,
        document_text: Optional[str] = None,
    ) -> ChatResponse:
        try:
            rag_response = self._rag_engine.answer(
                RAGRequest(
                    query=request.query,
                    patient_id=request.patient_id,
                    report_id=session.report_id or request.report_id,
                    document_type=session.document_type or request.document_type,
                    top_k=request.top_k or self._config.default_top_k,
                    temperature=request.temperature or self._config.default_temperature,
                    max_tokens=request.max_tokens or self._config.default_max_tokens,
                    enable_citations=request.enable_citations,
                    conversation_history=conversation_history,
                ),
                document_text=document_text,
            )
        except Exception as exc:
            raise ChatError(f"Failed to process question: {exc}") from exc

        confidence = self._calculate_confidence(rag_response)

        suggested = self._generate_suggestions(session, request.query)

        formatted = self._formatter.format_answer(
            answer=rag_response.answer,
            confidence=confidence,
            citations=rag_response.citations.citations if rag_response.citations else [],
            suggested_questions=suggested,
            query_type=rag_response.query_type,
            is_follow_up=is_follow_up,
        )

        qa = QAPair(
            question=request.query,
            answer=formatted["answer"],
            citations=formatted["citations"],
            confidence=confidence,
            query_type=rag_response.query_type,
            processing_time_ms=(time.perf_counter() - overall_start) * 1000,
        )
        self._sessions.add_qa_pair(session_id, qa)

        total_ms = round((time.perf_counter() - overall_start) * 1000, 2)

        return ChatResponse(
            answer=formatted["answer"],
            citations=formatted["citations"],
            confidence=confidence,
            suggested_questions=formatted["suggested_questions"],
            session_id=session_id,
            query_type=rag_response.query_type,
            timing_breakdown=getattr(rag_response, 'timing_breakdown', {}),
            is_follow_up=is_follow_up,
            processing_time_ms=total_ms,
        )

    def _calculate_confidence_from_graph(self, state: GraphState) -> ConfidenceScore:
        rag_resp = state.rag_response or {}
        retrieval_scores: list[float] = []
        for ev in state.retrieved_evidence or []:
            score = ev.get("score", 0.0)
            if score > 0:
                retrieval_scores.append(score)
        num_citations = len(state.retrieved_evidence or [])
        return self._confidence.calculate(
            retrieval_scores=retrieval_scores,
            num_citations=num_citations,
            guardrail_passed=True,
            guardrail_failures=[],
            answer_text=state.final_response or "",
            has_sufficient_context=num_citations > 0,
        )

    def get_session_questions(
        self, session_id: str, count: int = 10
    ) -> list[QAPair]:
        return self._sessions.get_recent_qa(session_id, count)

    def get_suggestions(
        self,
        session_id: str,
        document_sections: Optional[list[str]] = None,
    ) -> list[SuggestedQuestion]:
        try:
            session = self._sessions.get_session(session_id)
            recent = [qa.question for qa in session.questions[-3:]]
            return self._suggester.suggest(
                document_sections=document_sections or session.document_sections,
                recent_questions=recent,
                document_has_diagnosis=session.document_has_diagnosis,
                document_has_medication=session.document_has_medication,
                document_has_lab_results=session.document_has_lab_results,
                document_has_follow_up=session.document_has_follow_up,
            )
        except Exception as exc:
            raise QuestionGenerationError(
                f"Failed to generate suggestions: {exc}"
            ) from exc

    def create_session(
        self,
        session_id: Optional[str] = None,
        document_id: Optional[str] = None,
        report_id: Optional[str] = None,
        document_type: Optional[str] = None,
        document_sections: Optional[list[str]] = None,
    ) -> str:
        sid = session_id or self._create_session_id()
        self._sessions.create_session(
            session_id=sid,
            document_id=document_id,
            report_id=report_id,
            document_type=document_type,
            document_sections=document_sections,
        )
        return sid

    def update_session_document(
        self,
        session_id: str,
        document_id: Optional[str] = None,
        report_id: Optional[str] = None,
        document_type: Optional[str] = None,
        document_sections: Optional[list[str]] = None,
    ) -> None:
        self._sessions.update_document(
            session_id=session_id,
            document_id=document_id,
            report_id=report_id,
            document_type=document_type,
            document_sections=document_sections,
        )

    def delete_session(self, session_id: str) -> None:
        self._sessions.delete_session(session_id)

    def get_session_count(self) -> int:
        return self._sessions.session_count()

    def cleanup_expired_sessions(self) -> int:
        return self._sessions.cleanup_expired()

    def _calculate_confidence(
        self, rag_response: RAGResponse
    ) -> ConfidenceScore:
        retrieval_scores: list[float] = []
        if rag_response.citations:
            retrieval_scores = [
                c.score for c in rag_response.citations.citations
                if c.score > 0
            ]

        guardrail_failures: list[str] = []
        if rag_response.guardrail_result:
            guardrail_failures = rag_response.guardrail_result.failures

        num_citations = (
            rag_response.citations.citation_count
            if rag_response.citations
            else 0
        )

        return self._confidence.calculate(
            retrieval_scores=retrieval_scores,
            num_citations=num_citations,
            guardrail_passed=rag_response.guardrail_result.passed
            if rag_response.guardrail_result
            else True,
            guardrail_failures=guardrail_failures,
            answer_text=rag_response.answer,
            has_sufficient_context=True,
        )

    def _generate_suggestions(
        self,
        session: Any,
        current_query: str,
    ) -> list[SuggestedQuestion]:
        if not self._config.enable_question_suggestions:
            return []
        recent = [qa.question for qa in session.questions[-3:]]
        recent.append(current_query)
        return self._suggester.suggest(
            document_sections=session.document_sections,
            recent_questions=recent,
            document_has_diagnosis=session.document_has_diagnosis,
            document_has_medication=session.document_has_medication,
            document_has_lab_results=session.document_has_lab_results,
            document_has_follow_up=session.document_has_follow_up,
        )

    def _get_or_create_session(
        self, session_id: str, request: ChatRequest
    ) -> Any:
        try:
            return self._sessions.get_session(session_id)
        except Exception:
            return self._sessions.create_session(
                session_id=session_id,
                document_id=request.report_id,
                report_id=request.report_id,
                document_type=request.document_type,
                document_sections=request.document_sections,
            )

    def _create_session_id(self) -> str:
        return uuid.uuid4().hex[:16]
