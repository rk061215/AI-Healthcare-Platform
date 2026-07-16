from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from app.evaluation.exceptions import GroundTruthError


@dataclass
class GroundTruthEntry:
    query: str
    expected_answer: str
    expected_citations: list[str] = field(default_factory=list)
    expected_retrieved_docs: list[str] = field(default_factory=list)
    expected_relevance_scores: dict[str, float] = field(default_factory=dict)
    expected_medications: list[str] = field(default_factory=list)
    expected_diagnoses: list[str] = field(default_factory=list)
    expected_lab_results: list[dict[str, str]] = field(default_factory=list)
    expected_follow_ups: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GroundTruthSet:
    name: str
    entries: list[GroundTruthEntry] = field(default_factory=list)
    version: str = "1.0.0"

    @property
    def num_entries(self) -> int:
        return len(self.entries)

    def get_entry(self, query: str) -> Optional[GroundTruthEntry]:
        for entry in self.entries:
            if entry.query == query:
                return entry
        return None

    def add_entry(self, entry: GroundTruthEntry) -> None:
        if self.get_entry(entry.query):
            raise GroundTruthError(f"Entry for query '{entry.query}' already exists")
        self.entries.append(entry)

    def remove_entry(self, query: str) -> bool:
        for i, entry in enumerate(self.entries):
            if entry.query == query:
                self.entries.pop(i)
                return True
        return False

    def merge(self, other: GroundTruthSet) -> None:
        for entry in other.entries:
            if not self.get_entry(entry.query):
                self.entries.append(entry)

    def filter_by_category(self, category: str) -> GroundTruthSet:
        return GroundTruthSet(
            name=f"{self.name}_{category}",
            entries=[
                e for e in self.entries
                if e.metadata.get("category") == category
            ],
            version=self.version,
        )


class GroundTruthValidator:
    @staticmethod
    def validate_answer(
        actual: str,
        expected: str,
        case_sensitive: bool = False,
    ) -> bool:
        if case_sensitive:
            return actual.strip() == expected.strip()
        return actual.strip().lower() == expected.strip().lower()

    @staticmethod
    def validate_citations(
        actual: list[str],
        expected: list[str],
    ) -> dict[str, Any]:
        actual_set = set(a.lower().strip() for a in actual)
        expected_set = set(e.lower().strip() for e in expected)
        return {
            "matched": list(actual_set & expected_set),
            "missing": list(expected_set - actual_set),
            "extra": list(actual_set - expected_set),
            "precision": len(actual_set & expected_set) / len(actual_set) if actual_set else 0.0,
            "recall": len(actual_set & expected_set) / len(expected_set) if expected_set else 0.0,
        }

    @staticmethod
    def validate_medications(
        actual: list[str],
        expected: list[str],
    ) -> dict[str, Any]:
        actual_set = set(a.lower().strip() for a in actual)
        expected_set = set(e.lower().strip() for e in expected)
        return {
            "matched": list(actual_set & expected_set),
            "missing": list(expected_set - actual_set),
            "extra": list(actual_set - expected_set),
            "accuracy": len(actual_set & expected_set) / len(expected_set) if expected_set else 0.0,
        }

    @staticmethod
    def validate_diagnoses(
        actual: list[str],
        expected: list[str],
    ) -> dict[str, Any]:
        return GroundTruthValidator.validate_medications(actual, expected)
