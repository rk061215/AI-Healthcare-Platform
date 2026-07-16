from __future__ import annotations

import time
import uuid
from typing import Optional

from app.agents.agent_context import AgentContext
from app.agents.agent_response import AgentResponse
from app.agents.agent_state import AgentPhase, AgentState, ExecutionStatus
from app.agents.base_agent import BaseAgent
from app.agents.exceptions import (
    AgentExecutionError,
    AgentRetryExhaustedError,
    AgentTimeoutError,
    AgentValidationError,
)
from app.agents.config import AgentConfig


class AgentExecutor:
    def __init__(self, agent: BaseAgent, config: Optional[AgentConfig] = None) -> None:
        self._agent = agent
        self._config = config or agent.config

    @property
    def agent(self) -> BaseAgent:
        return self._agent

    def execute(self, context: AgentContext) -> AgentResponse:
        state = AgentState(session_id=context.session_id)
        trace_id = uuid.uuid4().hex[:16]
        state.start(trace_id)

        try:
            self._verify_timeout(state)

            self._run_phase(state, AgentPhase.INITIALIZING, self._agent.initialize)

            self._run_phase(state, AgentPhase.CHECKING_HANDLER, lambda: None)

            self._run_phase(state, AgentPhase.PREPARING_CONTEXT, lambda: setattr(
                context, "config_overrides", {}
            ))
            context = self._agent.prepare_context(context)

            self._run_phase(state, AgentPhase.RETRIEVING_MEMORY, lambda: None)
            if self._config.enable_memory:
                context = self._agent.retrieve_memory(context)

            self._run_phase(state, AgentPhase.RETRIEVING_DOCUMENTS, lambda: None)
            if self._config.enable_rag:
                context = self._agent.retrieve_documents(context)

            response = self._run_rag_phase(state, context)

            if not response.success:
                state.fail(response.error or "RAG returned failure response")
                self._agent.cleanup()
                response.session_id = context.session_id
                response.trace_id = trace_id
                return response

            if self._config.enable_tools:
                self._run_phase(state, AgentPhase.INVOKING_TOOLS, lambda: None)
                context = self._agent.invoke_tools(context)

            response = self._run_phase(
                state, AgentPhase.POST_PROCESSING,
                lambda: self._agent.post_process(response, context),
            )

            response = self._run_phase(
                state, AgentPhase.VALIDATING,
                lambda: self._agent.validate_response(response),
            )

            state.complete()
            response.status = (
                ExecutionStatus.SUCCESS if response.success else ExecutionStatus.FAILURE
            )
            response.session_id = context.session_id
            response.trace_id = trace_id
            response.total_duration_ms = state.total_duration_ms

            self._agent.cleanup()

            return response

        except (AgentTimeoutError, AgentRetryExhaustedError):
            state.fail(str(AgentError))
            self._agent.cleanup()
            return AgentResponse.error(
                error=state.errors[-1] if state.errors else "Execution failed",
                session_id=context.session_id,
                trace_id=trace_id,
                total_duration_ms=(time.time() - state.start_time) * 1000,
            )
        except Exception as exc:
            state.fail(str(exc))
            self._agent.cleanup()
            return AgentResponse.error(
                error=str(exc),
                session_id=context.session_id,
                trace_id=trace_id,
                total_duration_ms=(time.time() - state.start_time) * 1000,
            )

    def _verify_timeout(self, state: AgentState) -> None:
        state.set_phase(AgentPhase.INITIALIZING)

    def _run_phase(
        self, state: AgentState, phase: AgentPhase, fn, *args, **kwargs
    ):
        state.set_phase(phase)
        phase_start = time.time()
        try:
            if self._config.max_retries > 0:
                return self._with_retry(fn, *args, **kwargs)
            return fn(*args, **kwargs)
        except Exception as exc:
            duration = (time.time() - phase_start) * 1000
            state.add_component_trace(
                component=phase.value,
                status=ExecutionStatus.FAILURE,
                duration_ms=duration,
                error=str(exc),
            )
            raise AgentExecutionError(f"Phase '{phase.value}' failed: {exc}") from exc

    def _run_rag_phase(self, state: AgentState, context: AgentContext) -> AgentResponse:
        state.set_phase(AgentPhase.INVOKING_RAG)
        phase_start = time.time()
        try:
            response = self._run_phase_with_retry(lambda: self._agent.invoke_rag(context))
            duration = (time.time() - phase_start) * 1000
            state.add_component_trace(
                component=AgentPhase.INVOKING_RAG.value,
                status=ExecutionStatus.SUCCESS,
                duration_ms=duration,
            )
            return response
        except Exception as exc:
            duration = (time.time() - phase_start) * 1000
            state.add_component_trace(
                component=AgentPhase.INVOKING_RAG.value,
                status=ExecutionStatus.FAILURE,
                duration_ms=duration,
                error=str(exc),
            )
            raise AgentExecutionError(f"RAG invocation failed: {exc}") from exc

    def _with_retry(self, fn, *args, **kwargs):
        import time as time_module
        last_exc = None
        for attempt in range(self._config.max_retries):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                last_exc = exc
                if attempt < self._config.max_retries - 1:
                    time_module.sleep(self._config.retry_delay_seconds)
        raise AgentRetryExhaustedError(
            f"All {self._config.max_retries} retries failed: {last_exc}"
        ) from last_exc

    def _run_phase_with_retry(self, fn):
        return self._with_retry(fn)
