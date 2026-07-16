from __future__ import annotations

from typing import Optional, Type

from app.agents.base_agent import BaseAgent
from app.agents.exceptions import AgentNotFoundError, AgentRegistrationError


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, type[BaseAgent]] = {}

    def register(self, name: str, agent_class: type[BaseAgent]) -> None:
        if name in self._agents:
            raise AgentRegistrationError(f"Agent '{name}' is already registered")
        self._agents[name] = agent_class

    def unregister(self, name: str) -> None:
        self._agents.pop(name, None)

    def get(self, name: str) -> type[BaseAgent]:
        agent = self._agents.get(name)
        if agent is None:
            raise AgentNotFoundError(f"Agent '{name}' is not registered")
        return agent

    def list_agents(self) -> list[str]:
        return list(self._agents.keys())

    def clear(self) -> None:
        self._agents.clear()


_global_registry: Optional[AgentRegistry] = None


def get_global_registry() -> AgentRegistry:
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentRegistry()
    return _global_registry
