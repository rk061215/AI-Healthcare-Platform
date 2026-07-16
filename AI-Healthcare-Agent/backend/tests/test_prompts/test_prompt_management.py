"""Tests for the RAG Prompt Management System (Phase A)."""

import time
from pathlib import Path

import pytest

from app.prompts import PromptCache, PromptManager, PromptVersion, RAGPromptLoader


class TestPromptCache:
    def test_get_set(self):
        cache = PromptCache(maxsize=10, default_ttl_seconds=60)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_miss(self):
        cache = PromptCache(maxsize=10)
        assert cache.get("nonexistent") is None

    def test_ttl_expiry(self):
        cache = PromptCache(maxsize=10, default_ttl_seconds=0.01)
        cache.set("key1", "value1")
        time.sleep(0.02)
        assert cache.get("key1") is None

    def test_ttl_per_key(self):
        cache = PromptCache(maxsize=10, default_ttl_seconds=60)
        cache.set("short", "value", ttl_seconds=0.01)
        cache.set("long", "value", ttl_seconds=60)
        time.sleep(0.02)
        assert cache.get("short") is None
        assert cache.get("long") == "value"

    def test_lru_eviction(self):
        cache = PromptCache(maxsize=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.set("d", 4)
        assert cache.get("a") is None
        assert cache.get("d") == 4

    def test_lru_access_preserves(self):
        cache = PromptCache(maxsize=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.get("a")
        cache.set("d", 4)
        assert cache.get("a") == 1
        assert cache.get("b") is None

    def test_invalidate(self):
        cache = PromptCache(maxsize=10)
        cache.set("key1", "value1")
        cache.invalidate("key1")
        assert cache.get("key1") is None

    def test_clear(self):
        cache = PromptCache(maxsize=10)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.get("a")
        cache.get("b")
        cache.clear()
        assert cache.get("a") is None
        assert cache.stats["misses"] == 1
        assert cache.stats["hits"] == 0

    def test_stats(self):
        cache = PromptCache(maxsize=10)
        cache.set("k", "v")
        cache.get("k")
        cache.get("missing")
        stats = cache.stats
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5
        assert stats["size"] == 1

    def test_contains(self):
        cache = PromptCache(maxsize=10)
        cache.set("k", "v")
        assert "k" in cache
        assert "missing" not in cache

    def test_len(self):
        cache = PromptCache(maxsize=10)
        assert len(cache) == 0
        cache.set("a", 1)
        cache.set("b", 2)
        assert len(cache) == 2


class TestPromptVersion:
    def test_semver_parsing(self):
        v = PromptVersion("1.2.3", "abc123", {})
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3
        assert str(v) == "1.2.3"

    def test_malformed_version(self):
        v = PromptVersion("not-a-version", "abc123", {})
        assert v.major == 0
        assert v.minor == 0
        assert v.patch == 0

    def test_partial_version(self):
        v = PromptVersion("2.0", "abc123", {})
        assert v.major == 2
        assert v.minor == 0
        assert v.patch == 0

    def test_repr(self):
        v = PromptVersion("1.0.0", "abcdef123456", {})
        r = repr(v)
        assert "abcdef12" in r


class TestRAGPromptLoader:
    def test_load_existing_prompt(self):
        loader = RAGPromptLoader()
        prompt = loader.load("medical/report_analysis")
        assert prompt.category == "medical"
        assert prompt.name == "report_analysis"
        assert "You are a medical data extraction specialist" in prompt.content
        assert str(prompt.version) == "1.0.0"

    def test_load_rag_prompt(self):
        loader = RAGPromptLoader()
        prompt = loader.load("rag/document_retrieval")
        assert prompt.category == "rag"
        assert prompt.name == "document_retrieval"
        assert "search_queries" in prompt.content

    def test_load_nonexistent_raises(self):
        loader = RAGPromptLoader()
        with pytest.raises(FileNotFoundError):
            loader.load("nonexistent/category")

    def test_cache_hit(self):
        loader = RAGPromptLoader()
        cache = loader._cache
        loader.load("medical/report_analysis")
        assert cache.stats["misses"] == 1
        loader.load("medical/report_analysis")
        assert cache.stats["hits"] == 1
        assert cache.stats["misses"] == 1

    def test_bypass_cache(self):
        loader = RAGPromptLoader()
        p1 = loader.load("medical/report_analysis")
        p2 = loader.load("medical/report_analysis", bypass_cache=True)
        assert p1.path_key == p2.path_key
        assert p1.version.content_hash == p2.version.content_hash

    def test_get_version(self):
        loader = RAGPromptLoader()
        version = loader.get_version("rag/document_retrieval")
        assert version is not None
        assert str(version) == "1.0.0"

    def test_get_version_missing(self):
        loader = RAGPromptLoader()
        assert loader.get_version("nonexistent/foo") is None

    def test_invalidate_removes_from_cache(self):
        loader = RAGPromptLoader()
        cache = loader._cache
        loader.load("medical/report_analysis")
        assert cache.stats["size"] == 1
        loader.invalidate("medical/report_analysis")
        assert cache.stats["size"] == 0

    def test_render(self):
        loader = RAGPromptLoader()
        prompt = loader.load("rag/document_retrieval")
        rendered = prompt.render(question="test?")
        assert "test?" in rendered

    def test_content_hash_stable(self):
        loader = RAGPromptLoader()
        p1 = loader.load("medical/report_analysis")
        p2 = loader.load("medical/report_analysis", bypass_cache=True)
        assert p1.version.content_hash == p2.version.content_hash

    def test_render_missing_variable(self):
        loader = RAGPromptLoader()
        prompt = loader.load("rag/document_retrieval")
        rendered = prompt.render()
        assert "{{ question }}" not in rendered


class TestPromptManager:
    def test_list_categories(self):
        mgr = PromptManager()
        cats = mgr.list_categories()
        assert "medical" in cats
        assert "rag" in cats
        assert "chat" in cats
        assert "summary" in cats
        assert "system" in cats
        assert "emergency" in cats

    def test_list_prompts_all(self):
        mgr = PromptManager()
        prompts = mgr.list_prompts()
        assert len(prompts) >= 15
        paths = [p["path"] for p in prompts]
        assert "medical/report_analysis" in paths
        assert "rag/document_retrieval" in paths

    def test_list_prompts_by_category(self):
        mgr = PromptManager()
        rag_prompts = mgr.list_prompts(category="rag")
        assert len(rag_prompts) == 3
        for p in rag_prompts:
            assert p["category"] == "rag"

    def test_list_prompts_nonexistent_category(self):
        mgr = PromptManager()
        assert mgr.list_prompts(category="__nonexistent__") == []

    def test_get_prompt_metadata(self):
        mgr = PromptManager()
        meta = mgr.get_prompt_metadata("rag/document_retrieval")
        assert meta["path"] == "rag/document_retrieval"
        assert meta["category"] == "rag"
        assert "version" in meta
        assert "purpose" in meta
        assert "prompt_version" in meta

    def test_render(self):
        mgr = PromptManager()
        rendered = mgr.render("medical/report_analysis", text="test ocr text")
        assert "test ocr text" in rendered
        assert "{{ text }}" not in rendered

    def test_get_version(self):
        mgr = PromptManager()
        version = mgr.get_version("rag/document_retrieval")
        assert version == "1.0.0"

    def test_get_version_missing(self):
        mgr = PromptManager()
        assert mgr.get_version("__missing__") is None

    def test_preload_all(self):
        mgr = PromptManager()
        count = mgr.preload_all()
        assert count >= 15

    def test_invalidate_cache_single(self):
        mgr = PromptManager()
        mgr.get_prompt("medical/report_analysis")
        mgr.invalidate_cache("medical/report_analysis")

    def test_invalidate_cache_all(self):
        mgr = PromptManager()
        mgr.get_prompt("medical/report_analysis")
        mgr.invalidate_cache()
        stats = mgr._loader.cache_stats
        assert stats["size"] == 0

    def test_prompt_version_in_frontmatter(self):
        mgr = PromptManager()
        meta = mgr.get_prompt_metadata("rag/document_retrieval")
        assert meta["prompt_version"] == "1.0.0"
        assert str(meta["last_updated"]) == "2026-07-14"
