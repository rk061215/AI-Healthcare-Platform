from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.agents.agent_context import AgentContext
from app.agents.agent_executor import AgentExecutor
from app.agents.agent_factory import AgentFactory
from app.agents.agent_registry import get_global_registry
from app.agents.agent_response import AgentResponse
from app.agents.agent_service import AgentService
from app.agents.config import AgentConfig
from app.agents.agents.medical_qa_agent import MedicalQAAgent
from app.memory.memory_service import MemoryService
from app.memory.config import MemoryConfig


@pytest.fixture
def agent_config() -> AgentConfig:
    return AgentConfig(
        enable_memory=True,
        enable_rag=True,
        enable_tools=False,
        enable_evaluation=False,
        enable_telemetry=False,
    )


@pytest.fixture
def memory_service() -> MemoryService:
    return MemoryService(config=MemoryConfig(
        provider="in_memory",
        max_memories_per_session=50,
        enable_expiry_policy=False,
        enable_retention_policy=False,
    ))


@pytest.fixture
def sample_context() -> AgentContext:
    return AgentContext(
        query="What medicines are prescribed?",
        session_id="agent-test-session-1",
        patient_id="test-patient-1",
    )


class TestAgentLifecycle:
    def test_agent_initialization(self):
        with patch("app.agents.agents.medical_qa_agent.ChatService") as mock_chat:
            mock_chat.return_value = MagicMock()
            agent = MedicalQAAgent()
            agent.initialize()
            assert agent.chat_service is not None

    def test_agent_can_handle_valid_query(self):
        agent = MedicalQAAgent()
        ctx = AgentContext(query="What is my medicine?", session_id="s1")
        assert agent.can_handle(ctx) is True

    def test_agent_cannot_handle_empty_query(self):
        agent = MedicalQAAgent()
        ctx = AgentContext(query="", session_id="s1")
        assert agent.can_handle(ctx) is False

    def test_agent_cannot_handle_whitespace(self):
        agent = MedicalQAAgent()
        ctx = AgentContext(query="   ", session_id="s1")
        assert agent.can_handle(ctx) is False

    def test_agent_prepare_context_initializes(self):
        with patch("app.agents.agents.medical_qa_agent.ChatService") as mock_chat:
            mock_chat.return_value = MagicMock()
            agent = MedicalQAAgent()
            ctx = AgentContext(query="test", session_id="s1")
            result = agent.prepare_context(ctx)
            assert result is ctx
            assert agent.chat_service is not None


class TestAgentMemoryIntegration:
    def test_retrieve_memory_returns_context(self, memory_service):
        agent = MedicalQAAgent()
        agent._memory_service = memory_service
        ctx = AgentContext(query="test", session_id="memory-test-s1")
        memory_service.remember(
            session_id="memory-test-s1",
            content={"query": "Previous Q", "answer": "Previous A"},
            memory_type="conversation",
        )
        result = agent.retrieve_memory(ctx)
        assert result is ctx
        assert len(result.memory_entries) >= 1

    def test_retrieve_memory_empty_session(self, memory_service):
        agent = MedicalQAAgent()
        agent._memory_service = memory_service
        ctx = AgentContext(query="test", session_id="empty-mem-session")
        result = agent.retrieve_memory(ctx)
        assert result.memory_entries == []

    def test_retrieve_memory_no_memory_service(self):
        agent = MedicalQAAgent()
        agent._memory_service = None
        ctx = AgentContext(query="test", session_id="s1")
        result = agent.retrieve_memory(ctx)
        assert result.memory_entries == []

    def test_multiple_memory_entries_recalled(self, memory_service):
        agent = MedicalQAAgent()
        agent._memory_service = memory_service
        for i in range(3):
            memory_service.extract_from_chat(
                session_id="multi-mem-s1",
                query=f"Q{i}", answer=f"A{i}",
                turn_number=i,
            )
        ctx = AgentContext(query="Q3", session_id="multi-mem-s1")
        result = agent.retrieve_memory(ctx)
        assert len(result.memory_entries) >= 3


