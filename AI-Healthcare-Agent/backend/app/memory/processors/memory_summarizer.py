from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.memory.base_memory import BaseMemoryStore
from app.memory.exceptions import MemorySummarizationError
from app.memory.models import MemoryEntry, MemoryQuery, MemorySummary, MemoryType
from app.memory.types.conversation_memory import ConversationMemory


@dataclass
class SummarizationResult:
    summary: Optional[MemorySummary]
    entries_consumed: int = 0
    summary_text: str = ""


class MemorySummarizer:
    def __init__(self, store: BaseMemoryStore) -> None:
        self._store = store
        self._conversation = ConversationMemory()

    def summarize_conversation(
        self,
        session_id: str,
        max_turns: int = 20,
    ) -> SummarizationResult:
        try:
            query = MemoryQuery(
                session_id=session_id,
                memory_type=MemoryType.CONVERSATION,
                limit=max_turns,
            )
            entries = self._store.search(query)
            if not entries:
                return SummarizationResult(summary=None, entries_consumed=0, summary_text="")
            summary_text = self._conversation.summarize_turns(entries)
            memory_summary = MemorySummary(
                session_id=session_id,
                memory_type=MemoryType.CONVERSATION,
                summary_text=summary_text,
                entry_count=len(entries),
            )
            return SummarizationResult(
                summary=memory_summary,
                entries_consumed=len(entries),
                summary_text=summary_text,
            )
        except Exception as e:
            raise MemorySummarizationError(f"Failed to summarize conversation: {e}")

    def summarize_all(
        self,
        session_id: str,
    ) -> dict[str, SummarizationResult]:
        results: dict[str, SummarizationResult] = {}
        for memory_type in MemoryType:
            try:
                query = MemoryQuery(
                    session_id=session_id,
                    memory_type=memory_type,
                    limit=50,
                )
                entries = self._store.search(query)
                if entries:
                    texts = [e.content.get("query") or e.content.get("document_id") or str(e.memory_id) for e in entries]
                    summary_text = "\n".join(texts[:10])
                    memory_summary = MemorySummary(
                        session_id=session_id,
                        memory_type=memory_type,
                        summary_text=summary_text,
                        entry_count=len(entries),
                    )
                    results[memory_type.value] = SummarizationResult(
                        summary=memory_summary,
                        entries_consumed=len(entries),
                        summary_text=summary_text,
                    )
            except Exception:
                continue
        return results
