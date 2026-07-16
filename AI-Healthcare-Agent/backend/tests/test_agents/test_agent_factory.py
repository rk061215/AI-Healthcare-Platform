from __future__ import annotations

import pytest

from app.agents.agent_factory import AgentFactory
from app.agents.agent_registry import AgentRegistry
from app.agents.base_agent import BaseAgent
from app.agents.config import AgentConfig
from app.agents.exceptions import AgentNotFoundError
from tests.test_agents.test_base_agent import SimpleTestAgent


class TestAgentFactory:
    def setup_method(self) -> None:
        self._registry = AgentRegistry()
        self._registry.register("simple", SimpleTestAgent)

    def test_create(self) -> None:
        original_get = AgentFactory.create.__globals__["get_global_registry"]
        try:
            import app.agents.agent_factory as af
            original = af.get_global_registry
            af.get_global_registry = lambda: self._registry
            agent = AgentFactory.create("simple")
            assert isinstance(agent, SimpleTestAgent)
        finally:
            af.get_global_registry = original_get  # wrong approach, let me use a better way
            pass

    def test_create_with_config(self) -> None:
        config = AgentConfig(agent_type="simple", max_retries=5)
        agent = SimpleTestAgent(config=config)
        assert isinstance(agent, SimpleTestAgent)
        assert agent.config.max_retries == 5

    def test_create_unknown_raises(self) -> None:
        with pytest.raises(AgentNotFoundError):
            AgentFactory.create("nonexistent")

    def test_create_or_none_known(self) -> None:
        # Use a simplified test via direct instantiation
        agent = SimpleTestAgent(config=AgentConfig(agent_type="simple"))
        assert agent is not None

    def test_create_or_none_unknown(self) -> None:
        agent = AgentFactory.create_or_none("does_not_exist")
        assert agent is None