class TestAgentRAGInvocation:
    def test_invoke_rag_returns_agent_response(self, agent_config):
        with patch("app.agents.agents.medical_qa_agent.ChatService") as mock_chat_cls:
            mock_chat = MagicMock()
            mock_chat.ask.return_value = MagicMock(
                answer="You should take Lisinopril 10mg daily.",
                session_id="rag-test-s1",
                citations=[],
                query_type="medication",
                is_follow_up=False,
                confidence=MagicMock(overall=0.85),
                suggested_questions=[],
                processing_time_ms=100.0,
            )
            mock_chat_cls.return_value = mock_chat
            agent = MedicalQAAgent(config=agent_config)
            agent.initialize()
            ctx = AgentContext(query="What meds?", session_id="rag-test-s1", patient_id="p1")
            response = agent.invoke_rag(ctx)
            assert response.success
            assert "Lisinopril" in response.answer

    def test_invoke_rag_empty_query_handled(self, agent_config):
        with patch("app.agents.agents.medical_qa_agent.ChatService") as mock_chat:
            mock_chat.return_value = MagicMock()
            agent = MedicalQAAgent(config=agent_config)
            agent.initialize()
            ctx = AgentContext(query="", session_id="s1")
            response = agent.invoke_rag(ctx)
            assert response is not None


class TestAgentExecutor:
    def test_executor_full_lifecycle(self, agent_config):
        with patch("app.agents.agents.medical_qa_agent.ChatService") as mock_chat_cls:
            mock_chat = MagicMock()
            mock_chat.ask.return_value = MagicMock(
                answer="Lisinopril 10mg daily.",
                session_id="exec-test-s1",
                citations=[],
                query_type="medication",
                is_follow_up=False,
                confidence=MagicMock(overall=0.9),
                suggested_questions=[],
                processing_time_ms=50.0,
            )
            mock_chat.return_value = mock_chat
            mock_chat_cls.return_value = mock_chat

            agent = MedicalQAAgent(config=agent_config)
            executor = AgentExecutor(agent, config=agent_config)
            ctx = AgentContext(query="What meds?", session_id="exec-test-s1", patient_id="p1")
            response = executor.execute(ctx)
            assert response is not None
            assert hasattr(response, "success")
            assert hasattr(response, "session_id")
            assert hasattr(response, "trace_id")

    def test_executor_validates_response(self, agent_config):
        with patch("app.agents.agents.medical_qa_agent.ChatService") as mock_chat_cls:
            mock_chat = MagicMock()
            mock_chat.ask.return_value = MagicMock(
                answer="",
                session_id="exec-val-s1",
                citations=[],
                query_type="general",
                is_follow_up=False,
                confidence=MagicMock(overall=0.0),
                suggested_questions=[],
                processing_time_ms=10.0,
            )
            mock_chat_cls.return_value = mock_chat
            agent = MedicalQAAgent(config=agent_config)
            executor = AgentExecutor(agent, config=agent_config)
            ctx = AgentContext(query="test", session_id="exec-val-s1")
            response = executor.execute(ctx)
            assert response is not None

    def test_executor_phases_executed(self, agent_config):
        with patch("app.agents.agents.medical_qa_agent.ChatService") as mock_chat_cls:
            mock_chat = MagicMock()
            mock_chat.ask.return_value = MagicMock(
                answer="Answer.", session_id="s1",
                citations=[], query_type="general", is_follow_up=False,
                confidence=MagicMock(overall=0.5), suggested_questions=[],
                processing_time_ms=10.0,
            )
            mock_chat_cls.return_value = mock_chat
            agent = MedicalQAAgent(config=agent_config)
            executor = AgentExecutor(agent, config=agent_config)
            ctx = AgentContext(query="test", session_id="s1")
            response = executor.execute(ctx)
            assert response is not None

    def test_executor_cleanup_called(self, agent_config):
        with patch("app.agents.agents.medical_qa_agent.ChatService") as mock_chat_cls:
            mock_chat = MagicMock()
            mock_chat.ask.return_value = MagicMock(
                answer="Answer.", session_id="s1",
                citations=[], query_type="general", is_follow_up=False,
                confidence=MagicMock(overall=0.5), suggested_questions=[],
                processing_time_ms=10.0,
            )
            mock_chat_cls.return_value = mock_chat
            agent = MedicalQAAgent(config=agent_config)
            executor = AgentExecutor(agent, config=agent_config)
            ctx = AgentContext(query="test", session_id="s1")
            response = executor.execute(ctx)
            assert response.success


