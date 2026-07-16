from __future__ import annotations

import re
from typing import Any, Optional

from app.evaluation.metrics import Metric, MetricResult


def groundedness(
    answer: str,
    context_chunks: list[str],
    overlap_threshold: float = 0.3,
) -> float:
    if not answer or not context_chunks:
        return 0.0
    answer_sentences = re.split(r'(?<=[.!?])\s+', answer.strip())
    if not answer_sentences:
        return 0.0
    supported = 0
    for sentence in answer_sentences:
        sentence_lower = sentence.lower().strip()
        if not sentence_lower:
            continue
        best_overlap = 0.0
        for chunk in context_chunks:
            chunk_lower = chunk.lower()
            overlap = _compute_text_overlap(sentence_lower, chunk_lower)
            best_overlap = max(best_overlap, overlap)
        if best_overlap >= overlap_threshold:
            supported += 1
    return supported / len([s for s in answer_sentences if s.strip()])


def _compute_text_overlap(text_a: str, text_b: str) -> float:
    words_a = set(text_a.split())
    words_b = set(text_b.split())
    if not words_a:
        return 0.0
    intersection = words_a & words_b
    return len(intersection) / len(words_a)


def citation_accuracy(
    citations: list[dict[str, Any]],
    context_chunks: list[str],
) -> float:
    if not citations:
        return 0.0
    if not context_chunks:
        return 0.0
    valid = 0
    for citation in citations:
        citation_text = citation.get("text", "")
        if not citation_text:
            continue
        citation_lower = citation_text.lower()
        found = any(citation_lower in chunk.lower() for chunk in context_chunks)
        if found:
            valid += 1
    return valid / len(citations)


def context_precision(
    retrieved_chunks: list[str],
    relevant_chunks: list[str],
) -> float:
    if not retrieved_chunks:
        return 0.0
    if not relevant_chunks:
        return 0.0
    relevant_set = set(c.lower().strip() for c in relevant_chunks)
    if not relevant_set:
        return 0.0
    relevant_retrieved = sum(
        1 for chunk in retrieved_chunks
        if chunk.lower().strip() in relevant_set
    )
    return relevant_retrieved / len(retrieved_chunks)


def context_recall(
    retrieved_chunks: list[str],
    relevant_chunks: list[str],
) -> float:
    if not relevant_chunks:
        return 0.0
    if not retrieved_chunks:
        return 0.0
    retrieved_set = set(c.lower().strip() for c in retrieved_chunks)
    relevant_retrieved = sum(
        1 for chunk in relevant_chunks
        if chunk.lower().strip() in retrieved_set
    )
    return relevant_retrieved / len(relevant_chunks)


def answer_relevance(
    answer: str,
    question: str,
) -> float:
    if not answer or not question:
        return 0.0
    question_words = set(re.sub(r'[^\w\s]', '', question.lower()).split())
    answer_words = set(re.sub(r'[^\w\s]', '', answer.lower()).split())
    if not question_words:
        return 0.0
    if not answer_words:
        return 0.0
    intersection = question_words & answer_words
    return len(intersection) / len(question_words)


def medication_extraction_accuracy(
    expected_medications: list[str],
    extracted_medications: list[str],
) -> float:
    return _exact_match_accuracy(expected_medications, extracted_medications)


def diagnosis_accuracy(
    expected_diagnoses: list[str],
    extracted_diagnoses: list[str],
) -> float:
    return _exact_match_accuracy(expected_diagnoses, extracted_diagnoses)


def lab_result_accuracy(
    expected_lab_results: list[dict[str, str]],
    extracted_lab_results: list[dict[str, str]],
) -> float:
    if not expected_lab_results:
        return 0.0
    if not extracted_lab_results:
        return 0.0
    matched = 0
    for expected in expected_lab_results:
        expected_normalized = {k.lower(): v.lower().strip() for k, v in expected.items()}
        for extracted in extracted_lab_results:
            extracted_normalized = {k.lower(): v.lower().strip() for k, v in extracted.items()}
            if expected_normalized == extracted_normalized:
                matched += 1
                break
    return matched / len(expected_lab_results)


