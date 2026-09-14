"""Tests for `topic_resolver.resolve`, covering the exact-match, threshold
boundary, and zero-candidate cases from Section 6."""

from unittest.mock import AsyncMock, patch

import pytest

from app.models.github_models import TopicCandidate
from app.services import topic_resolver
from app.utils.cache import InMemoryCache


@pytest.mark.asyncio
async def test_exact_match_accepts_with_confidence_one():
    with patch(
        "app.services.github_service.search_topics",
        new=AsyncMock(return_value=[TopicCandidate(name="react")]),
    ):
        resolution = await topic_resolver.resolve(
            client=None,
            topic="react",
            github_rest_url="https://api.github.com",
            github_token="tok",
            timeout_seconds=10,
            confidence_threshold=0.80,
            cache=InMemoryCache(),
        )
    assert resolution.matched is True
    assert resolution.confidence == 1.0
    assert resolution.resolved_slug == "react"


@pytest.mark.asyncio
async def test_score_at_threshold_accepts():
    # "jquery" vs "jquerz" -- rapidfuzz.fuzz.ratio scores this well above 0.80,
    # so we directly patch the scoring path via a candidate list that scores
    # exactly at boundary through a controlled monkeypatch of fuzz.ratio.
    with patch(
        "app.services.github_service.search_topics",
        new=AsyncMock(return_value=[TopicCandidate(name="jquery")]),
    ), patch("app.services.topic_resolver.fuzz.ratio", return_value=80.0):
        resolution = await topic_resolver.resolve(
            client=None,
            topic="jquerz",
            github_rest_url="https://api.github.com",
            github_token="tok",
            timeout_seconds=10,
            confidence_threshold=0.80,
            cache=InMemoryCache(),
        )
    assert resolution.matched is True
    assert resolution.confidence == 0.80
    assert resolution.resolved_slug == "jquery"


@pytest.mark.asyncio
async def test_score_just_below_threshold_requests_clarification():
    with patch(
        "app.services.github_service.search_topics",
        new=AsyncMock(return_value=[TopicCandidate(name="jquery")]),
    ), patch("app.services.topic_resolver.fuzz.ratio", return_value=79.0):
        resolution = await topic_resolver.resolve(
            client=None,
            topic="jquerry",
            github_rest_url="https://api.github.com",
            github_token="tok",
            timeout_seconds=10,
            confidence_threshold=0.80,
            cache=InMemoryCache(),
        )
    assert resolution.matched is False
    assert resolution.needs_clarification is True
    assert "jquery" in resolution.clarification


@pytest.mark.asyncio
async def test_zero_candidates_returns_not_found():
    with patch(
        "app.services.github_service.search_topics",
        new=AsyncMock(return_value=[]),
    ):
        resolution = await topic_resolver.resolve(
            client=None,
            topic="totallymadeupnonexistenttopic",
            github_rest_url="https://api.github.com",
            github_token="tok",
            timeout_seconds=10,
            confidence_threshold=0.80,
            cache=InMemoryCache(),
        )
    assert resolution.not_found is True
    assert resolution.needs_clarification is False


@pytest.mark.asyncio
async def test_none_topic_returns_none():
    resolution = await topic_resolver.resolve(
        client=None,
        topic=None,
        github_rest_url="https://api.github.com",
        github_token="tok",
        timeout_seconds=10,
        confidence_threshold=0.80,
        cache=InMemoryCache(),
    )
    assert resolution is None
