from __future__ import annotations

import json
import time
from typing import Any, Optional

from app.agents.agent_context import AgentContext
from app.agents.agent_response import AgentResponse
from app.agents.agent_state import AgentPhase, AgentState, ExecutionStatus
from app.agents.base_agent import BaseAgent
from app.agents.config import AgentConfig
from app.ai.config import AIProviderConfig
from app.ai.provider_factory import AIProviderFactory
from app.tools.tool_registry import get_global_registry

PLANNER_SYSTEM_PROMPT = """You are a medical task planner. Given a user query, create a step-by-step plan
to answer the query using available tools and retrieval.

Available tools:
{tools_list}

Return a JSON plan:
{
  "plan": [
    {
      "step": 1,
      "action": "retrieve|reason|tool_call|respond",
      "description": "what to do",
      "tool_name": "tool name if action is tool_call, else null",
      "tool_action": "specific action if tool_call, else null",
      "depends_on": [list of step numbers this depends on]
    }
  ],
  "reasoning": "why this plan was chosen"
}"""


class PlannerAgent(BaseAgent):
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        provider_factory: Optional[AIProviderFactory] = None,
    ):
        super().__init__(config)
        self._provider_factory = provider_factory
        self._llm = None

    def initialize(self) -> None:
        if self._llm is None:
            ai_config = AIProviderConfig(
                provider=self._config.ai_provider or "gemini",
                model=self._config.ai_model or "gemini-2.0-flash",
                temperature=0.2,
                max_tokens=1024,
            )
            if self._provider_factory:
                self._llm = self._provider_factory.create(ai_config)
            else:
                self._llm = AIProviderFactory.create(ai_config)

    def can_handle(self, context: AgentContext) -> bool:
        return bool(context.query and context.query.strip())

    def prepare_context(self, context: AgentContext) -> AgentContext:
        return context

    def retrieve_memory(self, context: AgentContext) -> AgentContext:
        return context

    def retrieve_documents(self, context: AgentContext) -> AgentContext:
        return context

    def invoke_rag(self, context: AgentContext) -> AgentResponse:
        start = time.perf_counter()

        try:
            self.initialize()
            plan = self._create_plan(context.query)
            elapsed = (time.perf_counter() - start) * 1000
            return AgentResponse.ok(
                answer=json.dumps(plan, indent=2),
                data={"plan": plan},
                session_id=context.session_id,
                total_duration_ms=round(elapsed, 2),
                metadata={"agent": "planner", "steps": len(plan)},
            )
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            return AgentResponse.error(
                error=f"Planning failed: {exc}",
                session_id=context.session_id,
                total_duration_ms=round(elapsed, 2),
            )

    def post_process(self, response: AgentResponse, context: AgentContext) -> AgentResponse:
        return response

    def validate_response(self, response: AgentResponse) -> AgentResponse:
        return response

    def cleanup(self) -> None:
        self._llm = None

    def _create_plan(self, query: str) -> list[dict[str, Any]]:
        registry = get_global_registry()
        all_tools = registry.list_tools()
        tools_list = "\n".join(
            f"- {name}: {cls.__doc__ or 'No description'}"
            for name, cls in all_tools.items()
        )

        prompt = f"User query: {query}\n\nCreate a step-by-step plan."

        try:
            result = self._llm.generate_structured_output(
                prompt=prompt,
                output_schema={
                    "type": "object",
                    "properties": {
                        "plan": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "step": {"type": "integer"},
                                    "action": {"type": "string", "enum": ["retrieve", "reason", "tool_call", "respond"]},
                                    "description": {"type": "string"},
                                    "tool_name": {"type": "string"},
                                    "tool_action": {"type": "string"},
                                    "depends_on": {"type": "array", "items": {"type": "integer"}},
                                },
                            },
                        },
                        "reasoning": {"type": "string"},
                    },
                    "required": ["plan", "reasoning"],
                },
                system_prompt=PLANNER_SYSTEM_PROMPT.format(tools_list=tools_list),
            )
            return result.get("plan", [])
        except Exception:
            return self._fallback_plan(query)

    def _fallback_plan(self, query: str) -> list[dict[str, Any]]:
        return [
            {"step": 1, "action": "retrieve", "description": "Retrieve relevant medical documents", "tool_name": None, "tool_action": None, "depends_on": []},
            {"step": 2, "action": "reason", "description": f"Analyze query: {query[:100]}", "tool_name": None, "tool_action": None, "depends_on": [1]},
            {"step": 3, "action": "respond", "description": "Generate final answer", "tool_name": None, "tool_action": None, "depends_on": [2]},
        ]