def follow_up_extraction_accuracy(
    expected_follow_ups: list[str],
    extracted_follow_ups: list[str],
) -> float:
    return _exact_match_accuracy(expected_follow_ups, extracted_follow_ups)


def _exact_match_accuracy(
    expected: list[str],
    extracted: list[str],
) -> float:
    if not expected:
        return 0.0
    if not extracted:
        return 0.0
    expected_normalized = [e.lower().strip() for e in expected]
    extracted_normalized = [e.lower().strip() for e in extracted]
    matched = sum(1 for e in expected_normalized if e in extracted_normalized)
    return matched / len(expected_normalized)


class GroundednessMetric(Metric):
    def __init__(self, overlap_threshold: float = 0.3) -> None:
        super().__init__(name="Groundedness", category="rag")
        self._overlap_threshold = overlap_threshold

    def evaluate(
        self,
        answer: Optional[str] = None,
        context_chunks: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> MetricResult:
        score = groundedness(answer or "", context_chunks or [], self._overlap_threshold)
        return MetricResult(
            metric_name=self._name,
            score=score,
            category=self._category,
            details={"overlap_threshold": self._overlap_threshold},
        )


class CitationAccuracyMetric(Metric):
    def __init__(self) -> None:
        super().__init__(name="Citation Accuracy", category="rag")

    def evaluate(
        self,
        citations: Optional[list[dict[str, Any]]] = None,
        context_chunks: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> MetricResult:
        citations = citations or []
        context_chunks = context_chunks or []
        score = citation_accuracy(citations, context_chunks)
        return MetricResult(
            metric_name=self._name,
            score=score,
            category=self._category,
            details={"num_citations": len(citations), "num_chunks": len(context_chunks)},
        )


class ContextPrecisionMetric(Metric):
    def __init__(self) -> None:
        super().__init__(name="Context Precision", category="rag")

    def evaluate(
        self,
        retrieved_chunks: Optional[list[str]] = None,
        relevant_chunks: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> MetricResult:
        score = context_precision(retrieved_chunks or [], relevant_chunks or [])
        return MetricResult(
            metric_name=self._name,
            score=score,
            category=self._category,
            details={
                "num_retrieved": len(retrieved_chunks or []),
                "num_relevant": len(relevant_chunks or []),
            },
        )


class ContextRecallMetric(Metric):
    def __init__(self) -> None:
        super().__init__(name="Context Recall", category="rag")

    def evaluate(
        self,
        retrieved_chunks: Optional[list[str]] = None,
        relevant_chunks: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> MetricResult:
        score = context_recall(retrieved_chunks or [], relevant_chunks or [])
        return MetricResult(
            metric_name=self._name,
            score=score,
            category=self._category,
            details={
                "num_retrieved": len(retrieved_chunks or []),
                "num_relevant": len(relevant_chunks or []),
            },
        )


class AnswerRelevanceMetric(Metric):
    def __init__(self) -> None:
        super().__init__(name="Answer Relevance", category="rag")

    def evaluate(
        self,
        answer: Optional[str] = None,
        question: Optional[str] = None,
        **kwargs: Any,
    ) -> MetricResult:
        score = answer_relevance(answer or "", question or "")
        return MetricResult(
            metric_name=self._name,
            score=score,
            category=self._category,
        )


class MedicationAccuracyMetric(Metric):
    def __init__(self) -> None:
        super().__init__(name="Medication Extraction Accuracy", category="medical_qa")

    def evaluate(
        self,
        expected_medications: Optional[list[str]] = None,
        extracted_medications: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> MetricResult:
        score = medication_extraction_accuracy(
            expected_medications or [],
            extracted_medications or [],
        )
        return MetricResult(
            metric_name=self._name,
            score=score,
            category=self._category,
            details={
                "expected_count": len(expected_medications or []),
                "extracted_count": len(extracted_medications or []),
            },
        )


class DiagnosisAccuracyMetric(Metric):
    def __init__(self) -> None:
        super().__init__(name="Diagnosis Accuracy", category="medical_qa")

    def evaluate(
        self,
        expected_diagnoses: Optional[list[str]] = None,
        extracted_diagnoses: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> MetricResult:
        score = diagnosis_accuracy(
            expected_diagnoses or [],
            extracted_diagnoses or [],
        )
        return MetricResult(
            metric_name=self._name,
            score=score,
            category=self._category,
            details={
                "expected_count": len(expected_diagnoses or []),
                "extracted_count": len(extracted_diagnoses or []),
            },
        )


class LabResultAccuracyMetric(Metric):
    def __init__(self) -> None:
        super().__init__(name="Lab Result Accuracy", category="medical_qa")

    def evaluate(
        self,
        expected_lab_results: Optional[list[dict[str, str]]] = None,
        extracted_lab_results: Optional[list[dict[str, str]]] = None,
        **kwargs: Any,
    ) -> MetricResult:
        score = lab_result_accuracy(
            expected_lab_results or [],
            extracted_lab_results or [],
        )
        return MetricResult(
            metric_name=self._name,
            score=score,
            category=self._category,
            details={
                "expected_count": len(expected_lab_results or []),
                "extracted_count": len(extracted_lab_results or []),
            },
        )


class FollowUpAccuracyMetric(Metric):
    def __init__(self) -> None:
        super().__init__(name="Follow-up Extraction Accuracy", category="medical_qa")

    def evaluate(
        self,
        expected_follow_ups: Optional[list[str]] = None,
        extracted_follow_ups: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> MetricResult:
        score = follow_up_extraction_accuracy(
            expected_follow_ups or [],
            extracted_follow_ups or [],
        )
        return MetricResult(
            metric_name=self._name,
            score=score,
            category=self._category,
            details={
                "expected_count": len(expected_follow_ups or []),
                "extracted_count": len(extracted_follow_ups or []),
            },
        )


def compute_all_rag_metrics(
    answers: list[str],
    questions: list[str],
    contexts: list[list[str]],
    relevant_chunks_list: list[list[str]],
    citations_list: list[list[dict[str, Any]]],
) -> list[MetricResult]:
    results: list[MetricResult] = []
    num_queries = len(answers)
    if num_queries == 0:
        return results
    groundedness_scores = sum(
        groundedness(answers[i], contexts[i]) for i in range(num_queries)
    ) / num_queries
    results.append(MetricResult(
        metric_name="Groundedness",
        score=groundedness_scores,
        category="rag",
        details={"num_samples": num_queries},
        num_samples=num_queries,
    ))
    relevance_scores = sum(
        answer_relevance(answers[i], questions[i]) for i in range(num_queries)
    ) / num_queries
    results.append(MetricResult(
        metric_name="Answer Relevance",
        score=relevance_scores,
        category="rag",
        details={"num_samples": num_queries},
        num_samples=num_queries,
    ))
    context_prec_scores = sum(
        context_precision(contexts[i], relevant_chunks_list[i])
        for i in range(num_queries)
    ) / num_queries
    results.append(MetricResult(
        metric_name="Context Precision",
        score=context_prec_scores,
        category="rag",
        details={"num_samples": num_queries},
        num_samples=num_queries,
    ))
    context_rec_scores = sum(
        context_recall(contexts[i], relevant_chunks_list[i])
        for i in range(num_queries)
    ) / num_queries
    results.append(MetricResult(
        metric_name="Context Recall",
        score=context_rec_scores,
        category="rag",
        details={"num_samples": num_queries},
        num_samples=num_queries,
    ))
    citation_acc_scores = 0.0
    citation_queries = 0
    for i in range(num_queries):
        if citations_list[i]:
            citation_acc_scores += citation_accuracy(citations_list[i], contexts[i])
            citation_queries += 1
    if citation_queries > 0:
        citation_acc_scores /= citation_queries
    results.append(MetricResult(
        metric_name="Citation Accuracy",
        score=citation_acc_scores,
        category="rag",
        details={"num_samples": citation_queries, "total_queries": num_queries},
        num_samples=citation_queries,
    ))
    return results
