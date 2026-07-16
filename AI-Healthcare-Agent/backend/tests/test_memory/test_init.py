from __future__ import annotations

import app.memory


class TestMemoryExports:
    def test_core_classes_exported(self) -> None:
        assert hasattr(app.memory, "MemoryConfig")
        assert hasattr(app.memory, "MemoryService")
        assert hasattr(app.memory, "MemoryFactory")
        assert hasattr(app.memory, "MemoryRegistry")
        assert hasattr(app.memory, "get_global_registry")

    def test_models_exported(self) -> None:
        assert hasattr(app.memory, "MemoryEntry")
        assert hasattr(app.memory, "MemoryType")
        assert hasattr(app.memory, "MemoryQuery")
        assert hasattr(app.memory, "ConversationMemoryData")
        assert hasattr(app.memory, "DocumentContextData")
        assert hasattr(app.memory, "PatientContextData")
        assert hasattr(app.memory, "PreferenceMemoryData")
        assert hasattr(app.memory, "ToolMemoryData")

    def test_stores_exported(self) -> None:
        assert hasattr(app.memory, "InMemoryStore")

    def test_types_exported(self) -> None:
        assert hasattr(app.memory, "ConversationMemory")
        assert hasattr(app.memory, "DocumentContext")
        assert hasattr(app.memory, "PatientContext")
        assert hasattr(app.memory, "PreferenceMemory")
        assert hasattr(app.memory, "ToolMemory")

    def test_processors_exported(self) -> None:
        assert hasattr(app.memory, "MemoryExtractor")
        assert hasattr(app.memory, "MemoryRetriever")
        assert hasattr(app.memory, "MemorySummarizer")
        assert hasattr(app.memory, "MemoryPruner")

    def test_policies_exported(self) -> None:
        assert hasattr(app.memory, "RetentionPolicy")
        assert hasattr(app.memory, "PrivacyPolicy")
        assert hasattr(app.memory, "ExpiryPolicy")

    def test_exceptions_exported(self) -> None:
        assert hasattr(app.memory, "MemoryError")
        assert hasattr(app.memory, "MemoryNotFoundError")
        assert hasattr(app.memory, "MemoryFullError")
        assert hasattr(app.memory, "PolicyViolationError")
        assert hasattr(app.memory, "RetentionPolicyViolationError")
        assert hasattr(app.memory, "PrivacyPolicyViolationError")
        assert hasattr(app.memory, "ExpiryPolicyViolationError")
        assert hasattr(app.memory, "SessionNotFoundError")

    def test_all_exported(self) -> None:
        assert len(app.memory.__all__) > 30
