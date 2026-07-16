from __future__ import annotations

import pytest

from app.evaluation.ground_truth import GroundTruthEntry, GroundTruthSet, GroundTruthValidator
from app.evaluation.exceptions import GroundTruthError


class TestGroundTruthEntry:
    def test_default_values(self) -> None:
        entry = GroundTruthEntry(query="test", expected_answer="answer")
        assert entry.query == "test"
        assert entry.expected_answer == "answer"
        assert entry.expected_citations == []
        assert entry.expected_retrieved_docs == []


class TestGroundTruthSet:
    def test_num_entries(self) -> None:
        gt = GroundTruthSet(name="test")
        assert gt.num_entries == 0
        gt.entries.append(GroundTruthEntry(query="q", expected_answer="a"))
        assert gt.num_entries == 1

    def test_get_entry(self) -> None:
        gt = GroundTruthSet(name="test")
        entry = GroundTruthEntry(query="q1", expected_answer="a1")
        gt.entries.append(entry)
        assert gt.get_entry("q1") is entry
        assert gt.get_entry("nonexistent") is None

    def test_add_entry(self) -> None:
        gt = GroundTruthSet(name="test")
        entry = GroundTruthEntry(query="q1", expected_answer="a1")
        gt.add_entry(entry)
        assert gt.num_entries == 1

    def test_add_duplicate_entry_raises(self) -> None:
        gt = GroundTruthSet(name="test")
        gt.add_entry(GroundTruthEntry(query="q1", expected_answer="a1"))
        with pytest.raises(GroundTruthError):
            gt.add_entry(GroundTruthEntry(query="q1", expected_answer="a2"))

    def test_remove_entry(self) -> None:
        gt = GroundTruthSet(name="test")
        gt.add_entry(GroundTruthEntry(query="q1", expected_answer="a1"))
        assert gt.remove_entry("q1") is True
        assert gt.num_entries == 0
        assert gt.remove_entry("nonexistent") is False

    def test_merge(self) -> None:
        gt1 = GroundTruthSet(name="a")
        gt2 = GroundTruthSet(name="b")
        gt1.add_entry(GroundTruthEntry(query="q1", expected_answer="a1"))
        gt2.add_entry(GroundTruthEntry(query="q2", expected_answer="a2"))
        gt1.merge(gt2)
        assert gt1.num_entries == 2

    def test_merge_duplicates_not_added(self) -> None:
        gt1 = GroundTruthSet(name="a")
        gt2 = GroundTruthSet(name="b")
        gt1.add_entry(GroundTruthEntry(query="q1", expected_answer="a1"))
        gt2.add_entry(GroundTruthEntry(query="q1", expected_answer="a2"))
        gt1.merge(gt2)  # q1 already in gt1, should not add duplicate
        assert gt1.num_entries == 1

    def test_filter_by_category(self) -> None:
        gt = GroundTruthSet(name="all")
        gt.add_entry(GroundTruthEntry(query="q1", expected_answer="a1", metadata={"category": "medication"}))
        gt.add_entry(GroundTruthEntry(query="q2", expected_answer="a2", metadata={"category": "diagnosis"}))
        filtered = gt.filter_by_category("medication")
        assert filtered.num_entries == 1
        assert filtered.entries[0].query == "q1"


class TestGroundTruthValidator:
    def test_validate_answer_case_sensitive(self) -> None:
        assert GroundTruthValidator.validate_answer("Metformin", "Metformin", case_sensitive=True) is True
        assert GroundTruthValidator.validate_answer("metformin", "Metformin", case_sensitive=True) is False

    def test_validate_answer_case_insensitive(self) -> None:
        assert GroundTruthValidator.validate_answer("METFORMIN", "metformin") is True
        assert GroundTruthValidator.validate_answer("Metformin", "Metformin") is True
        assert GroundTruthValidator.validate_answer("Aspirin", "Metformin") is False

    def test_validate_citations(self) -> None:
        result = GroundTruthValidator.validate_citations(
            actual=["a", "b", "c"],
            expected=["a", "b", "d"],
        )
        assert result["precision"] == 2.0 / 3.0
        assert result["recall"] == 2.0 / 3.0
        assert "c" in result["extra"]
        assert "d" in result["missing"]

    def test_validate_citations_empty_actual(self) -> None:
        result = GroundTruthValidator.validate_citations([], ["a"])
        assert result["precision"] == 0.0

    def test_validate_citations_empty_expected(self) -> None:
        result = GroundTruthValidator.validate_citations(["a"], [])
        assert result["recall"] == 0.0

    def test_validate_medications(self) -> None:
        result = GroundTruthValidator.validate_medications(
            actual=["metformin", "insulin"],
            expected=["metformin", "aspirin"],
        )
        assert result["accuracy"] == 0.5
        assert "metformin" in result["matched"]
        assert "aspirin" in result["missing"]
        assert "insulin" in result["extra"]
