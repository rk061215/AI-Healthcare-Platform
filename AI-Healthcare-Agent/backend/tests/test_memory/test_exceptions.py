from __future__ import annotations

import pytest

from app.memory.exceptions import (
    ExpiryPolicyViolationError,
    MemoryError,
    MemoryExpiredError,
    MemoryExtractionError,
    MemoryFullError,
    MemoryNotFoundError,
    MemoryPruningError,
    MemoryRetrievalError,
    MemoryStoreError,
    MemorySummarizationError,
    MemoryTypeError,
    PolicyViolationError,
    PrivacyPolicyViolationError,
    RetentionPolicyViolationError,
    SessionNotFoundError,
)


class TestMemoryExceptions:
    def test_memory_error_base(self) -> None:
        assert issubclass(MemoryError, Exception)

    def test_all_exceptions_inherit(self) -> None:
        for exc in [
            MemoryStoreError, MemoryNotFoundError, MemoryTypeError,
            MemoryFullError, MemoryExpiredError, MemoryExtractionError,
            MemoryRetrievalError, MemorySummarizationError, MemoryPruningError,
            PolicyViolationError, SessionNotFoundError,
        ]:
            assert issubclass(exc, MemoryError)

    def test_policy_exceptions(self) -> None:
        assert issubclass(RetentionPolicyViolationError, PolicyViolationError)
        assert issubclass(PrivacyPolicyViolationError, PolicyViolationError)
        assert issubclass(ExpiryPolicyViolationError, PolicyViolationError)

    def test_all_raisable(self) -> None:
        with pytest.raises(MemoryError):
            raise MemoryNotFoundError("test")
        with pytest.raises(MemoryError):
            raise MemoryFullError("test")
        with pytest.raises(PolicyViolationError):
            raise PrivacyPolicyViolationError("test")
        with pytest.raises(MemoryError):
            raise SessionNotFoundError("test")
