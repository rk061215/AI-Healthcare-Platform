from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    value: T
    expires_at: float


class PromptCache:
    """TTL + LRU cache for loaded prompts.

    Evicts least-recently-used entries when maxsize is exceeded.
    Supports per-key TTL, manual invalidation, and hit/miss stats.
    """

    def __init__(self, maxsize: int = 256, default_ttl_seconds: float = 300.0):
        self._maxsize = maxsize
        self._default_ttl = default_ttl_seconds
        self._store: OrderedDict[str, CacheEntry[Any]] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        now = time.time()
        entry = self._store.get(key)
        if entry is None:
            self._misses += 1
            return None
        if entry.expires_at <= now:
            self._store.pop(key)
            self._misses += 1
            return None
        self._store.move_to_end(key)
        self._hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        self._store[key] = CacheEntry(value=value, expires_at=time.time() + ttl)
        self._store.move_to_end(key)
        while len(self._store) > self._maxsize:
            self._store.popitem(last=False)

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()
        self._hits = 0
        self._misses = 0

    @property
    def stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 4) if total > 0 else 0.0,
            "size": len(self._store),
            "maxsize": self._maxsize,
        }

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None

    def __len__(self) -> int:
        return len(self._store)
