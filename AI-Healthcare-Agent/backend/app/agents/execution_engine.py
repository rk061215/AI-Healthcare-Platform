from __future__ import annotations

import json
import time
import uuid
from typing import Any, Optional

from app.agents.agent_context import AgentContext
from app.agents.agent_response import AgentResponse
from app.agents.agent_state import AgentPhase, AgentState, ExecutionStatus
from app.agents.agents.planner_agent import PlannerAgent
from app.ai.config import AIProviderConfig
from app.ai.provider_factory import AIProviderFactory
from app.rag.citation_engine import CitationEngine
from app.rag.confidence_engine import ConfidenceEngine
from app.rag.models import RAGRequest
from app.rag.rag_engine import RAGEngine
from app.tools.tool_executor import ToolExecutor
from app.tools.tool_registry import get_global_registry


class ExecutionEngine:
    def __init__(
        self,
        rag_engine: Optional[RAGEngine] = None,
        planner_agent: Optional[PlannerAgent] = None,
        tool_executor: Optional[ToolExecutor] = None,
        citation_engine: Optional[CitationEngine] = None,
        confidence_engine: Optional[ConfidenceEngine] = None,
        provider_factory: Optional[AIProviderFactory] = None,
    ):
        self._rag = rag_engine or RAGEngine()
        self._planner = planner_agent or PlannerAgent(
            provider_factory=provider_factory
        )
        self._tool_executor = tool_executor or ToolExecutor()
        self._citation_engine = citation_engine or CitationEngine()
        self._confidence_engine = confidence_engine or ConfidenceEngine()
        self._provider_factory = provider_factory
        self._llm = None

    def _lazy_init_llm(self) -> None:
        if self._llm is not None:
            return
        config = AIProviderConfig(
            provider="gemini",
            model="gemini-2.0-flash",
            temperature=0.3,
            max_tokens=2048,
        )
        if self._provider_factory:
            self._llm = self._provider_factory.create(config)
        else:
            self._llm = AIProviderFactory.create(config)

    def execute(
        self, query: str, patient_id: Optional[str] = None, session_id: Optional[str] = None
    ) -> AgentResponse:
        start = time.perf_counter()
        sid = session_id or str(uuid.uuid4())
        state = AgentState(session_id=sid)
        state.start(str(uuid.uuid4()))

        try:
            self._lazy_init_llm()
            self._planner.initialize()

            context = AgentContext(
                query=query,
                session_id=sid,
                patient_id=patient_id or "",
            )

            plan_response = self._planner.invoke_rag(context)
            if not plan_response.success:
                return self._execute_fallback(query, context, start, sid)

            plan = plan_response.data.get("plan", [])
            if not plan:
                return self._execute_fallback(query, context, start, sid)

            completed: dict[int, Any] = {}

            for step in plan:
                step_num = step.get("step", 0)
                action = step.get("action", "")
                description = step.get("description", "")
                tool_name = step.get("tool_name")
                tool_action = step.get("tool_action")

                state.set_phase(AgentPhase.INVOKING_TOOLS if action == "tool_call" else AgentPhase.INVOKING_RAG)

                if action == "retrieve":
                    rag_response = self._rag.answer(query=RAGRequest(
                        query=description or query,
                        patient_id=patient_id,
                    ))
                    completed[step_num] = {"type": "retrieval", "result": rag_response}

                elif action == "tool_call" and tool_name:
                    tool_result = self._tool_executor.execute(
                        tool_name=tool_name,
                        action=tool_action or "",
                        context={"query": query, "patient_id": patient_id},
                    )
                    completed[step_num] = {"type": "tool", "result": tool_result}

                elif action == "reason":
                    reasoning = self._execute_reasoning_step(step, completed, query)
                    completed[step_num] = {"type": "reasoning", "result": reasoning}

                elif action == "respond":
                    final = self._generate_final_answer(query, completed, step)
                    elapsed = (time.perf_counter() - start) * 1000
                    state.complete()
                    return AgentResponse.ok(
                        answer=final.get("answer", ""),
                        data={"plan": plan, "step_results": completed},
                        session_id=sid,
                        total_duration_ms=round(elapsed, 2),
                        citations=final.get("citations", []),
                        metadata={"confidence": final.get("confidence", 0.0)},
                    )

            return self._execute_fallback(query, context, start, sid)

        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            state.fail(str(exc))
            return AgentResponse.error(
                error=f"Execution failed: {exc}",
                session_id=sid,
                total_duration_ms=round(elapsed, 2),
            )

    def _execute_fallback(
        self, query: str, context: AgentContext, start: float, sid: str
    ) -> AgentResponse:
        try:
            rag_response = self._rag.answer(query=RAGRequest(
                query=query,
                patient_id=context.patient_id,
            ))
            elapsed = (time.perf_counter() - start) * 1000
            return AgentResponse.ok(
                answer=rag_response.answer,
                session_id=sid,
                total_duration_ms=round(elapsed, 2),
            )
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            return AgentResponse.error(
                error=str(exc),
                session_id=sid,
                total_duration_ms=round(elapsed, 2),
            )

    def _execute_reasoning_step(
        self, step: dict[str, Any], completed: dict[int, Any], query: str
    ) -> str:
        context_parts = [f"Query: {query}"]
        for dep in step.get("depends_on", []):
            if dep in completed:
                dep_result = completed[dep]["result"]
                if hasattr(dep_result, "answer"):
                    context_parts.append(f"Step {dep}: {dep_result.answer[:500]}")
                else:
                    context_parts.append(f"Step {dep}: {str(dep_result)[:500]}")

        prompt = "\n".join(context_parts)
        prompt += f"\n\nStep {step['step']}: {step.get('description', 'Analyze')}"
        return self._llm.generate_text(prompt)

    def _generate_final_answer(
        self, query: str, completed: dict[int, Any], step: dict[str, Any]
    ) -> dict[str, Any]:
        context_parts = [f"Query: {query}"]
        for dep in step.get("depends_on", []):
            if dep in completed:
                dep_result = completed[dep]["result"]
                if hasattr(dep_result, "answer"):
                    context_parts.append(f"Step {dep}: {dep_result.answer}")
                else:
                    context_parts.append(f"Step {dep}: {str(dep_result)}")

        prompt = "\n".join(context_parts) + "\n\nGenerate a comprehensive medical answer."
        answer = self._llm.generate_text(prompt)

        return {"answer": answer, "citations": [], "confidence": 0.7}
