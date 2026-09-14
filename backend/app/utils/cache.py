"""Caching abstraction used by the search pipeline.

`Cache` is a minimal protocol with `get`/`set`/`delete`. `search_service.py`
and `topic_resolver.py` depend only on this interface, never on a concrete
implementation, so swapping `InMemoryCache` for `RedisCache` (automatically,
based on whether `REDIS_URL` is set) requires zero changes at any call site.
When `CACHE_ENABLED=false`, `NoOpCache` implements the same interface as a
pure pass-through, so the whole caching layer can be disabled without
touching any call site either.

Never cache anything containing secrets (`GROQ_API_KEY`, `GITHUB_TOKEN`) or a
per-user identifier -- only the two things described in Section 10: exact
topic-lookup strings and exact constructed GitHub search-query strings.
"""

from __future__ import annotations

import time
from typing import Optional, Protocol


class Cache(Protocol):
    async def get(self, key: str) -> Optional[str]: ...

    async def set(self, key: str, value: str, ttl_seconds: int) -> None: ...

    async def delete(self, key: str) -> None: ...


class InMemoryCache:
    """A simple TTL dict cache, safe for a single-process deployment.

    Not shared across processes/instances -- for multi-instance deployments,
    set `REDIS_URL` to get `RedisCache` instead.
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, str]] = {}

    async def get(self, key: str) -> Optional[str]:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() > expires_at:
            self._store.pop(key, None)
            return None
        return value

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        self._store[key] = (time.monotonic() + ttl_seconds, value)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)


class RedisCache:
    """Cache backed by Redis, used automatically when `REDIS_URL` is set."""

    def __init__(self, redis_url: str) -> None:
        import redis.asyncio as redis  # local import: optional dependency

        self._client = redis.from_url(redis_url, decode_responses=True)

    async def get(self, key: str) -> Optional[str]:
        return await self._client.get(key)

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        await self._client.set(key, value, ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)


class NoOpCache:
    """Used when `CACHE_ENABLED=false`. Every call is a no-op miss."""

    async def get(self, key: str) -> Optional[str]:
        return None

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        return None

    async def delete(self, key: str) -> None:
        return None


def build_cache(*, cache_enabled: bool, redis_url: Optional[str]) -> Cache:
    """Factory choosing the right `Cache` implementation from settings."""

    if not cache_enabled:
        return NoOpCache()
    if redis_url:
        return RedisCache(redis_url)
    return InMemoryCache()
