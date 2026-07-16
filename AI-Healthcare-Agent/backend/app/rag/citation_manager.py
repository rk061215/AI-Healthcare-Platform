from __future__ import annotations

from typing import Any, Optional

from app.rag.exceptions import CitationError
from app.rag.models import CitationBlock, CitationEntry, RAGContext

CITATION_PATTERN_TEMPLATE = "[citation:{id}]"


class CitationManager:
    """Manages citation formatting, grounding, and validation.

    Responsibilities:
    - Extract unique citation entries from RAG context
    - Format citations as a structured block
    - Validate that citations in responses are grounded in retrieved documents
    - Prevent hallucinated citations
    """

    def __init__(self, include_scores: bool = False) -> None:
        self._include_scores = include_scores

    def extract_citations(self, context: RAGContext) -> CitationBlock:
        """Extract unique citation entries from RAG context fragments.

        Deduplicates by chunk_id and assigns sequential citation IDs.
        """
        if not context.citations:
            return CitationBlock()

        seen: set[str] = set()
        entries: list[CitationEntry] = []
        citation_id = 1

        for raw in context.citations:
            chunk_id = raw.get("chunk_id", "")
            if not chunk_id or chunk_id in seen:
                continue
            seen.add(chunk_id)

            snippet = self._extract_snippet(context, chunk_id)

            entries.append(
                CitationEntry(
                    citation_id=citation_id,
                    document_id=raw.get("document_id", ""),
                    report_id=raw.get("report_id"),
                    chunk_id=chunk_id,
                    page=raw.get("page"),
                    section=raw.get("section"),
                    source=raw.get("source", "ocr"),
                    text_snippet=snippet,
                    score=raw.get("score", 0.0),
                )
            )
            citation_id += 1

        block_text = self._format_block(entries)

        return CitationBlock(
            citations=entries,
            formatted_block=block_text,
            citation_count=len(entries),
        )

    def format_inline_citation(self, citation_id: int) -> str:
        """Generate an inline citation marker for use in response text."""
        return CITATION_PATTERN_TEMPLATE.format(id=citation_id)

    def has_hallucinated_citations(
        self, response: str, citations: CitationBlock
    ) -> list[dict[str, Any]]:
        """Check for hallucinated citations in the response.

        Returns a list of hallucinated citation references found in the
        response text that do not match any valid citation.
        """
        import re

        if not citations.citations:
            return []

        valid_ids = {str(c.citation_id) for c in citations.citations}
        hallucinated: list[dict[str, Any]] = []

        pattern = re.compile(r"\[citation:(\d+)\]")
        for match in pattern.finditer(response):
            cited_id = match.group(1)
            if cited_id not in valid_ids:
                hallucinated.append({
                    "cited_id": cited_id,
                    "position": match.start(),
                    "text": match.group(0),
                })

        return hallucinated

    def validate_response_grounding(
        self, response: str, citations: CitationBlock
    ) -> dict[str, Any]:
        """Validate that all citations in the response are grounded.

        Returns a dict with:
        - is_grounded: bool
        - total_citations_in_response: int
        - hallucinated_count: int
        - hallucinated_refs: list
        """
        hallucinated = self.has_hallucinated_citations(response, citations)

        total = 0
        import re
        total = len(re.findall(r"\[citation:\d+\]", response))

        return {
            "is_grounded": len(hallucinated) == 0,
            "total_citations_in_response": total,
            "hallucinated_count": len(hallucinated),
            "hallucinated_refs": hallucinated,
        }

    def _format_block(self, entries: list[CitationEntry]) -> str:
        if not entries:
            return ""

        lines = ["\n---\n**Sources**"]
        for entry in entries:
            parts = [f"[{entry.citation_id}] Document: {entry.document_id}"]
            if entry.report_id:
                parts.append(f"Report: {entry.report_id}")
            if entry.section:
                parts.append(f"Section: {entry.section}")
            if entry.page is not None:
                parts.append(f"Page: {entry.page}")
            if entry.source:
                parts.append(f"Source: {entry.source}")
            if self._include_scores and entry.score > 0:
                parts.append(f"Relevance: {entry.score:.3f}")
            lines.append(" | ".join(parts))

        return "\n".join(lines)

    def _extract_snippet(
        self, context: RAGContext, chunk_id: str
    ) -> str:
        for frag in context.fragments:
            citation = frag.get("citation", {})
            if citation.get("chunk_id") == chunk_id:
                text = frag.get("text", "")
                return text[:200] + "..." if len(text) > 200 else text
        return ""
