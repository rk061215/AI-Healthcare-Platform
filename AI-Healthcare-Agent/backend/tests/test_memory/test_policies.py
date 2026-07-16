from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.memory.exceptions import (
    ExpiryPolicyViolationError,
    PrivacyPolicyViolationError,
    RetentionPolicyViolationError,
)
from app.memory.models import MemoryEntry, MemoryType
from app.memory.policies.expiry_policy import ExpiryPolicy
from app.memory.policies.privacy_policy import PrivacyPolicy
from app.memory.policies.retention_policy import RetentionPolicy


class TestRetentionPolicy:
    def test_check_retention_within_limit(self) -> None:
        policy = RetentionPolicy(retention_days=30)
        entry = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={})
        assert policy.check_retention(entry) is True

    def test_check_retention_expired(self) -> None:
        policy = RetentionPolicy(retention_days=30)
        entry = MemoryEntry(
            memory_id="m1", session_id="s1",
            memory_type=MemoryType.CONVERSATION,
            content={},
            created_at=datetime.utcnow() - timedelta(days=60),
        )
        assert policy.check_retention(entry) is False

    def test_check_retention_with_expiry(self) -> None:
        policy = RetentionPolicy(retention_days=30)
        entry = MemoryEntry(
            memory_id="m1", session_id="s1",
            memory_type=MemoryType.CONVERSATION,
            content={},
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        assert policy.check_retention(entry) is False

    def test_can_store_patient_context(self) -> None:
        policy = RetentionPolicy()
        entry = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.PATIENT_CONTEXT, content={})
        assert policy.can_store(entry) is True

    def test_exceeds_session_limit(self) -> None:
        policy = RetentionPolicy(max_sessions_per_patient=5)
        assert policy.exceeds_session_limit(5) is True
        assert policy.exceeds_session_limit(4) is False

    def test_validate_raises(self) -> None:
        policy = RetentionPolicy(retention_days=1)
        entry = MemoryEntry(
            memory_id="m1", session_id="s1",
            memory_type=MemoryType.CONVERSATION,
            content={},
            created_at=datetime.utcnow() - timedelta(days=10),
        )
        with pytest.raises(RetentionPolicyViolationError):
            policy.validate(entry)

    def test_validate_passes(self) -> None:
        policy = RetentionPolicy(retention_days=30)
        entry = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={})
        policy.validate(entry)  # should not raise

    def test_filter_retention(self) -> None:
        policy = RetentionPolicy(retention_days=30)
        fresh = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={})
        old = MemoryEntry(
            memory_id="m2", session_id="s1",
            memory_type=MemoryType.CONVERSATION,
            content={},
            created_at=datetime.utcnow() - timedelta(days=60),
        )
        result = policy.filter_retention([fresh, old])
        assert len(result) == 1


class TestPrivacyPolicy:
    def test_non_strict_no_op(self) -> None:
        policy = PrivacyPolicy(strict_mode=False)
        entry = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={"patient_id": "pat1"})
        result = policy.apply(entry)
        assert result.content["patient_id"] == "pat1"

    def test_strict_removes_restricted(self) -> None:
        policy = PrivacyPolicy(strict_mode=True)
        entry = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={"patient_id": "pat1", "query": "test"})
        result = policy.apply(entry)
        assert "patient_id" not in result.content
        assert result.content["query"] == "test"

    def test_check_field_access(self) -> None:
        policy = PrivacyPolicy()
        assert policy.check_field_access("query") is True
        assert policy.check_field_access("patient_id") is False

    def test_validate_access_restricted(self) -> None:
        policy = PrivacyPolicy(strict_mode=True)
        entry = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={"patient_id": "pat1"})
        with pytest.raises(PrivacyPolicyViolationError):
            policy.validate_access(entry)

    def test_validate_access_allowed(self) -> None:
        policy = PrivacyPolicy(strict_mode=True)
        entry = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={"query": "test"})
        policy.validate_access(entry)  # should not raise

    def test_allowed_fields(self) -> None:
        policy = PrivacyPolicy(allowed_fields=("query", "answer"))
        assert "patient_id" not in policy.allowed_fields

    def test_restricted_fields(self) -> None:
        policy = PrivacyPolicy(restricted_fields=("ssn", "dob"))
        entry = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={"query": "test", "ssn": "123-45-6789"})
        result = policy.apply(entry)  # non-strict, no op
        assert result.content["ssn"] == "123-45-6789"


class TestExpiryPolicy:
    def test_default_ttl(self) -> None:
        policy = ExpiryPolicy(default_ttl_seconds=1800)
        assert policy.default_ttl_seconds == 1800

    def test_get_ttl_by_type(self) -> None:
        policy = ExpiryPolicy()
        assert policy.get_ttl(MemoryType.CONVERSATION) == 3600
        assert policy.get_ttl(MemoryType.PATIENT_CONTEXT) == 86400

    def test_is_expired(self) -> None:
        policy = ExpiryPolicy()
        entry = MemoryEntry(
            memory_id="m1", session_id="s1",
            memory_type=MemoryType.CONVERSATION,
            content={},
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        assert policy.is_expired(entry) is True

    def test_not_expired(self) -> None:
        policy = ExpiryPolicy()
        entry = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={})
        assert policy.is_expired(entry) is False

    def test_set_expiry(self) -> None:
        policy = ExpiryPolicy(default_ttl_seconds=3600)
        entry = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={})
        updated = policy.set_expiry(entry)
        assert updated.expires_at is not None

    def test_filter_expired(self) -> None:
        policy = ExpiryPolicy()
        fresh = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={})
        expired = MemoryEntry(
            memory_id="m2", session_id="s1",
            memory_type=MemoryType.CONVERSATION,
            content={},
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        result = policy.filter_expired([fresh, expired])
        assert len(result) == 1

    def test_validate_raises(self) -> None:
        policy = ExpiryPolicy()
        entry = MemoryEntry(
            memory_id="m1", session_id="s1",
            memory_type=MemoryType.CONVERSATION,
            content={},
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        with pytest.raises(ExpiryPolicyViolationError):
            policy.validate(entry)

    def test_validate_passes(self) -> None:
        policy = ExpiryPolicy()
        entry = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={})
        policy.validate(entry)  # should not raise
