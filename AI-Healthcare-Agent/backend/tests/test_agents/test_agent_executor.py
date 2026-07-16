from __future__ import annotations

from typing import Optional

import pytest

from app.agents.agent_context import AgentContext
from app.agents.agent_executor import AgentExecutor
from app.agents.agent_response import AgentResponse
from app.agents.agent_state import ExecutionStatus
from app.agents.base_agent import BaseAgent
from app.agents.config import AgentConfig
from app.agents.exceptions import (
    AgentExecutionError,
    AgentRetryExhaustedError,
    AgentTimeoutError,
    AgentValidationError,
)


class LifecycleTrackingAgent(BaseAgent):
    def __init__(self, config: Optional[AgentConfig] = None) -> None:
        super().__init__(config=config)
        self.lifecycle: list[str] = []
        self.should_fail_rag = False

    def initialize(self) -> None:
        self.lifecycle.append("initialize")

    def can_handle(self, context: AgentContext) -> bool:
        self.lifecycle.append("can_handle")
        return True

    def prepare_context(self, context: AgentContext) -> AgentContext:
        self.lifecycle.append("prepare_context")
        return context

    def retrieve_memory(self, context: AgentContext) -> AgentContext:
        self.lifecycle.append("retrieve_memory")
        return context

    def retrieve_documents(self, context: AgentContext) -> AgentContext:
        self.lifecycle.append("retrieve_documents")
        return context

    def invoke_rag(self, context: AgentContext) -> AgentResponse:
        self.lifecycle.append("invoke_rag")
        if self.should_fail_rag:
            raise ValueError("RAG failed")
        return AgentResponse.ok(answer=f"Answer: {context.query}", session_id=context.session_id)

    def invoke_tools(self, context: AgentContext) -> AgentContext:
        self.lifecycle.append("invoke_tools")
        return context

    def post_process(self, response: AgentResponse, context: AgentContext) -> AgentResponse:
        self.lifecycle.append("post_process")
        return response

    def validate_response(self, response: AgentResponse) -> AgentResponse:
        self.lifecycle.append("validate_response")
        return response

    def cleanup(self) -> None:
        self.lifecycle.append("cleanup")


class TestAgentExecutor:
    def test_execute_full_lifecycle(self) -> None:
        config = AgentConfig(enable_memory=True, enable_rag=True, enable_tools=True)
        agent = LifecycleTrackingAgent(config=config)
        executor = AgentExecutor(agent, config=config)
        context = AgentContext(query="test", session_id="s1")
        response = executor.execute(context)
        assert response.success is True
        assert "initialize" in agent.lifecycle
        assert "prepare_context" in agent.lifecycle
        assert "retrieve_memory" in agent.lifecycle
        assert "retrieve_documents" in agent.lifecycle
        assert "invoke_rag" in agent.lifecycle
        assert "invoke_tools" in agent.lifecycle
        assert "post_process" in agent.lifecycle
        assert "validate_response" in agent.lifecycle
        assert "cleanup" in agent.lifecycle

    def test_execute_without_tools(self) -> None:
        config = AgentConfig(enable_tools=False)
        agent = LifecycleTrackingAgent(config=config)
        executor = AgentExecutor(agent, config=config)
        context = AgentContext(query="test", session_id="s1")
        executor.execute(context)
        assert "invoke_tools" not in agent.lifecycle

    def test_execute_without_memory(self) -> None:
        config = AgentConfig(enable_memory=False)
        agent = LifecycleTrackingAgent(config=config)
        executor = AgentExecutor(agent, config=config)
        context = AgentContext(query="test", session_id="s1")
        executor.execute(context)
        assert "retrieve_memory" not in agent.lifecycle

    def test_execute_rag_failure(self) -> None:
        config = AgentConfig(max_retries=1)
        agent = LifecycleTrackingAgent(config=config)
        agent.should_fail_rag = True
        executor = AgentExecutor(agent, config=config)
        context = AgentContext(query="test", session_id="s1")
        response = executor.execute(context)
        assert response.success is False
        assert "RAG failed" in response.error

    def test_execute_retry_on_failure(self) -> None:
        config = AgentConfig(max_retries=3, retry_delay_seconds=0.01)
        agent = LifecycleTrackingAgent(config=config)
        agent.should_fail_rag = True
        executor = AgentExecutor(agent, config=config)
        context = AgentContext(query="test", session_id="s1")
        response = executor.execute(context)
        assert response.success is False

    def test_executor_property(self) -> None:
        agent = LifecycleTrackingAgent()
        executor = AgentExecutor(agent)
        assert executor.agent is agent
