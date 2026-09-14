"""FastAPI `Depends()` providers.

Every dependency here reads from `app.state`, which is populated once at
startup by the lifespan handler in `main.py`. This avoids module-level
mutable globals (explicitly disallowed by Section 10) while still giving
every request access to the single shared `httpx.AsyncClient` and cache
instance.
"""

from __future__ import annotations

import httpx
from fastapi import Request

from app.config.settings import Settings, get_settings
from app.utils.cache import Cache


def get_http_client(request: Request) -> httpx.AsyncClient:
    """Return the shared `httpx.AsyncClient` created at app startup."""

    return request.app.state.http_client


def get_cache(request: Request) -> Cache:
    """Return the shared cache instance created at app startup."""

    return request.app.state.cache


def get_app_settings() -> Settings:
    return get_settings()