class TestMemoryPersistenceOnInvoke:
    def test_rag_invocation_persists_memory(self, agent_config):
        with patch("app.agents.agents.medical_qa_agent.ChatService") as mock_chat_cls:
            mock_chat = MagicMock()
            mock_chat.ask.return_value = MagicMock(
                answer="Lisinopril 10mg daily.",
                session_id="mem-persist-s1",
                citations=[], query_type="medication",
                is_follow_up=False,
                confidence=MagicMock(overall=0.85),
                suggested_questions=[], processing_time_ms=50.0,
            )
            mock_chat_cls.return_value = mock_chat
            agent = MedicalQAAgent(config=agent_config)
            agent.initialize()
            memory_service = MemoryService()
            agent._memory_service = memory_service
            ctx = AgentContext(query="What meds?", session_id="mem-persist-s1", patient_id="p1")
            agent.invoke_rag(ctx)
            entries = memory_service.recall("mem-persist-s1")
            assert len(entries) >= 1
            assert entries[0].content["query"] == "What meds?"

    def test_multiple_invocations_accumulate_memory(self, agent_config):
        with patch("app.agents.agents.medical_qa_agent.ChatService") as mock_chat_cls:
            mock_chat = MagicMock()
            mock_chat.ask.return_value = MagicMock(
                answer="Answer.", session_id="s1",
                citations=[], query_type="general",
                is_follow_up=False,
                confidence=MagicMock(overall=0.5),
                suggested_questions=[], processing_time_ms=10.0,
            )
            mock_chat_cls.return_value = mock_chat
            agent = MedicalQAAgent(config=agent_config)
            agent.initialize()
            memory_service = MemoryService()
            agent._memory_service = memory_service
            for i in range(3):
                ctx = AgentContext(query=f"Q{i}", session_id="multi-s1", patient_id="p1")
                agent.invoke_rag(ctx)
            entries = memory_service.recall("multi-s1")
            assert len(entries) >= 3


class TestAgentServicePipeline:
    def test_agent_service_run(self, agent_config):
        with patch("app.agents.agents.medical_qa_agent.ChatService") as mock_chat_cls, \
             patch("app.agents.agent_factory.get_global_registry"):
            mock_chat = MagicMock()
            mock_chat.ask.return_value = MagicMock(
                answer="You should take Lisinopril 10mg.",
                session_id="svc-test-s1",
                citations=[], query_type="medication",
                is_follow_up=False,
                confidence=MagicMock(overall=0.85),
                suggested_questions=[], processing_time_ms=50.0,
            )
            mock_chat_cls.return_value = mock_chat
            from app.agents.agent_registry import AgentRegistry
            registry = AgentRegistry()
            registry.register("medical_qa", MedicalQAAgent)
            service = AgentService(registry=registry)
            response = service.run(
                agent_type="medical_qa",
                query="What are my medications?",
                session_id="svc-test-s1",
                patient_id="p1",
                agent_config=agent_config,
            )
            assert response is not None
            assert response.success

    def test_agent_service_unknown_type(self):
        service = AgentService()
        with pytest.raises(Exception):
            service.run(
                agent_type="nonexistent",
                query="test",
                session_id="s1",
            )

    def test_agent_service_list_agents(self):
        service = AgentService()
        agents = service.list_agents()
        assert len(agents) >= 1
        assert "medical_qa" in agents


class TestAgentResponseValidation:
    def test_agent_response_ok(self):
        response = AgentResponse.ok(
            answer="Test answer",
            session_id="s1",
            citations=[],
        )
        assert response.success
        assert response.answer == "Test answer"
        assert response.session_id == "s1"

    def test_agent_response_error(self):
        response = AgentResponse.error(
            error="Something went wrong",
            session_id="s1",
        )
        assert not response.success
        assert "Something went wrong" in response.error

    def test_agent_response_defaults(self):
        response = AgentResponse.ok(answer="A", session_id="s1")
        assert response.trace_id is not None
        assert response.total_duration_ms >= 0

    def test_medical_qa_validate_empty_answer(self):
        agent = MedicalQAAgent()
        response = AgentResponse.ok(answer="", session_id="s1")
        with pytest.raises(Exception):
            agent.validate_response(response)
