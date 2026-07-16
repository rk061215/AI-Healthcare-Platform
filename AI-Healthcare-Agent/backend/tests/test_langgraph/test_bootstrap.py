from __future__ import annotations

from unittest.mock import patch

from app.langgraph.bootstrap import GraphBootstrap, get_bootstrap_result, set_bootstrap_result


class TestGraphBootstrap:
    def test_register_graphs(self):
        result = GraphBootstrap.register_graphs()
        assert result.graph_registered is True
        assert result.graph_name == "medical_qa"
        assert "registry_graphs" in result.diagnostics

    def test_validate_dependencies_runs_without_crash(self):
        result = GraphBootstrap.validate_dependencies()
        assert result.diagnostics is not None
        assert isinstance(result.validation_errors, list)
        assert "ai_provider" in result.diagnostics
        assert "rag_engine" in result.diagnostics
        assert "memory_service" in result.diagnostics
        assert "tool_service" in result.diagnostics
        assert "medical_qa_agent" in result.diagnostics

    def test_full_bootstrap_registers_graph(self):
        result = GraphBootstrap.run_full_bootstrap()
        assert result.graph_registered is True
        assert isinstance(result.validation_errors, list)
        assert "registry_graphs" in result.diagnostics

    def test_set_and_get_bootstrap_result(self):
        result = GraphBootstrap.register_graphs()
        set_bootstrap_result(result)
        retrieved = get_bootstrap_result()
        assert retrieved is result
        assert retrieved.graph_name == "medical_qa"

    def test_bootstrap_result_dataclass(self):
        from app.langgraph.bootstrap import GraphBootstrapResult
        r = GraphBootstrapResult(
            graph_registered=True,
            graph_name="test",
            dependencies_validated=True,
            success=True,
        )
        assert r.graph_name == "test"
        assert r.success is True
