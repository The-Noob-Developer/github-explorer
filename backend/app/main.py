"""FastAPI application entrypoint.

Owns the app-wide lifecycle: builds the single shared `httpx.AsyncClient` and
cache instance at startup (closed cleanly at shutdown), configures CORS to
only the deployed frontend origin, wires up the rate limiter, and includes
every route module. Deliberately contains no pipeline logic itself -- that
all lives in `services/`.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.api.routes import facts, health, search
from app.config.settings import get_settings
from app.utils.cache import build_cache
from app.utils.rate_limit import limiter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # A single shared AsyncClient (not one per request) reuses connection
    # pools across requests, which matters under any real load.
    app.state.http_client = httpx.AsyncClient()
    app.state.cache = build_cache(
        cache_enabled=settings.cache_enabled, redis_url=settings.redis_url
    )
    logger.info("Startup complete: cache_enabled=%s", settings.cache_enabled)

    yield

    await app.state.http_client.aclose()
    logger.info("Shutdown complete")


app = FastAPI(title="GitHub Explorer API", lifespan=lifespan)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """A distinct "too fast" shape, deliberately not the GitHub error shape,
    since this limit is about our own API, not GitHub's."""

    return JSONResponse(
        status_code=429,
        content={
            "status": "error",
            "error": {
                "code": "rate_limited",
                "message": "You're sending requests too quickly. Please slow down and try again.",
            },
        },
    )


_settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    # allow_origins=[_settings.allowed_origin],
    allow_origins=_settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(facts.router)
app.include_router(health.router)
