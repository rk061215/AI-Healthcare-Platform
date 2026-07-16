from __future__ import annotations

from dataclasses import dataclass, field

from app.document_pipeline.exceptions import PipelineConfigurationError


@dataclass
class DocumentPipelineConfig:
    chunker_type: str = "recursive"
    chunk_size: int = 500
    chunk_overlap: int = 50
    max_chunk_size: int = 2000
    min_chunk_size: int = 50
    supported_languages: list[str] = field(default_factory=lambda: ["en"])
    default_language: str = "en"
    max_document_length: int = 100_000
    enable_classification: bool = True
    enable_metadata: bool = True
    enable_versioning: bool = True

    def __post_init__(self) -> None:
        valid_types = ["fixed", "recursive", "semantic", "medical_section", "sentence"]
        if self.chunker_type not in valid_types:
            raise PipelineConfigurationError(
                f"Invalid chunker_type '{self.chunker_type}'. "
                f"Must be one of {valid_types}"
            )
        if self.chunk_size < self.min_chunk_size:
            raise PipelineConfigurationError(
                f"chunk_size ({self.chunk_size}) must be >= min_chunk_size ({self.min_chunk_size})"
            )
        if self.chunk_overlap >= self.chunk_size:
            raise PipelineConfigurationError(
                f"chunk_overlap ({self.chunk_overlap}) must be < chunk_size ({self.chunk_size})"
            )
        if self.chunk_size > self.max_chunk_size:
            raise PipelineConfigurationError(
                f"chunk_size ({self.chunk_size}) must be <= max_chunk_size ({self.max_chunk_size})"
            )
