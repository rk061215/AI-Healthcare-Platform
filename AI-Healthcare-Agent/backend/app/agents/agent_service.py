from __future__ import annotations

from typing import Any, Optional

from app.agents.agent_context import AgentContext
from app.agents.agent_executor import AgentExecutor
from app.agents.agent_factory import AgentFactory
from app.agents.agent_registry import get_global_registry
from app.agents.agent_response import AgentResponse
from app.agents.base_agent import BaseAgent
from app.agents.config import AgentConfig
from app.agents.exceptions import AgentNotFoundError


class AgentService:
    def __init__(self, registry=None) -> None:
        self._registry = registry or get_global_registry()

    def run(
        self,
        agent_type: str,
        query: str,
        session_id: str,
        patient_id: str = "",
        document_id: Optional[str] = None,
        report_id: Optional[str] = None,
        document_type: Optional[str] = None,
        document_sections: Optional[list[str]] = None,
        config_overrides: Optional[dict[str, Any]] = None,
        agent_config: Optional[AgentConfig] = None,
    ) -> AgentResponse:
        agent = AgentFactory.create(agent_type, config=agent_config)

        context = AgentContext(
            query=query,
            session_id=session_id,
            patient_id=patient_id,
            document_id=document_id,
            report_id=report_id,
            document_type=document_type,
            document_sections=document_sections or [],
            config_overrides=config_overrides or {},
        )

        executor = AgentExecutor(agent, config=agent_config or agent.config)
        return executor.execute(context)

    def run_with_agent(
        self, agent: BaseAgent, context: AgentContext,
    ) -> AgentResponse:
        executor = AgentExecutor(agent, config=agent.config)
        return executor.execute(context)

    def list_agents(self) -> list[str]:
        return self._registry.list_agents()
