from __future__ import annotations

from typing import Any

from app.validation.dataset.ground_truth import GroundTruthSet


class ValidationResult:
    def __init__(self) -> None:
        self.is_valid: bool = True
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def add_error(self, msg: str) -> None:
        self.is_valid = False
        self.errors.append(msg)

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }


class DatasetValidator:
    MIN_ENTRIES_PER_DOCUMENT = 1
    MAX_QUESTION_LENGTH = 2000
    MIN_ANSWER_LENGTH = 1
    MAX_ANSWER_LENGTH = 10000

    @staticmethod
    def validate(gt_set: GroundTruthSet) -> ValidationResult:
        result = ValidationResult()

        if not gt_set.name:
            result.add_error("Dataset name is required")

        if not gt_set.documents:
            result.add_error("Dataset must contain at least one document")

        seen_ids: set[str] = set()
        for doc in gt_set.documents:
            if not doc.document_id:
                result.add_error("Each document must have a document_id")
                continue
            if doc.document_id in seen_ids:
                result.add_warning(f"Duplicate document_id: {doc.document_id}")
            seen_ids.add(doc.document_id)

            if not doc.document_text:
                result.add_warning(f"Document {doc.document_id} has empty document_text")

            if len(doc.entries) < DatasetValidator.MIN_ENTRIES_PER_DOCUMENT:
                result.add_warning(
                    f"Document {doc.document_id} has fewer than "
                    f"{DatasetValidator.MIN_ENTRIES_PER_DOCUMENT} entries"
                )

            seen_questions: set[str] = set()
            for entry in doc.entries:
                if not entry.question:
                    result.add_error(
                        f"Document {doc.document_id} has an entry with empty question"
                    )
                if len(entry.question) > DatasetValidator.MAX_QUESTION_LENGTH:
                    result.add_warning(
                        f"Document {doc.document_id} has an overly long question "
                        f"({len(entry.question)} chars)"
                    )
                if entry.question in seen_questions:
                    result.add_warning(
                        f"Document {doc.document_id} has duplicate question: {entry.question[:60]}"
                    )
                seen_questions.add(entry.question)

                if not entry.expected_answer:
                    result.add_warning(
                        f"Document {doc.document_id} entry '{entry.question[:60]}' "
                        f"has empty expected_answer"
                    )
                if len(entry.expected_answer) > DatasetValidator.MAX_ANSWER_LENGTH:
                    result.add_warning(
                        f"Document {doc.document_id} entry has overly long expected_answer"
                    )

                if entry.expected_confidence < 0 or entry.expected_confidence > 1:
                    result.add_error(
                        f"Document {doc.document_id} entry has confidence "
                        f"out of range [0,1]: {entry.expected_confidence}"
                    )

        return result
