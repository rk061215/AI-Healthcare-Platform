"""Prompt management system for RAG.

This module provides the RAG prompt management layer:
- PromptCache: TTL+LRU cache for loaded prompts
- RAGPromptLoader: Loads prompts with version tracking
- PromptManager: Central registry for prompt discovery and management

Underlying prompt templates are loaded from backend/prompts/ as .md files
via app.core.prompt_loader (the core loading engine).
"""

from app.prompts.cache import PromptCache
from app.prompts.loader import RAGPrompt, RAGPromptLoader, PromptVersion
from app.prompts.manager import PromptManager

__all__ = [
    "PromptCache",
    "PromptVersion",
    "RAGPrompt",
    "RAGPromptLoader",
    "PromptManager",
]
