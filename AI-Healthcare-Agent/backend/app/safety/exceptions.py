from __future__ import annotations


class SafetyError(Exception):
    """Base exception for safety layer errors."""


class UnsafeContentError(SafetyError):
    """Raised when content fails safety checks."""
