"""Resolves a free-text topic candidate against GitHub's real topic index.

Kept as its own module, separate from `query_builder.py`, because it needs
I/O (GitHub REST calls) and fuzzy matching -- mixing that into the query
builder would make the one function that's supposed to be pure and trivially
testable (`query_builder.build`) depend on network state instead.

Algorithm (exact 8 steps from Section 6):
1. Query `/search/topics?q=<candidate>`.
2. Exact case-insensitive name match -> accept immediately, confidence 1.0.
3. No exact match -> re-query with a loosened term (strip hyphens/underscores,
   singular/plural variants) and collect candidates.
4. Score every candidate against the original input with fuzzy similarity.
5. Take the top-scoring candidate.
6. Score >= threshold -> auto-accept.
7. Score < threshold -> needs_clarification, with a suggestion.
8. Zero candidates at all -> topic_not_found, not a clarification (nothing to suggest).
"""

from __future__ import annotations

import json
import logging

import httpx
from rapidfuzz import fuzz

from app.models.github_models import TopicCandidate, TopicResolution
from app.services import github_service
from app.utils.cache import Cache

logger = logging.getLogger("app.topic_resolver")

_CACHE_PREFIX = "topic:"
_CACHE_TTL_SECONDS = 300


def _loosened_variants(term: str) -> list[str]:
    """Generate loosened forms of `term`: hyphen/underscore stripped, and
    naive singular/plural variants, used as fallback search terms when the
    exact query returns no exact match."""

    base = term.strip().lower()
    variants = {base, base.replace("-", " "), base.replace("_", " "), base.replace("-", "").replace("_", "")}
    if base.endswith("s"):
        variants.add(base[:-1])
    else:
        variants.add(base + "s")
    variants.discard("")
    return list(variants)


async def resolve(
    client: httpx.AsyncClient,
    topic: str | None,
    *,
    github_rest_url: str,
    github_token: str,
    timeout_seconds: float,
    confidence_threshold: float,
    cache: Cache,
) -> TopicResolution | None:
    """Resolve `topic` into a `TopicResolution`, or None if `topic` is falsy.

    Only ever called when `filters.topic` is non-null -- every other filter
    field passes through to `query_builder` untouched (Section 4's table).
    """

    if not topic:
        return None

    cache_key = f"{_CACHE_PREFIX}{topic.strip().lower()}"
    cached = await cache.get(cache_key)
    if cached is not None:
        return TopicResolution.model_validate(json.loads(cached))

    resolution = await _resolve_uncached(
        client,
        topic,
        github_rest_url=github_rest_url,
        github_token=github_token,
        timeout_seconds=timeout_seconds,
        confidence_threshold=confidence_threshold,
    )

    # Cache the resolution outcome itself (not raw GitHub responses, and
    # never anything containing GITHUB_TOKEN) so identical topic lookups
    # within the TTL window skip the network round trip entirely.
    await cache.set(cache_key, resolution.model_dump_json(), _CACHE_TTL_SECONDS)
    return resolution


async def _resolve_uncached(
    client: httpx.AsyncClient,
    topic: str,
    *,
    github_rest_url: str,
    github_token: str,
    timeout_seconds: float,
    confidence_threshold: float,
) -> TopicResolution:
    kwargs = dict(
        github_rest_url=github_rest_url,
        github_token=github_token,
        timeout_seconds=timeout_seconds,
    )

    # Step 1: query for the candidate as given.
    candidates = await github_service.search_topics(client, topic, **kwargs)

    # Step 2: exact, case-insensitive name match -> accept immediately.
    lowered = topic.strip().lower()
    for candidate in candidates:
        if candidate.name.lower() == lowered:
            return TopicResolution(resolved_slug=candidate.name, confidence=1.0, matched=True)

    # Step 3: no exact match -> re-query with loosened variants and collect
    # a combined candidate pool.
    all_candidates: dict[str, TopicCandidate] = {c.name: c for c in candidates}
    for variant in _loosened_variants(topic):
        if variant == lowered:
            continue
        try:
            more = await github_service.search_topics(client, variant, **kwargs)
        except Exception as exc:  # a loosened-variant query failing shouldn't abort resolution
            logger.warning("Loosened topic query failed for variant '%s': %s", variant, exc)
            continue
        for candidate in more:
            all_candidates.setdefault(candidate.name, candidate)
            if candidate.name.lower() == lowered:
                return TopicResolution(resolved_slug=candidate.name, confidence=1.0, matched=True)

    # Step 8: zero candidates at all -> topic_not_found, not a clarification.
    if not all_candidates:
        return TopicResolution(not_found=True)

    # Step 4-5: score every candidate against the original input, take the top.
    scored = [
        (candidate, fuzz.ratio(lowered, candidate.name.lower()) / 100.0)
        for candidate in all_candidates.values()
    ]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    top_candidate, top_score = scored[0]

    # Step 6: auto-accept at/above threshold.
    if top_score >= confidence_threshold:
        return TopicResolution(resolved_slug=top_candidate.name, confidence=top_score, matched=True)

    # Step 7: below threshold -> ask for clarification instead of guessing.
    return TopicResolution(
        confidence=top_score,
        matched=False,
        needs_clarification=True,
        clarification=(
            f"I couldn't confidently match the topic '{topic}'. "
            f"Did you mean {top_candidate.name}?"
        ),
    )
