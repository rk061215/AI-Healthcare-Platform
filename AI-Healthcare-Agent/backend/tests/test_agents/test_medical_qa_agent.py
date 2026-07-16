from __future__ import annotations

from typing import Any, Optional
from unittest.mock import MagicMock

import pytest

from app.agents.agent_context import AgentContext
from app.agents.agent_response import AgentResponse
from app.agents.agents.medical_qa_agent import MedicalQAAgent
from app.agents.config import AgentConfig
from app.agents.exceptions import AgentValidationError
from app.chat.models import (
    ChatRequest,
    ChatResponse,
    ConfidenceLevel,
    ConfidenceScore,
    SuggestedQuestion,
)
from app.rag.models import RAGResponse


def make_mock_chat_response(
    answer: str = "Your medication is lisinopril 10mg daily.",
    session_id: str = "s1",
) -> ChatResponse:
    return ChatResponse(
        answer=answer,
        session_id=session_id,
        confidence=ConfidenceScore(
            overall=0.85,
            level=ConfidenceLevel.high,
            retrieval_score=0.8,
            chunk_count=3,
            citation_coverage=0.67,
            guardrail_validated=True,
        ),
        suggested_questions=[
            SuggestedQuestion(question="What are the side effects?", category="medication", priority=1),
        ],
        query_type="medication",
        is_follow_up=False,
        processing_time_ms=150.0,
    )


class TestMedicalQAAgent:
    def test_initialization(self) -> None:
        agent = MedicalQAAgent()
        assert isinstance(agent, MedicalQAAgent)
        assert agent.config.agent_type == "base"

    def test_custom_config(self) -> None:
        config = AgentConfig(agent_type="medical_qa")
        agent = MedicalQAAgent(config=config)
        assert agent.config.agent_type == "medical_qa"

    def test_initialize_creates_chat_service(self) -> None:
        agent = MedicalQAAgent(rag_engine=MagicMock())
        assert agent.chat_service is None
        agent.initialize()
        assert agent.chat_service is not None

    def test_can_handle_with_query(self) -> None:
        agent = MedicalQAAgent()
        context = AgentContext(query="What is my diagnosis?", session_id="s1")
        assert agent.can_handle(context) is True

    def test_can_handle_empty_query(self) -> None:
        agent = MedicalQAAgent()
        context = AgentContext(query="", session_id="s1")
        assert agent.can_handle(context) is False

    def test_invoke_rag_with_mock(self) -> None:
        agent = MedicalQAAgent()
        mock_service = MagicMock()
        mock_service.ask.return_value = make_mock_chat_response()
        agent._chat_service = mock_service

        context = AgentContext(query="What medication?", session_id="s1")
        response = agent.invoke_rag(context)
        assert response.success is True
        assert "lisinopril" in response.answer
        mock_service.ask.assert_called_once()

    def test_invoke_rag_empty_query(self) -> None:
        agent = MedicalQAAgent()
        mock_service = MagicMock()
        from app.chat.exceptions import EmptyQuestionError
        mock_service.ask.side_effect = EmptyQuestionError("Question cannot be empty")
        agent._chat_service = mock_service

        context = AgentContext(query="", session_id="s1")
        response = agent.invoke_rag(context)
        assert response.success is False

    def test_validate_response_raises_on_empty(self) -> None:
        agent = MedicalQAAgent()
        response = AgentResponse.ok(answer="", session_id="s1")
        with pytest.raises(AgentValidationError):
            agent.validate_response(response)

    def test_validate_passes_with_answer(self) -> None:
        agent = MedicalQAAgent()
        response = AgentResponse.ok(answer="Valid answer", session_id="s1")
        result = agent.validate_response(response)
        assert result.success is True

    def test_prepare_context_without_init(self) -> None:
        agent = MedicalQAAgent(rag_engine=MagicMock())
        context = AgentContext(query="test", session_id="s1")
        result = agent.prepare_context(context)
        assert result is context
        assert agent.chat_service is not None

    def test_cleanup_noop(self) -> None:
        agent = MedicalQAAgent()
        agent.cleanup()

    def test_retrieve_memory_returns_context(self) -> None:
        agent = MedicalQAAgent()
        context = AgentContext(query="test", session_id="s1")
        result = agent.retrieve_memory(context)
        assert result is context

    def test_retrieve_documents_returns_context(self) -> None:
        agent = MedicalQAAgent()
        context = AgentContext(query="test", session_id="s1")
        result = agent.retrieve_documents(context)
        assert result is context

    def test_post_process_returns_same(self) -> None:
        agent = MedicalQAAgent()
        response = AgentResponse.ok(answer="test", session_id="s1")
        context = AgentContext(query="test", session_id="s1")
        result = agent.post_process(response, context)
        assert result is response

    def test_create_session(self) -> None:
        agent = MedicalQAAgent()
        mock_service = MagicMock()
        mock_service.create_session.return_value = "session_123"
        agent._chat_service = mock_service
        sid = agent.create_session(report_id="rep1")
        assert sid == "session_123"
        mock_service.create_session.assert_called_once()

    def test_get_suggestions(self) -> None:
        agent = MedicalQAAgent()
        mock_service = MagicMock()
        mock_service.get_suggestions.return_value = [
            SuggestedQuestion(question="What next?", category="follow_up", priority=1),
        ]
        agent._chat_service = mock_service
        suggestions = agent.get_suggestions("s1")
        assert len(suggestions) == 1
        assert suggestions[0].question == "What next?"

    def test_agent_config_property(self) -> None:
        agent = MedicalQAAgent()
        assert isinstance(agent.config, AgentConfig)
