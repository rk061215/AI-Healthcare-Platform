from __future__ import annotations

from app.evaluation.config import EvaluationConfig


class TestEvaluationConfig:
    def test_default_config(self) -> None:
        config = EvaluationConfig()
        assert config.provider == "gemini"
        assert config.model == "gemini-2.0-flash"
        assert config.temperature == 0.3
        assert config.top_k == 10
        assert config.min_score == 0.0
        assert config.k_values == (1, 3, 5, 10)
        assert config.retrieval_metrics_enabled is True
        assert config.rag_metrics_enabled is True
        assert config.hallucination_metrics_enabled is True
        assert config.citation_metrics_enabled is True
        assert config.performance_metrics_enabled is True
        assert config.token_usage_metrics_enabled is True
        assert config.medical_qa_metrics_enabled is True
        assert config.dataset_path == "datasets"
        assert config.output_path == "evaluation_reports"
        assert config.benchmark_name == "default_benchmark"
        assert config.num_runs == 1

    def test_custom_config(self) -> None:
        config = EvaluationConfig(
            provider="openai",
            model="gpt-4",
            top_k=20,
            k_values=(5, 10),
            retrieval_metrics_enabled=False,
            benchmark_name="custom_benchmark",
        )
        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.top_k == 20
        assert config.k_values == (5, 10)
        assert config.retrieval_metrics_enabled is False
        assert config.benchmark_name == "custom_benchmark"

    def test_model_default_empty(self) -> None:
        config = EvaluationConfig(model="")
        assert config.model == "gemini-2.0-flash"

    def test_model_default_custom(self) -> None:
        config = EvaluationConfig(model="gemini-1.5-pro")
        assert config.model == "gemini-1.5-pro"
