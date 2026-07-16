from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class DocumentType(str, Enum):
    PRESCRIPTION = "prescription"
    CBC_REPORT = "cbc_report"
    LIPID_PROFILE = "lipid_profile"
    THYROID = "thyroid"
    KIDNEY_FUNCTION = "kidney_function"
    LIVER_FUNCTION = "liver_function"
    DIABETES = "diabetes"
    RADIOLOGY = "radiology"
    DISCHARGE_SUMMARY = "discharge_summary"
    CLINICAL_NOTES = "clinical_notes"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class QuestionCategory(str, Enum):
    DIAGNOSIS = "diagnosis"
    TREATMENT = "treatment"
    MEDICATION = "medication"
    LAB_RESULT = "lab_result"
    PROGNOSIS = "prognosis"
    FOLLOW_UP = "follow_up"
    SIDE_EFFECT = "side_effect"
    CONTRAINDICATION = "contraindication"
    DOSAGE = "dosage"
    REFERRAL = "referral"


class MetricName(str, Enum):
    RETRIEVAL_RECALL = "retrieval_recall"
    PRECISION_AT_K = "precision_at_k"
    MRR = "mrr"
    NDCG = "ndcg"
    CITATION_PRECISION = "citation_precision"
    CITATION_RECALL = "citation_recall"
    GROUNDEDNESS = "groundedness"
    ANSWER_RELEVANCE = "answer_relevance"
    HALLUCINATION_RATE = "hallucination_rate"
    LATENCY_MS = "latency_ms"
    MEMORY_USAGE_MB = "memory_usage_mb"
    TOKEN_USAGE = "token_usage"


@dataclass
class GroundTruthEntry:
    question: str
    expected_answer: str
    expected_citations: list[str] = field(default_factory=list)
    expected_medical_concepts: list[str] = field(default_factory=list)
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    category: QuestionCategory = QuestionCategory.DIAGNOSIS
    ground_truth_document: str = ""
    ground_truth_extraction: dict[str, Any] = field(default_factory=dict)
    expected_confidence: float = 0.9
    notes: str = ""


@dataclass
class GroundTruth:
    document_id: str
    document_type: DocumentType
    document_text: str
    structured_extraction: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    entries: list[GroundTruthEntry] = field(default_factory=list)
    version: str = "1.0.0"

    def add_entry(self, entry: GroundTruthEntry) -> None:
        self.entries.append(entry)

    def filter_by_difficulty(self, level: DifficultyLevel) -> list[GroundTruthEntry]:
        return [e for e in self.entries if e.difficulty == level]

    def filter_by_category(self, cat: QuestionCategory) -> list[GroundTruthEntry]:
        return [e for e in self.entries if e.category == cat]


@dataclass
class GroundTruthSet:
    name: str
    description: str = ""
    version: str = "1.0.0"
    documents: list[GroundTruth] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_document(self, doc: GroundTruth) -> None:
        self.documents.append(doc)

    def all_entries(self) -> list[GroundTruthEntry]:
        entries: list[GroundTruthEntry] = []
        for doc in self.documents:
            entries.extend(doc.entries)
        return entries

    def count(self) -> int:
        return len(self.all_entries())

    def stats(self) -> dict[str, Any]:
        entries = self.all_entries()
        by_difficulty: dict[str, int] = {}
        by_category: dict[str, int] = {}
        by_doc_type: dict[str, int] = {}
        for e in entries:
            by_difficulty[e.difficulty.value] = by_difficulty.get(e.difficulty.value, 0) + 1
            by_category[e.category.value] = by_category.get(e.category.value, 0) + 1
        for d in self.documents:
            dt = d.document_type.value
            by_doc_type[dt] = by_doc_type.get(dt, 0) + len(d.entries)
        return {
            "name": self.name,
            "version": self.version,
            "total_documents": len(self.documents),
            "total_entries": len(entries),
            "by_difficulty": by_difficulty,
            "by_category": by_category,
            "by_document_type": by_doc_type,
        }
