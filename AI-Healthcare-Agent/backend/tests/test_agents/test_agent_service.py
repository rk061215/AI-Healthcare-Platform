from __future__ import annotations

import pytest

from app.agents.agent_service import AgentService
from app.agents.agent_registry import AgentRegistry
from app.agents.agent_response import AgentResponse
from app.agents.exceptions import AgentNotFoundError
from tests.test_agents.test_base_agent import SimpleTestAgent


class TestAgentService:
    def setup_method(self) -> None:
        self._registry = AgentRegistry()
        self._registry.register("simple", SimpleTestAgent)
        self._service = AgentService(registry=self._registry)

    def test_run_with_agent(self) -> None:
        agent = SimpleTestAgent()
        from app.agents.agent_context import AgentContext
        context = AgentContext(query="hello", session_id="s1")
        response = self._service.run_with_agent(agent, context)
        assert response.success is True
        assert "Answer for: hello" in response.answer

    def test_run_with_agent_failure(self) -> None:
        agent = SimpleTestAgent()
        from app.agents.agent_context import AgentContext
        context = AgentContext(query="fail", session_id="s1")
        response = self._service.run_with_agent(agent, context)
        assert response.success is False

    def test_list_agents(self) -> None:
        agents = self._service.list_agents()
        assert "simple" in agents
        assert len(agents) == 1
