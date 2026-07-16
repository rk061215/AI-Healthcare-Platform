from __future__ import annotations

import re
from typing import Any, Optional

from app.evaluation.metrics import Metric, MetricResult


HALLUCINATION_PATTERNS: list[str] = [
    r'\bsignificant\s+improvement\b',
    r'\bdramatic\s+recovery\b',
    r'\bcompletely\s+cured\b',
    r'\bguaranteed\b',
    r'\b100%\s+(effective|safe|cure)\b',
    r'\bno\s+(risk|side\s*effects)\b',
    r'\bproven\s+(to|cure|treatment)\b',
    r'\bmiraculous\b',
    r'\bbreakthrough\s+(treatment|cure|therapy)\b',
]


SUPPORTED_PATTERNS: list[str] = [
    r'\bbased\s+on\s+(the\s+)?(available\s+)?(information|records|data|reports)\b',
    r'\baccording\s+to\s+(the\s+)?(provided\s+)?(context|document|report|record)\b',
    r'\bthe\s+(provided\s+)?(context|document|report)\s+(indicates|shows|suggests|states)\b',
    r'\bas\s+(per|stated\s+in)\s+(the\s+)?(provided\s+)?(context|document|report)\b',
]


UNSUPPORTED_CLAIM_PATTERNS: list[str] = [
    r'\byou\s+(should|must|need\s+to)\s+(take|stop|start)\b',
    r'\b(i|we)\s+(recommend|prescribe|suggest)\b',
    r'\b(discontinue|stop\s+taking)\s+your\s+medication\b',
    r'\bincrease\s+(the\s+)?dosage\b',
    r'\bdecrease\s+(the\s+)?dosage\b',
]


def detect_hallucinated_claims(
    answer: str,
    context_chunks: list[str],
    overlap_threshold: float = 0.2,
) -> list[str]:
    if not answer:
        return []
    answer_sentences = re.split(r'(?<=[.!?])\s+', answer.strip())
    hallucinated: list[str] = []
    for sentence in answer_sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        sentence_lower = sentence.lower()
        best_overlap = 0.0
        for chunk in context_chunks:
            chunk_lower = chunk.lower()
            words_sentence = set(sentence_lower.split())
            words_chunk = set(chunk_lower.split())
            if not words_sentence:
                continue
            intersection = words_sentence & words_chunk
            overlap = len(intersection) / len(words_sentence)
            best_overlap = max(best_overlap, overlap)
        has_support_phrase = any(
            re.search(pattern, sentence_lower)
            for pattern in SUPPORTED_PATTERNS
        )
        if best_overlap < overlap_threshold and not has_support_phrase:
            hallucinated.append(sentence)
    return hallucinated


def hallucination_rate(
    answer: str,
    context_chunks: list[str],
    overlap_threshold: float = 0.2,
) -> float:
    if not answer:
        return 0.0
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', answer.strip()) if s.strip()]
    if not sentences:
        return 0.0
    hallucinated = detect_hallucinated_claims(answer, context_chunks, overlap_threshold)
    return len(hallucinated) / len(sentences)


def contains_hallucination_patterns(answer: str) -> list[str]:
    if not answer:
        return []
    answer_lower = answer.lower()
    return [
        pattern for pattern in HALLUCINATION_PATTERNS
        if re.search(pattern, answer_lower)
    ]


def contains_unsupported_medical_claims(answer: str) -> list[str]:
    if not answer:
        return []
    answer_lower = answer.lower()
    return [
        pattern for pattern in UNSUPPORTED_CLAIM_PATTERNS
        if re.search(pattern, answer_lower)
    ]


class HallucinationRateMetric(Metric):
    def __init__(self, overlap_threshold: float = 0.2) -> None:
        super().__init__(name="Hallucination Rate", category="hallucination")
        self._overlap_threshold = overlap_threshold

    def evaluate(
        self,
        answer: Optional[str] = None,
        context_chunks: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> MetricResult:
        answer = answer or ""
        context_chunks = context_chunks or []
        rate = hallucination_rate(answer, context_chunks, self._overlap_threshold)
        hallucinated_claims = detect_hallucinated_claims(
            answer, context_chunks, self._overlap_threshold,
        )
        pattern_matches = contains_hallucination_patterns(answer)
        unsupported_claims = contains_unsupported_medical_claims(answer)
        return MetricResult(
            metric_name=self._name,
            score=1.0 - rate,
            category=self._category,
            details={
                "hallucination_rate": rate,
                "hallucinated_claims_count": len(hallucinated_claims),
                "hallucinated_claims": hallucinated_claims[:10],
                "overlap_threshold": self._overlap_threshold,
                "pattern_matches": pattern_matches,
                "unsupported_medical_claims": unsupported_claims,
            },
        )


def compute_all_hallucination_metrics(
    answers: list[str],
    contexts: list[list[str]],
    overlap_threshold: float = 0.2,
) -> list[MetricResult]:
    num_queries = len(answers)
    if num_queries == 0:
        return []
    total_rate = sum(
        hallucination_rate(answers[i], contexts[i], overlap_threshold)
        for i in range(num_queries)
    ) / num_queries
    total_claims = sum(
        len(detect_hallucinated_claims(answers[i], contexts[i], overlap_threshold))
        for i in range(num_queries)
    )
    total_patterns = sum(
        len(contains_hallucination_patterns(answers[i]))
        for i in range(num_queries)
    )
    total_unsupported = sum(
        len(contains_unsupported_medical_claims(answers[i]))
        for i in range(num_queries)
    )
    return [
        MetricResult(
            metric_name="Hallucination Rate",
            score=1.0 - total_rate,
            category="hallucination",
            details={
                "hallucination_rate": total_rate,
                "total_hallucinated_claims": total_claims,
                "total_pattern_matches": total_patterns,
                "total_unsupported_claims": total_unsupported,
                "num_samples": num_queries,
            },
            num_samples=num_queries,
        ),
    ]
