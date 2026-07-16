from __future__ import annotations

import pytest

from app.agents.agent_registry import AgentRegistry, get_global_registry
from app.agents.base_agent import BaseAgent
from app.agents.exceptions import AgentNotFoundError, AgentRegistrationError
from tests.test_agents.test_base_agent import SimpleTestAgent


class TestAgentRegistry:
    def test_register_and_get(self) -> None:
        registry = AgentRegistry()
        registry.register("test", SimpleTestAgent)
        assert registry.get("test") is SimpleTestAgent

    def test_register_duplicate_raises(self) -> None:
        registry = AgentRegistry()
        registry.register("dup", SimpleTestAgent)
        with pytest.raises(AgentRegistrationError):
            registry.register("dup", SimpleTestAgent)

    def test_get_not_found(self) -> None:
        registry = AgentRegistry()
        with pytest.raises(AgentNotFoundError):
            registry.get("nonexistent")

    def test_unregister(self) -> None:
        registry = AgentRegistry()
        registry.register("tmp", SimpleTestAgent)
        registry.unregister("tmp")
        assert "tmp" not in registry.list_agents()

    def test_list_agents(self) -> None:
        registry = AgentRegistry()
        registry.register("a", SimpleTestAgent)
        registry.register("b", SimpleTestAgent)
        agents = registry.list_agents()
        assert "a" in agents
        assert "b" in agents
        assert len(agents) == 2

    def test_clear(self) -> None:
        registry = AgentRegistry()
        registry.register("x", SimpleTestAgent)
        registry.clear()
        assert registry.list_agents() == []

    def test_global_registry(self) -> None:
        registry = get_global_registry()
        assert isinstance(registry, AgentRegistry)
        assert "medical_qa" in registry.list_agents()
