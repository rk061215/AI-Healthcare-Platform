from __future__ import annotations

import math
from typing import Any, Optional


class BenchmarkMetrics:

    @staticmethod
    def retrieval_recall(relevant_retrieved: int, total_relevant: int) -> float:
        if total_relevant == 0:
            return 0.0
        return relevant_retrieved / total_relevant

    @staticmethod
    def precision_at_k(relevant_retrieved: int, k: int) -> float:
        if k == 0:
            return 0.0
        return relevant_retrieved / k

    @staticmethod
    def average_precision_at_k(ranked_relevance: list[bool], k: int) -> float:
        if k == 0 or not ranked_relevance:
            return 0.0
        trimmed = ranked_relevance[:k]
        total_relevant = sum(trimmed)
        if total_relevant == 0:
            return 0.0
        cum_precision = 0.0
        relevant_count = 0
        for i, rel in enumerate(trimmed):
            if rel:
                relevant_count += 1
                cum_precision += relevant_count / (i + 1)
        return cum_precision / total_relevant

    @staticmethod
    def mean_reciprocal_rank(ranked_relevance: list[bool], k: int) -> float:
        trimmed = ranked_relevance[:k]
        for i, rel in enumerate(trimmed):
            if rel:
                return 1.0 / (i + 1)
        return 0.0

    @staticmethod
    def ndcg_at_k(ranked_relevance: list[float], k: int) -> float:
        trimmed = ranked_relevance[:k]
        dcg = sum(
            (2 ** rel - 1) / math.log2(i + 2)
            for i, rel in enumerate(trimmed)
        )
        ideal = sorted(ranked_relevance, reverse=True)[:k]
        idcg = sum(
            (2 ** rel - 1) / math.log2(i + 2)
            for i, rel in enumerate(ideal)
        )
        if idcg == 0:
            return 0.0
        return dcg / idcg

    @staticmethod
    def citation_precision(correct_citations: int, total_citations: int) -> float:
        if total_citations == 0:
            return 0.0
        return correct_citations / total_citations

    @staticmethod
    def citation_recall(correct_citations: int, expected_citations: int) -> float:
        if expected_citations == 0:
            return 0.0
        return correct_citations / expected_citations

    @staticmethod
    def citation_f1(precision: float, recall: float) -> float:
        if precision + recall == 0:
            return 0.0
        return 2 * precision * recall / (precision + recall)

    @staticmethod
    def groundedness(
        supported_claims: int, total_claims: int
    ) -> float:
        if total_claims == 0:
            return 1.0
        return supported_claims / total_claims

    @staticmethod
    def hallucination_rate(
        unsupported_claims: int, total_claims: int
    ) -> float:
        if total_claims == 0:
            return 0.0
        return unsupported_claims / total_claims

    @staticmethod
    def answer_relevance(
        relevant_answers: int, total_questions: int
    ) -> float:
        if total_questions == 0:
            return 0.0
        return relevant_answers / total_questions

    @staticmethod
    def mean(values: list[float]) -> float:
        if not values:
            return 0.0
        return sum(values) / len(values)

    @staticmethod
    def median(values: list[float]) -> float:
        if not values:
            return 0.0
        sorted_v = sorted(values)
        n = len(sorted_v)
        mid = n // 2
        if n % 2 == 0:
            return (sorted_v[mid - 1] + sorted_v[mid]) / 2
        return float(sorted_v[mid])

    @staticmethod
    def percentile(values: list[float], p: float) -> float:
        if not values:
            return 0.0
        sorted_v = sorted(values)
        k = (p / 100.0) * (len(sorted_v) - 1)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return float(sorted_v[int(k)])
        d0 = sorted_v[f] * (c - k)
        d1 = sorted_v[c] * (k - f)
        return d0 + d1

    @staticmethod
    def std_dev(values: list[float]) -> float:
        if len(values) < 2:
            return 0.0
        mean_v = BenchmarkMetrics.mean(values)
        variance = sum((x - mean_v) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)

    @staticmethod
    def compute_all(
        ranked_relevance: list[float],
        k_values: list[int],
    ) -> dict[str, float]:
        metrics: dict[str, float] = {}
        bool_rel = [r > 0 for r in ranked_relevance]
        total_rel = sum(bool_rel)
        for k in k_values:
            metrics[f"precision_at_{k}"] = BenchmarkMetrics.precision_at_k(
                sum(bool_rel[:k]), k
            )
            metrics[f"recall_at_{k}"] = BenchmarkMetrics.retrieval_recall(
                sum(bool_rel[:k]), total_rel
            )
            metrics[f"mrr_at_{k}"] = BenchmarkMetrics.mean_reciprocal_rank(
                bool_rel, k
            )
            metrics[f"ndcg_at_{k}"] = BenchmarkMetrics.ndcg_at_k(
                ranked_relevance, k
            )
            metrics[f"map_at_{k}"] = BenchmarkMetrics.average_precision_at_k(
                bool_rel, k
            )
        return metrics
