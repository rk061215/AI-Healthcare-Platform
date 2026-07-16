from __future__ import annotations

from typing import Any, Optional

from app.evaluation.metrics import Metric, MetricResult


def citation_precision(
    citations: list[str],
    relevant_sources: list[str],
) -> float:
    if not citations:
        return 0.0
    if not relevant_sources:
        return 0.0
    relevant_set = set(s.lower().strip() for s in relevant_sources)
    valid = sum(1 for c in citations if c.lower().strip() in relevant_set)
    return valid / len(citations)


def citation_recall(
    citations: list[str],
    relevant_sources: list[str],
) -> float:
    if not relevant_sources:
        return 0.0
    if not citations:
        return 0.0
    citation_set = set(c.lower().strip() for c in citations)
    found = sum(1 for s in relevant_sources if s.lower().strip() in citation_set)
    return found / len(relevant_sources)


def citation_f1(
    citations: list[str],
    relevant_sources: list[str],
) -> float:
    prec = citation_precision(citations, relevant_sources)
    rec = citation_recall(citations, relevant_sources)
    if prec + rec == 0.0:
        return 0.0
    return 2.0 * (prec * rec) / (prec + rec)


def citation_redundancy(
    citations: list[str],
) -> float:
    if not citations:
        return 0.0
    unique = len(set(c.lower().strip() for c in citations))
    return 1.0 - (unique / len(citations))


def citation_coverage(
    citations: list[str],
    expected_citations: list[str],
) -> float:
    if not expected_citations:
        return 0.0
    if not citations:
        return 0.0
    expected_set = set(e.lower().strip() for e in expected_citations)
    citation_set = set(c.lower().strip() for c in citations)
    covered = len(expected_set & citation_set)
    return covered / len(expected_set)


class CitationPrecisionMetric(Metric):
    def __init__(self) -> None:
        super().__init__(name="Citation Precision", category="citation")

    def evaluate(
        self,
        citations: Optional[list[str]] = None,
        relevant_sources: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> MetricResult:
        citations = citations or []
        relevant_sources = relevant_sources or []
        score = citation_precision(citations, relevant_sources)
        return MetricResult(
            metric_name=self._name,
            score=score,
            category=self._category,
            details={
                "num_citations": len(citations),
                "num_relevant_sources": len(relevant_sources),
            },
        )


class CitationRecallMetric(Metric):
    def __init__(self) -> None:
        super().__init__(name="Citation Recall", category="citation")

    def evaluate(
        self,
        citations: Optional[list[str]] = None,
        relevant_sources: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> MetricResult:
        citations = citations or []
        relevant_sources = relevant_sources or []
        score = citation_recall(citations, relevant_sources)
        return MetricResult(
            metric_name=self._name,
            score=score,
            category=self._category,
            details={
                "num_citations": len(citations),
                "num_relevant_sources": len(relevant_sources),
            },
        )


class CitationF1Metric(Metric):
    def __init__(self) -> None:
        super().__init__(name="Citation F1", category="citation")

    def evaluate(
        self,
        citations: Optional[list[str]] = None,
        relevant_sources: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> MetricResult:
        citations = citations or []
        relevant_sources = relevant_sources or []
        score = citation_f1(citations, relevant_sources)
        return MetricResult(
            metric_name=self._name,
            score=score,
            category=self._category,
            details={
                "num_citations": len(citations),
                "num_relevant_sources": len(relevant_sources),
            },
        )


class CitationCoverageMetric(Metric):
    def __init__(self) -> None:
        super().__init__(name="Citation Coverage", category="citation")

    def evaluate(
        self,
        citations: Optional[list[str]] = None,
        expected_citations: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> MetricResult:
        citations = citations or []
        expected_citations = expected_citations or []
        score = citation_coverage(citations, expected_citations)
        return MetricResult(
            metric_name=self._name,
            score=score,
            category=self._category,
            details={
                "num_citations": len(citations),
                "num_expected": len(expected_citations),
            },
        )


class CitationRedundancyMetric(Metric):
    def __init__(self) -> None:
        super().__init__(name="Citation Redundancy", category="citation")

    def evaluate(
        self,
        citations: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> MetricResult:
        citations = citations or []
        redundancy = citation_redundancy(citations)
        return MetricResult(
            metric_name=self._name,
            score=redundancy,
            category=self._category,
            details={"num_citations": len(citations), "num_unique": len(set(c.lower().strip() for c in citations))},
        )


def compute_all_citation_metrics(
    all_citations: list[list[str]],
    all_relevant_sources: list[list[str]],
    all_expected_citations: list[list[str]],
) -> list[MetricResult]:
    num_queries = len(all_citations)
    if num_queries == 0:
        return []
    avg_precision = sum(
        citation_precision(all_citations[i], all_relevant_sources[i])
        for i in range(num_queries)
    ) / num_queries
    avg_recall = sum(
        citation_recall(all_citations[i], all_relevant_sources[i])
        for i in range(num_queries)
    ) / num_queries
    avg_f1 = sum(
        citation_f1(all_citations[i], all_relevant_sources[i])
        for i in range(num_queries)
    ) / num_queries
    avg_coverage = sum(
        citation_coverage(all_citations[i], all_expected_citations[i])
        for i in range(num_queries)
    ) / num_queries
    avg_redundancy = sum(
        citation_redundancy(all_citations[i])
        for i in range(num_queries)
    ) / num_queries
    return [
        MetricResult(metric_name="Citation Precision", score=avg_precision, category="citation", details={"num_queries": num_queries}, num_samples=num_queries),
        MetricResult(metric_name="Citation Recall", score=avg_recall, category="citation", details={"num_queries": num_queries}, num_samples=num_queries),
        MetricResult(metric_name="Citation F1", score=avg_f1, category="citation", details={"num_queries": num_queries}, num_samples=num_queries),
        MetricResult(metric_name="Citation Coverage", score=avg_coverage, category="citation", details={"num_queries": num_queries}, num_samples=num_queries),
        MetricResult(metric_name="Citation Redundancy", score=avg_redundancy, category="citation", details={"num_queries": num_queries}, num_samples=num_queries),
    ]
