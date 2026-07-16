from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from app.validation.benchmark.benchmark_metrics import BenchmarkMetrics
from app.validation.dataset.ground_truth import GroundTruthSet


@dataclass
class ClinicalTestCase:
    question: str
    expected_answer: str = ""
    expected_citations: list[str] = field(default_factory=list)
    expected_concepts: list[str] = field(default_factory=list)
    difficulty: str = "medium"
    category: str = "diagnosis"
    ground_truth_document: str = ""
    expected_confidence: float = 0.0


@dataclass
class ClinicalTestResult:
    case: ClinicalTestCase
    passed: bool = False
    actual_answer: str = ""
    actual_citations: list[str] = field(default_factory=list)
    answer_match_score: float = 0.0
    citation_score: float = 0.0
    latency_ms: float = 0.0
    errors: list[str] = field(default_factory=list)


@dataclass
class ClinicalTestSummary:
    test_name: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    avg_latency_ms: float = 0.0
    avg_answer_score: float = 0.0
    avg_citation_score: float = 0.0
    by_difficulty: dict[str, dict[str, float]] = field(default_factory=dict)
    by_category: dict[str, dict[str, float]] = field(default_factory=dict)
    results: list[ClinicalTestResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class ClinicalTestRunner:
    def __init__(self):
        self.metrics = BenchmarkMetrics()

    def run(
        self,
        dataset: GroundTruthSet,
        answer_fn: Callable[[str], dict[str, Any]],
        test_name: str = "clinical_test",
    ) -> ClinicalTestSummary:
        entries = dataset.all_entries()
        results: list[ClinicalTestResult] = []

        for entry in entries:
            case = ClinicalTestCase(
                question=entry.question,
                expected_answer=entry.expected_answer,
                expected_citations=entry.expected_citations,
                expected_concepts=entry.expected_medical_concepts,
                difficulty=entry.difficulty.value,
                category=entry.category.value,
                ground_truth_document=entry.ground_truth_document,
                expected_confidence=entry.expected_confidence,
            )

            result = self._run_single(case, answer_fn)
            results.append(result)

        return self._summarize(results, test_name)

    def _run_single(
        self,
        case: ClinicalTestCase,
        answer_fn: Callable[[str], dict[str, Any]],
    ) -> ClinicalTestResult:
        result = ClinicalTestResult(case=case)
        start = time.perf_counter()

        try:
            response = answer_fn(case.question)
            elapsed = (time.perf_counter() - start) * 1000
            result.latency_ms = elapsed

            actual_answer = response.get("answer", response.get("text", ""))
            result.actual_answer = actual_answer

            actual_citations = response.get("citations", response.get("sources", []))
            result.actual_citations = actual_citations

            if case.expected_answer:
                result.answer_match_score = self._score_answer_match(
                    actual_answer, case.expected_answer
                )

            if case.expected_citations:
                result.citation_score = self._score_citations(
                    actual_citations, case.expected_citations
                )

            result.passed = result.answer_match_score >= 0.3 or not case.expected_answer

        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            result.latency_ms = elapsed
            result.errors.append(str(e))

        return result

    def _score_answer_match(self, actual: str, expected: str) -> float:
        a_words = set(actual.lower().split())
        e_words = set(expected.lower().split())
        if not e_words:
            return 1.0 if not actual else 0.0
        intersection = a_words & e_words
        recall = len(intersection) / len(e_words) if e_words else 0
        precision = len(intersection) / len(a_words) if a_words else 0
        return 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    def _score_citations(
        self, actual: list[str], expected: list[str],
    ) -> float:
        if not expected:
            return 1.0
        if not actual:
            return 0.0
        act_set = set(actual)
        exp_set = set(expected)
        overlap = act_set & exp_set
        return len(overlap) / len(exp_set)

    def _summarize(
        self,
        results: list[ClinicalTestResult],
        test_name: str,
    ) -> ClinicalTestSummary:
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed
        latencies = [r.latency_ms for r in results if r.latency_ms > 0]
        answer_scores = [r.answer_match_score for r in results if r.answer_match_score > 0]
        citation_scores = [r.citation_score for r in results if r.citation_score > 0]
        errors = [e for r in results for e in r.errors]

        by_difficulty: dict[str, dict[str, float]] = {}
        by_category: dict[str, dict[str, float]] = {}

        for r in results:
            diff = r.case.difficulty
            cat = r.case.category
            if diff not in by_difficulty:
                by_difficulty[diff] = {"total": 0, "passed": 0, "avg_score": 0.0, "scores": []}
            by_difficulty[diff]["total"] += 1
            if r.passed:
                by_difficulty[diff]["passed"] += 1
            by_difficulty[diff]["scores"].append(r.answer_match_score)

            if cat not in by_category:
                by_category[cat] = {"total": 0, "passed": 0, "avg_score": 0.0, "scores": []}
            by_category[cat]["total"] += 1
            if r.passed:
                by_category[cat]["passed"] += 1
            by_category[cat]["scores"].append(r.answer_match_score)

        for d in by_difficulty.values():
            d["avg_score"] = BenchmarkMetrics.mean(d["scores"]) if d["scores"] else 0.0
            del d["scores"]
        for c in by_category.values():
            c["avg_score"] = BenchmarkMetrics.mean(c["scores"]) if c["scores"] else 0.0
            del c["scores"]

        return ClinicalTestSummary(
            test_name=test_name,
            total=total,
            passed=passed,
            failed=failed,
            avg_latency_ms=BenchmarkMetrics.mean(latencies) if latencies else 0,
            avg_answer_score=BenchmarkMetrics.mean(answer_scores) if answer_scores else 0,
            avg_citation_score=BenchmarkMetrics.mean(citation_scores) if citation_scores else 0,
            by_difficulty=by_difficulty,
            by_category=by_category,
            results=results,
            errors=errors,
        )
