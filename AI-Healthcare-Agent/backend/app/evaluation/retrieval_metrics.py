from __future__ import annotations

import math
from typing import Any, Optional

from app.evaluation.metrics import Metric, MetricResult


def recall_at_k(
    retrieved: list[str],
    relevant: list[str],
    k: int,
) -> float:
    relevant_set = set(relevant)
    if not relevant_set:
        return 0.0
    retrieved_at_k = retrieved[:k]
    relevant_retrieved = sum(1 for doc_id in retrieved_at_k if doc_id in relevant_set)
    return relevant_retrieved / len(relevant_set)


def precision_at_k(
    retrieved: list[str],
    relevant: list[str],
    k: int,
) -> float:
    if k <= 0:
        return 0.0
    relevant_set = set(relevant)
    retrieved_at_k = retrieved[:k]
    if not retrieved_at_k:
        return 0.0
    relevant_retrieved = sum(1 for doc_id in retrieved_at_k if doc_id in relevant_set)
    return relevant_retrieved / len(retrieved_at_k)


def reciprocal_rank(
    retrieved: list[str],
    relevant: list[str],
) -> float:
    relevant_set = set(relevant)
    for rank, doc_id in enumerate(retrieved, start=1):
        if doc_id in relevant_set:
            return 1.0 / rank
    return 0.0


def mean_reciprocal_rank(
    queries_retrieved: list[list[str]],
    queries_relevant: list[list[str]],
) -> float:
    if not queries_retrieved:
        return 0.0
    total_rr = sum(
        reciprocal_rank(retrieved, relevant)
        for retrieved, relevant in zip(queries_retrieved, queries_relevant)
    )
    return total_rr / len(queries_retrieved)


def dcg_at_k(
    relevance_scores: list[float],
    k: int,
) -> float:
    scores = relevance_scores[:k]
    if not scores:
        return 0.0
    return scores[0] + sum(
        score / math.log2(idx + 2)
        for idx, score in enumerate(scores[1:], start=2)
    )


def ndcg_at_k(
    retrieved: list[str],
    relevance_map: dict[str, float],
    k: int,
) -> float:
    if k <= 0 or not retrieved:
        return 0.0
    scores = [relevance_map.get(doc_id, 0.0) for doc_id in retrieved[:k]]
    ideal_scores = sorted(
        [s for s in relevance_map.values() if s > 0],
        reverse=True,
    )[:k]
    actual_dcg = dcg_at_k(scores, k)
    ideal_dcg = dcg_at_k(ideal_scores, k)
    if ideal_dcg == 0.0:
        return 0.0
    return actual_dcg / ideal_dcg


def average_ndcg(
    queries_retrieved: list[list[str]],
    queries_relevance: list[dict[str, float]],
    k: int,
) -> float:
    if not queries_retrieved:
        return 0.0
    total_ndcg = sum(
        ndcg_at_k(retrieved, relevance, k)
        for retrieved, relevance in zip(queries_retrieved, queries_relevance)
    )
    return total_ndcg / len(queries_retrieved)


