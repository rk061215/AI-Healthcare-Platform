from __future__ import annotations

from typing import Optional

import pytest

from app.agents.agent_context import AgentContext
from app.agents.agent_response import AgentResponse
from app.agents.base_agent import BaseAgent
from app.agents.config import AgentConfig


class SimpleTestAgent(BaseAgent):
    def __init__(self, config: Optional[AgentConfig] = None) -> None:
        super().__init__(config=config)
        self.initialized = False
        self.cleaned_up = False

    def initialize(self) -> None:
        self.initialized = True

    def can_handle(self, context: AgentContext) -> bool:
        return bool(context.query)

    def prepare_context(self, context: AgentContext) -> AgentContext:
        return context

    def retrieve_memory(self, context: AgentContext) -> AgentContext:
        return context

    def retrieve_documents(self, context: AgentContext) -> AgentContext:
        return context

    def invoke_rag(self, context: AgentContext) -> AgentResponse:
        if context.query == "fail":
            return AgentResponse.error("Intentional failure", session_id=context.session_id)
        return AgentResponse.ok(answer=f"Answer for: {context.query}", session_id=context.session_id)

    def post_process(self, response: AgentResponse, context: AgentContext) -> AgentResponse:
        return response

    def validate_response(self, response: AgentResponse) -> AgentResponse:
        return response

    def cleanup(self) -> None:
        self.cleaned_up = True


class TestBaseAgent:
    def test_default_config(self) -> None:
        agent = SimpleTestAgent()
        assert agent.config.agent_type == "base"

    def test_custom_config(self) -> None:
        config = AgentConfig(agent_type="test", max_retries=5)
        agent = SimpleTestAgent(config=config)
        assert agent.config.max_retries == 5

    def test_config_property(self) -> None:
        agent = SimpleTestAgent()
        assert isinstance(agent.config, AgentConfig)

    def test_initialize_called_when_config_matches(self) -> None:
        agent = SimpleTestAgent()
        agent.initialize()
        assert agent.initialized

    def test_cleanup_called(self) -> None:
        agent = SimpleTestAgent()
        agent.cleanup()
        assert agent.cleaned_up

    def test_can_handle_with_query(self) -> None:
        agent = SimpleTestAgent()
        context = AgentContext(query="hello", session_id="s1")
        assert agent.can_handle(context) is True

    def test_can_handle_without_query(self) -> None:
        agent = SimpleTestAgent()
        context = AgentContext(query="", session_id="s1")
        assert agent.can_handle(context) is False

    def test_invoke_rag_success(self) -> None:
        agent = SimpleTestAgent()
        context = AgentContext(query="test", session_id="s1")
        response = agent.invoke_rag(context)
        assert response.success is True
        assert "Answer for: test" in response.answer

    def test_invoke_rag_failure(self) -> None:
        agent = SimpleTestAgent()
        context = AgentContext(query="fail", session_id="s1")
        response = agent.invoke_rag(context)
        assert response.success is False

    def test_validate_passes_good_response(self) -> None:
        agent = SimpleTestAgent()
        response = AgentResponse.ok(answer="good answer", session_id="s1")
        result = agent.validate_response(response)
        assert result.success is True

    def test_abstract_class_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            BaseAgent()  # type: ignore

    def test_invoke_tools_default_noop(self) -> None:
        agent = SimpleTestAgent()
        context = AgentContext(query="test", session_id="s1")
        result = agent.invoke_tools(context)
        assert result is context
