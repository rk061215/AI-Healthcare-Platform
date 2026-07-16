from __future__ import annotations

from typing import Optional

from app.context.exceptions import CitationError
from app.context.models import CitationInfo, ContextFragment


class CitationGenerator:
    """Generates and manages citation metadata for context fragments."""

    def __init__(self, include_citations: bool = True) -> None:
        self._include_citations = include_citations

    def extract_citations(
        self, fragments: list[ContextFragment]
    ) -> list[CitationInfo]:
        if not fragments:
            return []

        citations = []
        seen: set[str] = set()
        for frag in fragments:
            key = frag.citation.chunk_id
            if key not in seen:
                seen.add(key)
                citations.append(frag.citation)
        return citations

    def format_citation_block(self, citations: list[CitationInfo]) -> str:
        if not self._include_citations or not citations:
            return ""

        lines = ["\n---\n**Sources**"]
        for i, c in enumerate(citations, 1):
            parts = [f"[{i}] Document: {c.document_id}"]
            if c.report_id:
                parts.append(f"Report: {c.report_id}")
            if c.section:
                parts.append(f"Section: {c.section}")
            if c.page is not None:
                parts.append(f"Page: {c.page}")
            if c.source:
                parts.append(f"Source: {c.source}")
            lines.append(" | ".join(parts))

        return "\n".join(lines)

    def annotate_fragment(
        self, fragment: ContextFragment, index: int
    ) -> str:
        if not self._include_citations:
            return fragment.text

        c = fragment.citation
        prefix = f"[Source: {c.document_id}"
        if c.section:
            prefix += f", {c.section}"
        if c.page is not None:
            prefix += f", p.{c.page}"
        prefix += f"]\n"

        return prefix + fragment.text
