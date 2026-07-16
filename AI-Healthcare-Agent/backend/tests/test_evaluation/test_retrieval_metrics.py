from __future__ import annotations

from app.evaluation.retrieval_metrics import (
    MRR,
    NDCG,
    PrecisionAtK,
    RecallAtK,
    compute_all_retrieval_metrics,
    dcg_at_k,
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


class TestRecallAtK:
    def test_perfect_recall(self) -> None:
        retrieved = ["a", "b", "c", "d", "e"]
        relevant = ["a", "b"]
        assert recall_at_k(retrieved, relevant, 5) == 1.0

    def test_partial_recall(self) -> None:
        retrieved = ["a", "b", "c", "d", "e"]
        relevant = ["a", "f"]
        assert recall_at_k(retrieved, relevant, 5) == 0.5

    def test_no_relevant(self) -> None:
        retrieved = ["a", "b", "c"]
        relevant = ["x", "y"]
        assert recall_at_k(retrieved, relevant, 3) == 0.0

    def test_empty_relevant(self) -> None:
        assert recall_at_k(["a", "b"], [], 3) == 0.0

    def test_k_smaller(self) -> None:
        retrieved = ["a", "b", "c", "d", "e"]
        relevant = ["a", "e"]
        assert recall_at_k(retrieved, relevant, 3) == 0.5


class TestPrecisionAtK:
    def test_perfect_precision(self) -> None:
        retrieved = ["a", "b", "c"]
        relevant = ["a", "b"]
        assert precision_at_k(retrieved, relevant, 3) == 2.0 / 3.0

    def test_all_relevant(self) -> None:
        retrieved = ["a", "b", "c"]
        relevant = ["a", "b", "c"]
        assert precision_at_k(retrieved, relevant, 3) == 1.0

    def test_no_relevant(self) -> None:
        retrieved = ["a", "b", "c"]
        relevant = ["x"]
        assert precision_at_k(retrieved, relevant, 3) == 0.0

    def test_k_zero(self) -> None:
        assert precision_at_k(["a"], ["a"], 0) == 0.0

    def test_empty_retrieved(self) -> None:
        assert precision_at_k([], ["a"], 3) == 0.0


class TestReciprocalRank:
    def test_first_rank(self) -> None:
        assert reciprocal_rank(["a", "b", "c"], ["a"]) == 1.0

    def test_second_rank(self) -> None:
        assert reciprocal_rank(["x", "a", "b"], ["a"]) == 0.5

    def test_not_found(self) -> None:
        assert reciprocal_rank(["a", "b"], ["c"]) == 0.0

    def test_empty_retrieved(self) -> None:
        assert reciprocal_rank([], ["a"]) == 0.0


class TestMRR:
    def test_mean_reciprocal_rank(self) -> None:
        queries_retrieved = [
            ["a", "b", "c"],
            ["x", "y", "z"],
            ["a", "b", "c"],
        ]
        queries_relevant = [
            ["a"],
            ["y"],
            ["z"],
        ]
        mrr = mean_reciprocal_rank(queries_retrieved, queries_relevant)
        expected = (1.0 + 0.5 + 0.0) / 3.0
        assert abs(mrr - expected) < 1e-10

    def test_empty_queries(self) -> None:
        assert mean_reciprocal_rank([], []) == 0.0


class TestDCG:
    def test_dcg_at_k(self) -> None:
        scores = [3.0, 2.0, 3.0, 0.0, 1.0]
        result = dcg_at_k(scores, 5)
        assert result > 0

    def test_dcg_empty(self) -> None:
        assert dcg_at_k([], 3) == 0.0


class TestNDCG:
    def test_ndcg_at_k_perfect(self) -> None:
        retrieved = ["a", "b", "c"]
        relevance = {"a": 3.0, "b": 2.0, "c": 1.0}
        result = ndcg_at_k(retrieved, relevance, 3)
        assert abs(result - 1.0) < 1e-10

    def test_ndcg_at_k_suboptimal(self) -> None:
        retrieved = ["c", "b", "a"]
        relevance = {"a": 3.0, "b": 2.0, "c": 1.0}
        result = ndcg_at_k(retrieved, relevance, 3)
        assert result < 1.0
        assert result > 0.0

    def test_ndcg_zero_ideal(self) -> None:
        retrieved = ["a", "b"]
        relevance = {"a": 0.0, "b": 0.0}
        assert ndcg_at_k(retrieved, relevance, 2) == 0.0


class TestRecallAtKMetric:
    def test_evaluate(self) -> None:
        metric = RecallAtK(k=3)
        result = metric.evaluate(
            retrieved=["a", "b", "c", "d"],
            relevant=["a", "e"],
        )
        assert result.metric_name == "Recall@3"
        assert result.category == "retrieval"
        assert result.score == 0.5
        assert result.details["k"] == 3

    def test_evaluate_no_data(self) -> None:
        metric = RecallAtK(k=5)
        result = metric.evaluate()
        assert result.score == 0.0


class TestPrecisionAtKMetric:
    def test_evaluate(self) -> None:
        metric = PrecisionAtK(k=3)
        result = metric.evaluate(
            retrieved=["a", "b", "c", "d"],
            relevant=["a", "e"],
        )
        assert result.metric_name == "Precision@3"
        assert result.score > 0


class TestMRRMetric:
    def test_evaluate(self) -> None:
        metric = MRR()
        result = metric.evaluate(
            queries_retrieved=[["a", "b"], ["c", "d"]],
            queries_relevant=[["a"], ["d"]],
        )
        assert result.metric_name == "MRR"
        assert result.score > 0
        assert result.details["num_queries"] == 2

    def test_evaluate_mismatched_lists(self) -> None:
        metric = MRR()
        result = metric.evaluate(
            queries_retrieved=[["a"]],
            queries_relevant=[["a"], ["b"]],
        )
        assert result.score == 0.0
        assert "error" in result.details

    def test_evaluate_no_data(self) -> None:
        metric = MRR()
        result = metric.evaluate()
        assert result.score == 0.0


class TestNDCGMetric:
    def test_evaluate(self) -> None:
        metric = NDCG(k=3)
        result = metric.evaluate(
            queries_retrieved=[["a", "b", "c"]],
            queries_relevance=[{"a": 3.0, "b": 2.0, "c": 1.0}],
        )
        assert result.metric_name == "NDCG@3"
        assert abs(result.score - 1.0) < 1e-10

    def test_evaluate_no_data(self) -> None:
        metric = NDCG(k=5)
        result = metric.evaluate()
        assert result.score == 0.0


class TestComputeAllRetrievalMetrics:
    def test_basic_computation(self) -> None:
        results = compute_all_retrieval_metrics(
            queries_retrieved=[["a", "b", "c"], ["d", "e", "f"]],
            queries_relevant=[["a"], ["f"]],
            queries_relevance=[{"a": 1.0}, {"f": 1.0}],
            k_values=(1, 3),
        )
        assert len(results) >= 6
        result_names = [r.metric_name for r in results]
        assert "Recall@1" in result_names
        assert "Recall@3" in result_names
        assert "Precision@1" in result_names
        assert "Precision@3" in result_names
        assert "NDCG@1" in result_names
        assert "MRR" in result_names

    def test_no_relevance_scores(self) -> None:
        results = compute_all_retrieval_metrics(
            queries_retrieved=[["a", "b"]],
            queries_relevant=[["a"]],
            k_values=(1,),
        )
        ndcg_names = [r.metric_name for r in results if "NDCG" in r.metric_name]
        assert len(ndcg_names) == 0
