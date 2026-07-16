from __future__ import annotations

import pytest

from app.memory.models import MemoryEntry, MemoryQuery, MemoryType
from app.memory.processors.memory_extractor import MemoryExtractor
from app.memory.processors.memory_pruner import MemoryPruner
from app.memory.processors.memory_retriever import MemoryRetriever
from app.memory.processors.memory_summarizer import MemorySummarizer
from app.memory.stores.in_memory_store import InMemoryStore
from app.memory.types.conversation_memory import ConversationMemory


class TestMemoryExtractor:
    def test_extract_from_chat(self) -> None:
        extractor = MemoryExtractor()
        entry = extractor.extract_from_chat("s1", "What meds?", "Metformin", "medication", 0.9, 1)
        assert entry.session_id == "s1"
        assert entry.content["query"] == "What meds?"
        assert entry.memory_type == MemoryType.CONVERSATION

    def test_extract_from_document(self) -> None:
        extractor = MemoryExtractor()
        entry = extractor.extract_from_document("s1", "doc1", "pat1", "rep1", "lab_report", ["glucose"])
        assert entry.memory_type == MemoryType.DOCUMENT_CONTEXT
        assert entry.content["document_id"] == "doc1"
        assert entry.importance == 0.8

    def test_extract_patient_context(self) -> None:
        extractor = MemoryExtractor()
        entry = extractor.extract_patient_context("s1", "pat1", "fr", "doc1")
        assert entry.memory_type == MemoryType.PATIENT_CONTEXT
        assert entry.content["language"] == "fr"
        assert entry.importance == 0.9

    def test_extract_preference(self) -> None:
        extractor = MemoryExtractor()
        entry = extractor.extract_preference("s1", "ui", "theme", "dark", "display")
        assert entry.memory_type == MemoryType.PREFERENCE

    def test_extract_tool_memory(self) -> None:
        extractor = MemoryExtractor()
        entry = extractor.extract_tool_memory("s1", "appointment", "booked", {"date": "2026-07-20"})
        assert entry.memory_type == MemoryType.TOOL
        assert entry.content["result"]["date"] == "2026-07-20"


class TestMemoryRetriever:
    def test_retrieve_by_session(self) -> None:
        store = InMemoryStore()
        entry = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={})
        store.store(entry)
        retriever = MemoryRetriever(store)
        results = retriever.retrieve("s1")
        assert len(results) == 1

    def test_retrieve_by_type(self) -> None:
        store = InMemoryStore()
        e1 = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={})
        store.store(e1)
        retriever = MemoryRetriever(store)
        results = retriever.retrieve_conversation("s1")
        assert len(results) == 1

    def test_retrieve_document_context(self) -> None:
        store = InMemoryStore()
        from app.memory.types.document_context import DocumentContext
        dc = DocumentContext()
        entry = dc.create_entry("s1", "doc1", "pat1")
        store.store(entry)
        retriever = MemoryRetriever(store)
        result = retriever.retrieve_document_context("s1")
        assert result is not None
        assert result.content["document_id"] == "doc1"

    def test_retrieve_patient_context_empty(self) -> None:
        store = InMemoryStore()
        retriever = MemoryRetriever(store)
        assert retriever.retrieve_patient_context("nonexistent") is None

    def test_retrieve_with_min_importance(self) -> None:
        store = InMemoryStore()
        e1 = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={}, importance=0.9)
        e2 = MemoryEntry(memory_id="m2", session_id="s1", memory_type=MemoryType.CONVERSATION, content={}, importance=0.1)
        store.store(e1)
        store.store(e2)
        retriever = MemoryRetriever(store)
        results = retriever.retrieve("s1", min_importance=0.5)
        assert len(results) == 1


class TestMemorySummarizer:
    def test_summarize_conversation(self) -> None:
        store = InMemoryStore()
        from app.memory.types.conversation_memory import ConversationMemory
        cm = ConversationMemory()
        e1 = cm.create_entry("s1", 1, "What meds?", "Metformin")
        e2 = cm.create_entry("s1", 2, "Any allergies?", "None")
        store.store(e1)
        store.store(e2)
        summarizer = MemorySummarizer(store)
        result = summarizer.summarize_conversation("s1")
        assert result.entries_consumed == 2
        assert "What meds?" in result.summary_text
        assert result.summary is not None
        assert result.summary.memory_type == MemoryType.CONVERSATION

    def test_summarize_conversation_empty(self) -> None:
        store = InMemoryStore()
        summarizer = MemorySummarizer(store)
        result = summarizer.summarize_conversation("empty_session")
        assert result.entries_consumed == 0
        assert result.summary is None

    def test_summarize_all(self) -> None:
        store = InMemoryStore()
        cm = ConversationMemory()
        e1 = cm.create_entry("s1", 1, "q", "a")
        store.store(e1)
        summarizer = MemorySummarizer(store)
        results = summarizer.summarize_all("s1")
        assert "conversation" in results


class TestMemoryPruner:
    def test_prune_session(self) -> None:
        store = InMemoryStore()
        for i in range(10):
            e = MemoryEntry(
                memory_id=f"m{i}", session_id="s1",
                memory_type=MemoryType.CONVERSATION,
                content={},
                importance=0.1 if i < 5 else 0.9,
            )
            store.store(e)
        pruner = MemoryPruner(store, importance_threshold=0.5, max_count=10)
        report = pruner.prune_session("s1")
        assert report.removed_count == 5
        assert report.total_before == 10
        assert report.total_after == 5

    def test_prune_session_max_count(self) -> None:
        store = InMemoryStore()
        for i in range(10):
            e = MemoryEntry(
                memory_id=f"m{i}", session_id="s1",
                memory_type=MemoryType.CONVERSATION,
                content={},
                importance=0.9,
            )
            store.store(e)
        pruner = MemoryPruner(store, importance_threshold=0.0, max_count=3)
        report = pruner.prune_session("s1")
        assert report.removed_count == 7
        assert report.total_after == 3

    def test_prune_expired(self) -> None:
        from datetime import datetime, timedelta
        store = InMemoryStore()
        expired = MemoryEntry(
            memory_id="m1", session_id="s1",
            memory_type=MemoryType.CONVERSATION,
            content={},
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        active = MemoryEntry(
            memory_id="m2", session_id="s1",
            memory_type=MemoryType.CONVERSATION,
            content={},
        )
        store.store(expired)
        store.store(active)
        pruner = MemoryPruner(store)
        report = pruner.prune_expired()
        assert report.removed_count == 1

    def test_prune_report_repr(self) -> None:
        from app.memory.processors.memory_pruner import PruningReport
        report = PruningReport()
        report.removed_count = 5
        assert "removed=5" in repr(report)
