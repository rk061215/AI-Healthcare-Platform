from __future__ import annotations

import re
from typing import Optional

from app.document_pipeline.config import DocumentPipelineConfig
from app.document_pipeline.exceptions import DocumentCleanError, EmptyDocumentError
from app.document_pipeline.interfaces import DocumentCleaner


class DefaultDocumentCleaner(DocumentCleaner):
    """Default text cleaner for OCR output.

    Performs:
    1. Strip leading/trailing whitespace
    2. Collapse multiple newlines to at most two
    3. Remove null bytes
    4. Normalize unicode whitespace
    5. Remove excessive whitespace within lines
    6. Strip page separator artifacts
    """

    def clean(self, text: str, config: Optional[DocumentPipelineConfig] = None) -> str:
        if not text or not text.strip():
            raise EmptyDocumentError("Document is empty after cleaning")

        try:
            cleaned = text
            cleaned = self._remove_null_bytes(cleaned)
            cleaned = self._normalize_newlines(cleaned)
            cleaned = self._normalize_whitespace(cleaned)
            cleaned = self._strip_page_separators(cleaned)
            cleaned = self._remove_non_breaking_spaces(cleaned)
            cleaned = cleaned.strip()

            if not cleaned:
                raise EmptyDocumentError("Document is empty after cleaning")

            if config and len(cleaned) > config.max_document_length:
                cleaned = cleaned[:config.max_document_length]

            return cleaned
        except EmptyDocumentError:
            raise
        except Exception as exc:
            raise DocumentCleanError(f"Failed to clean document: {exc}") from exc

    def _remove_null_bytes(self, text: str) -> str:
        return text.replace("\x00", "")

    def _normalize_newlines(self, text: str) -> str:
        result = text.replace("\r\n", "\n")
        result = result.replace("\r", "\n")
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result

    def _normalize_whitespace(self, text: str) -> str:
        lines = text.split("\n")
        normalized = []
        for line in lines:
            line = re.sub(r"[ \t]+", " ", line)
            normalized.append(line)
        return "\n".join(normalized)

    def _strip_page_separators(self, text: str) -> str:
        result = re.sub(r"(?i)-+\s*page\s*\d+\s*-+", "\n", text)
        result = re.sub(r"(?im)^\s*---+\s*page\s*\d+\s*---+\s*$", "\n", result)
        result = re.sub(r"(?im)^\s*\f\s*$", "\n", result)
        return result

    def _remove_non_breaking_spaces(self, text: str) -> str:
        return text.replace("\xa0", " ")
