from __future__ import annotations

from typing import Optional

from app.agents.agent_registry import get_global_registry
from app.agents.base_agent import BaseAgent
from app.agents.config import AgentConfig
from app.agents.exceptions import AgentNotFoundError


class AgentFactory:
    @staticmethod
    def create(agent_type: str, config: Optional[AgentConfig] = None) -> BaseAgent:
        registry = get_global_registry()
        agent_class = registry.get(agent_type)
        return agent_class(config=config)

    @staticmethod
    def create_or_none(agent_type: str, config: Optional[AgentConfig] = None) -> Optional[BaseAgent]:
        try:
            return AgentFactory.create(agent_type, config=config)
        except AgentNotFoundError:
            return None