class RecallAtK(Metric):
    def __init__(self, k: int = 10) -> None:
        super().__init__(name=f"Recall@{k}", category="retrieval")
        self._k = k

    def evaluate(
        self,
        retrieved: Optional[list[str]] = None,
        relevant: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> MetricResult:
        retrieved = retrieved or []
        relevant = relevant or []
        score = recall_at_k(retrieved, relevant, self._k)
        return MetricResult(
            metric_name=self._name,
            score=score,
            category=self._category,
            details={"k": self._k, "retrieved_count": len(retrieved), "relevant_count": len(relevant)},
        )


class PrecisionAtK(Metric):
    def __init__(self, k: int = 10) -> None:
        super().__init__(name=f"Precision@{k}", category="retrieval")
        self._k = k

    def evaluate(
        self,
        retrieved: Optional[list[str]] = None,
        relevant: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> MetricResult:
        retrieved = retrieved or []
        relevant = relevant or []
        score = precision_at_k(retrieved, relevant, self._k)
        return MetricResult(
            metric_name=self._name,
            score=score,
            category=self._category,
            details={"k": self._k, "retrieved_count": len(retrieved), "relevant_count": len(relevant)},
        )


class MRR(Metric):
    def __init__(self) -> None:
        super().__init__(name="MRR", category="retrieval")

    def evaluate(
        self,
        queries_retrieved: Optional[list[list[str]]] = None,
        queries_relevant: Optional[list[list[str]]] = None,
        **kwargs: Any,
    ) -> MetricResult:
        queries_retrieved = queries_retrieved or []
        queries_relevant = queries_relevant or []
        if not queries_retrieved or not queries_relevant:
            return MetricResult(
                metric_name=self._name,
                score=0.0,
                category=self._category,
                details={"error": "No query data provided", "num_queries": 0},
            )
        if len(queries_retrieved) != len(queries_relevant):
            return MetricResult(
                metric_name=self._name,
                score=0.0,
                category=self._category,
                details={"error": "Mismatched query/retrieved lists"},
            )
        score = mean_reciprocal_rank(queries_retrieved, queries_relevant)
        return MetricResult(
            metric_name=self._name,
            score=score,
            category=self._category,
            details={"num_queries": len(queries_retrieved), "per_query_rr": [
                reciprocal_rank(r, rel)
                for r, rel in zip(queries_retrieved, queries_relevant)
            ]},
        )


class NDCG(Metric):
    def __init__(self, k: int = 10) -> None:
        super().__init__(name=f"NDCG@{k}", category="retrieval")
        self._k = k

    def evaluate(
        self,
        queries_retrieved: Optional[list[list[str]]] = None,
        queries_relevance: Optional[list[dict[str, float]]] = None,
        **kwargs: Any,
    ) -> MetricResult:
        queries_retrieved = queries_retrieved or []
        queries_relevance = queries_relevance or []
        if not queries_retrieved or not queries_relevance:
            return MetricResult(
                metric_name=self._name,
                score=0.0,
                category=self._category,
                details={"error": "No query data provided"},
            )
        if len(queries_retrieved) != len(queries_relevance):
            return MetricResult(
                metric_name=self._name,
                score=0.0,
                category=self._category,
                details={"error": "Mismatched query/relevance lists"},
            )
        score = average_ndcg(queries_retrieved, queries_relevance, self._k)
        per_query = [
            ndcg_at_k(r, rel, self._k)
            for r, rel in zip(queries_retrieved, queries_relevance)
        ]
        return MetricResult(
            metric_name=self._name,
            score=score,
            category=self._category,
            details={"k": self._k, "num_queries": len(queries_retrieved), "per_query_ndcg": per_query},
        )


def compute_all_retrieval_metrics(
    queries_retrieved: list[list[str]],
    queries_relevant: list[list[str]],
    queries_relevance: Optional[list[dict[str, float]]] = None,
    k_values: tuple[int, ...] = (1, 3, 5, 10),
) -> list[MetricResult]:
    results: list[MetricResult] = []
    for k in k_values:
        recall_scores = [
            recall_at_k(retrieved, relevant, k)
            for retrieved, relevant in zip(queries_retrieved, queries_relevant)
        ]
        avg_recall = sum(recall_scores) / len(recall_scores) if recall_scores else 0.0
        results.append(MetricResult(
            metric_name=f"Recall@{k}",
            score=avg_recall,
            category="retrieval",
            details={"k": k, "num_queries": len(queries_retrieved), "per_query": recall_scores},
            num_samples=len(queries_retrieved),
        ))
        precision_scores = [
            precision_at_k(retrieved, relevant, k)
            for retrieved, relevant in zip(queries_retrieved, queries_relevant)
        ]
        avg_precision = sum(precision_scores) / len(precision_scores) if precision_scores else 0.0
        results.append(MetricResult(
            metric_name=f"Precision@{k}",
            score=avg_precision,
            category="retrieval",
            details={"k": k, "num_queries": len(queries_retrieved), "per_query": precision_scores},
            num_samples=len(queries_retrieved),
        ))
    if queries_relevance:
        for k in k_values:
            ndcg_scores = [
                ndcg_at_k(retrieved, relevance, k)
                for retrieved, relevance in zip(queries_retrieved, queries_relevance)
            ]
            avg_ndcg = sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0
            results.append(MetricResult(
                metric_name=f"NDCG@{k}",
                score=avg_ndcg,
                category="retrieval",
                details={"k": k, "num_queries": len(queries_retrieved), "per_query": ndcg_scores},
                num_samples=len(queries_retrieved),
            ))
    mrr_score = mean_reciprocal_rank(queries_retrieved, queries_relevant)
    results.append(MetricResult(
        metric_name="MRR",
        score=mrr_score,
        category="retrieval",
        details={"num_queries": len(queries_retrieved)},
        num_samples=len(queries_retrieved),
    ))
    return results
