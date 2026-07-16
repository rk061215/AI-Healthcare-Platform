from __future__ import annotations

import app.agents


class TestAgentsExports:
    def test_core_classes_exported(self) -> None:
        assert hasattr(app.agents, "BaseAgent")
        assert hasattr(app.agents, "AgentContext")
        assert hasattr(app.agents, "AgentState")
        assert hasattr(app.agents, "AgentPhase")
        assert hasattr(app.agents, "ExecutionStatus")
        assert hasattr(app.agents, "AgentResponse")
        assert hasattr(app.agents, "AgentConfig")
        assert hasattr(app.agents, "AgentRegistry")
        assert hasattr(app.agents, "get_global_registry")
        assert hasattr(app.agents, "AgentFactory")
        assert hasattr(app.agents, "AgentExecutor")
        assert hasattr(app.agents, "AgentService")
        assert hasattr(app.agents, "MedicalQAAgent")
        assert hasattr(app.agents, "AgentOrchestrator")

    def test_exceptions_exported(self) -> None:
        assert hasattr(app.agents, "AgentError")
        assert hasattr(app.agents, "AgentNotFoundError")
        assert hasattr(app.agents, "AgentRegistrationError")
        assert hasattr(app.agents, "AgentInitializationError")
        assert hasattr(app.agents, "AgentExecutionError")
        assert hasattr(app.agents, "AgentContextError")
        assert hasattr(app.agents, "AgentStateError")
        assert hasattr(app.agents, "AgentTimeoutError")
        assert hasattr(app.agents, "AgentValidationError")
        assert hasattr(app.agents, "AgentRetryExhaustedError")
        assert hasattr(app.agents, "AgentMemoryError")
        assert hasattr(app.agents, "AgentRAGError")
        assert hasattr(app.agents, "AgentToolError")
        assert hasattr(app.agents, "AgentResponseError")

    def test_all_exported(self) -> None:
        assert len(app.agents.__all__) > 20
