from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.document_pipeline.interfaces import VersionTracker


DOCUMENT_PIPELINE_VERSION = "1.0.0"
EXTRACTION_PIPELINE_VERSION = "1.0.0"
CHUNK_SCHEMA_VERSION = "1.0.0"
EMBEDDING_SCHEMA_VERSION = ""


@dataclass
class VersionInfo:
    document_version: str = DOCUMENT_PIPELINE_VERSION
    extraction_version: str = EXTRACTION_PIPELINE_VERSION
    schema_version: str = CHUNK_SCHEMA_VERSION
    embedding_version: str = EMBEDDING_SCHEMA_VERSION


class DefaultVersionTracker(VersionTracker):
    """Default version tracker using module-level constants.

    In the future this can be extended to read from config files,
    database, or remote version manifests.
    """

    def __init__(self, version_override: Optional[VersionInfo] = None) -> None:
        self._version = version_override or VersionInfo()

    def get_document_version(self) -> str:
        return self._version.document_version

    def get_extraction_version(self) -> str:
        return self._version.extraction_version

    def get_schema_version(self) -> str:
        return self._version.schema_version

    def get_embedding_version(self) -> str:
        return self._version.embedding_version
