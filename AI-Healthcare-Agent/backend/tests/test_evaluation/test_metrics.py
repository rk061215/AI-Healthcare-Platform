from __future__ import annotations

import pytest

from app.evaluation.metrics import Metric, MetricRegistry, MetricResult, get_global_registry, register_metric


class TestMetricResult:
    def test_default_values(self) -> None:
        result = MetricResult(metric_name="test", score=0.5)
        assert result.metric_name == "test"
        assert result.score == 0.5
        assert result.category == "general"
        assert result.details == {}
        assert result.num_samples == 0
        assert result.passed is True
        assert result.error is None

    def test_custom_values(self) -> None:
        result = MetricResult(
            metric_name="custom",
            score=0.8,
            category="retrieval",
            details={"k": 5},
            num_samples=10,
            passed=False,
            error="something went wrong",
        )
        assert result.metric_name == "custom"
        assert result.score == 0.8
        assert result.category == "retrieval"
        assert result.details == {"k": 5}
        assert result.num_samples == 10
        assert result.passed is False
        assert result.error == "something went wrong"


class TestMetric:
    def test_metric_name_and_category(self) -> None:
        class TestMetric(Metric):
            def evaluate(self, **kwargs):
                return MetricResult(metric_name=self.name, score=0.0)

        metric = TestMetric(name="test_metric", category="test_category")
        assert metric.name == "test_metric"
        assert metric.category == "test_category"

    def test_metric_callable(self) -> None:
        class TestMetric(Metric):
            def evaluate(self, **kwargs):
                return MetricResult(metric_name=self.name, score=0.42)

        metric = TestMetric(name="callable_test")
        result = metric()
        assert result.score == 0.42
        assert result.metric_name == "callable_test"

    def test_metric_repr(self) -> None:
        class TestMetric(Metric):
            def evaluate(self, **kwargs):
                return MetricResult(metric_name=self.name, score=0.0)

        metric = TestMetric(name="repr_test", category="cat")
        assert "repr_test" in repr(metric)
        assert "cat" in repr(metric)

    def test_abstract_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            Metric(name="abstract")  # type: ignore


class TestMetricRegistry:
    def test_register_and_get(self) -> None:
        registry = MetricRegistry()
        class DummyMetric(Metric):
            def evaluate(self, **kwargs):
                return MetricResult(metric_name=self.name, score=1.0)
        metric = DummyMetric(name="dummy")
        registry.register(metric)
        assert registry.get("dummy") is metric

    def test_register_duplicate_raises(self) -> None:
        registry = MetricRegistry()
        class DummyMetric(Metric):
            def evaluate(self, **kwargs):
                return MetricResult(metric_name=self.name, score=1.0)
        metric = DummyMetric(name="dup")
        registry.register(metric)
        with pytest.raises(ValueError, match="already registered"):
            registry.register(DummyMetric(name="dup"))

    def test_unregister(self) -> None:
        registry = MetricRegistry()
        class DummyMetric(Metric):
            def evaluate(self, **kwargs):
                return MetricResult(metric_name=self.name, score=1.0)
        metric = DummyMetric(name="removable")
        registry.register(metric)
        registry.unregister("removable")
        assert registry.get("removable") is None

    def test_list_metrics(self) -> None:
        registry = MetricRegistry()
        class DummyMetric(Metric):
            def evaluate(self, **kwargs):
                return MetricResult(metric_name=self.name, score=1.0)
        registry.register(DummyMetric(name="a", category="cat1"))
        registry.register(DummyMetric(name="b", category="cat1"))
        registry.register(DummyMetric(name="c", category="cat2"))
        all_metrics = registry.list_metrics()
        assert len(all_metrics) == 3
        cat1_metrics = registry.list_metrics(category="cat1")
        assert len(cat1_metrics) == 2
        cat2_metrics = registry.list_metrics(category="cat2")
        assert len(cat2_metrics) == 1

    def test_clear(self) -> None:
        registry = MetricRegistry()
        class DummyMetric(Metric):
            def evaluate(self, **kwargs):
                return MetricResult(metric_name=self.name, score=1.0)
        registry.register(DummyMetric(name="x"))
        registry.clear()
        assert len(registry.list_metrics()) == 0

    def test_evaluate_all(self) -> None:
        registry = MetricRegistry()
        class DummyMetric(Metric):
            def evaluate(self, **kwargs):
                return MetricResult(metric_name=self.name, score=0.5)
        registry.register(DummyMetric(name="m1"))
        registry.register(DummyMetric(name="m2"))
        results = registry.evaluate_all()
        assert len(results) == 2
        for r in results:
            assert r.score == 0.5


class TestGlobalRegistry:
    def test_get_global_registry(self) -> None:
        registry = get_global_registry()
        assert isinstance(registry, MetricRegistry)

    def test_register_metric(self) -> None:
        class DummyMetric(Metric):
            def evaluate(self, **kwargs):
                return MetricResult(metric_name=self.name, score=1.0)
        metric = DummyMetric(name="global_test")
        register_metric(metric)
        registry = get_global_registry()
        assert registry.get("global_test") is metric
        registry.unregister("global_test")
