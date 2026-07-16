class OCRError(Exception):
    """Base exception for all OCR errors."""


class OCREngineNotFoundError(OCRError):
    """Raised when a requested OCR engine is not registered."""


class OCRImageUnreadableError(OCRError):
    """Raised when an image cannot be read or decoded."""


class OCRProcessingError(OCRError):
    """Raised when the OCR engine fails to process a document."""


class OCRTimeoutError(OCRError):
    """Raised when OCR processing exceeds the configured timeout."""


class OCRRetryExhaustedError(OCRError):
    """Raised after all OCR retry attempts are exhausted."""


class OCRLanguageNotSupportedError(OCRError):
    """Raised when the requested language is not supported by the engine."""


class OCRPageSplitError(OCRError):
    """Raised when page splitting fails for multi-page documents."""
