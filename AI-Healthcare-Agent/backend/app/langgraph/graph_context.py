from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from app.agents.agent_executor import AgentExecutor
from app.agents.agents.medical_qa_agent import MedicalQAAgent
from app.langgraph.config import LangGraphConfig
from app.langgraph.graph_state import GraphState
from app.memory.memory_service import MemoryService
from app.tools.tool_service import ToolService


@dataclass
class GraphContext:
    config: LangGraphConfig
    state: GraphState
    memory_service: Optional[MemoryService] = None
    medical_qa_agent: Optional[MedicalQAAgent] = None
    agent_executor: Optional[AgentExecutor] = None
    tool_service: Optional[ToolService] = None
    rag_engine: Any = None
    context_builder: Any = None
    retriever_service: Any = None
    ai_provider: Any = None
    session_manager: Any = None
    logger: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_memory(self) -> MemoryService:
        if self.memory_service is None:
            from app.memory.config import MemoryConfig
            self.memory_service = MemoryService(
                config=MemoryConfig(provider="in_memory"),
            )
        return self.memory_service

    def get_agent(self) -> MedicalQAAgent:
        if self.medical_qa_agent is None:
            self.medical_qa_agent = MedicalQAAgent()
            self.medical_qa_agent.initialize()
        return self.medical_qa_agent

    def get_agent_executor(self) -> AgentExecutor:
        if self.agent_executor is None:
            agent = self.get_agent()
            self.agent_executor = AgentExecutor(agent=agent)
        return self.agent_executor

    def get_tool_service(self) -> ToolService:
        if self.tool_service is None:
            self.tool_service = ToolService()
        return self.tool_service

    def populate_services(self, state: GraphState) -> None:
        if self.memory_service is not None:
            state.services["memory_service"] = self.memory_service
        if self.agent_executor is not None:
            state.services["agent_executor"] = self.agent_executor
        if self.tool_service is not None:
            state.services["tool_service"] = self.tool_service
        if self.rag_engine is not None:
            state.services["rag_engine"] = self.rag_engine
        if self.context_builder is not None:
            state.services["context_builder"] = self.context_builder
        if self.retriever_service is not None:
            state.services["retriever_service"] = self.retriever_service
        if self.ai_provider is not None:
            state.services["ai_provider"] = self.ai_provider
        if self.session_manager is not None:
            state.services["session_manager"] = self.session_manager
