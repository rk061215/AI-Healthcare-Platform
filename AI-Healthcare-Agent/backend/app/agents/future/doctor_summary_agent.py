from __future__ import annotations

from typing import Optional

from app.agents.agent_context import AgentContext
from app.agents.agent_response import AgentResponse
from app.agents.base_agent import BaseAgent
from app.agents.config import AgentConfig


class DoctorSummaryAgent(BaseAgent):
    def __init__(self, config: Optional[AgentConfig] = None) -> None:
        super().__init__(config=config or AgentConfig(agent_type="doctor_summary"))

    def initialize(self) -> None:
        pass

    def can_handle(self, context: AgentContext) -> bool:
        return False

    def prepare_context(self, context: AgentContext) -> AgentContext:
        return context

    def retrieve_memory(self, context: AgentContext) -> AgentContext:
        return context

    def retrieve_documents(self, context: AgentContext) -> AgentContext:
        return context

    def invoke_rag(self, context: AgentContext) -> AgentResponse:
        return AgentResponse.error("DoctorSummaryAgent not yet implemented", session_id=context.session_id)

    def post_process(self, response: AgentResponse, context: AgentContext) -> AgentResponse:
        return response

    def validate_response(self, response: AgentResponse) -> AgentResponse:
        return response

    def cleanup(self) -> None:
        pass
