"""Full pipeline orchestration tests with mocked groq/github services,
including the end-to-end clarification round-trip from Section 19."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.models.github_models import GraphQLSearchResult, PageInfo, RepositoryResult
from app.services.search_service import ClarificationResult, OrchestrationResult, orchestrate
from app.utils.cache import InMemoryCache
from app.utils.errors import NoUsableFiltersError

_GRAPHQL_RESULT = GraphQLSearchResult(
    repository_count=1,
    page_info=PageInfo(has_next_page=False, end_cursor=None),
    repositories=[
        RepositoryResult(
            name="example-repo",
            owner="example-owner",
            description="An example repository",
            url="https://github.com/example-owner/example-repo",
            stars=12345,
            forks=678,
            primary_language="Python",
            is_archived=False,
            created_at="2020-01-01T00:00:00Z",
            pushed_at="2026-01-01T00:00:00Z",
        )
    ],
)


def _groq_json(**overrides):
    payload = {
        "filters": {"language": "Python", "stars": {"op": ">", "value": 10000}},
        "sort": None,
        "unsupported_requests": [],
        "interpretation_notes": "note",
        "needs_clarification": False,
        "clarification": None,
    }
    payload.update(overrides)
    return json.dumps(payload)


@pytest.mark.asyncio
async def test_orchestrate_happy_path_returns_results():
    with patch(
        "app.services.groq_service.interpret", new=AsyncMock(return_value=_groq_json())
    ), patch(
        "app.services.github_service.search_repositories",
        new=AsyncMock(return_value=_GRAPHQL_RESULT),
    ):
        result = await orchestrate(
            client=None,
            cache=InMemoryCache(),
            query="Find Python repositories with more than 10,000 stars",
            limit=25,
            clarification_answer=None,
            cursor=None,
            groq_api_key="key",
            groq_model="model",
            groq_timeout_seconds=10,
            github_rest_url="https://api.github.com",
            github_graphql_url="https://api.github.com/graphql",
            github_token="tok",
            github_timeout_seconds=10,
            confidence_threshold=0.80,
            max_results=100,
        )

    assert isinstance(result, OrchestrationResult)
    assert result.search_query == "language:Python stars:>10000"
    assert result.graphql_result.repositories[0].name == "example-repo"


@pytest.mark.asyncio
async def test_orchestrate_no_usable_filters_raises():
    empty_json = _groq_json(filters={})
    with patch("app.services.groq_service.interpret", new=AsyncMock(return_value=empty_json)):
        with pytest.raises(NoUsableFiltersError):
            await orchestrate(
                client=None,
                cache=InMemoryCache(),
                query="hello",
                limit=25,
                clarification_answer=None,
                cursor=None,
                groq_api_key="key",
                groq_model="model",
                groq_timeout_seconds=10,
                github_rest_url="https://api.github.com",
                github_graphql_url="https://api.github.com/graphql",
                github_token="tok",
                github_timeout_seconds=10,
                confidence_threshold=0.80,
                max_results=100,
            )


@pytest.mark.asyncio
async def test_clarification_round_trip_end_to_end():
    """First call returns needs_clarification (low-confidence topic); second
    call with clarificationAnswer returns ok with results."""

    topic_json = _groq_json(filters={"topic": "jquerry"})

    with patch(
        "app.services.groq_service.interpret", new=AsyncMock(return_value=topic_json)
    ), patch(
        "app.services.topic_resolver.resolve",
        new=AsyncMock(
            return_value=type(
                "R",
                (),
                {
                    "not_found": False,
                    "needs_clarification": True,
                    "clarification": "Did you mean jquery?",
                    "resolved_slug": None,
                },
            )()
        ),
    ):
        first = await orchestrate(
            client=None,
            cache=InMemoryCache(),
            query="Find jquerry repositories",
            limit=25,
            clarification_answer=None,
            cursor=None,
            groq_api_key="key",
            groq_model="model",
            groq_timeout_seconds=10,
            github_rest_url="https://api.github.com",
            github_graphql_url="https://api.github.com/graphql",
            github_token="tok",
            github_timeout_seconds=10,
            confidence_threshold=0.80,
            max_results=100,
        )

    assert isinstance(first, ClarificationResult)
    assert "jquery" in first.question

    with patch(
        "app.services.groq_service.interpret", new=AsyncMock(return_value=topic_json)
    ), patch(
        "app.services.topic_resolver.resolve",
        new=AsyncMock(
            return_value=type(
                "R",
                (),
                {
                    "not_found": False,
                    "needs_clarification": False,
                    "clarification": None,
                    "resolved_slug": "jquery",
                },
            )()
        ),
    ), patch(
        "app.services.github_service.search_repositories",
        new=AsyncMock(return_value=_GRAPHQL_RESULT),
    ):
        second = await orchestrate(
            client=None,
            cache=InMemoryCache(),
            query="Find jquerry repositories",
            limit=25,
            clarification_answer="jquery",
            cursor=None,
            groq_api_key="key",
            groq_model="model",
            groq_timeout_seconds=10,
            github_rest_url="https://api.github.com",
            github_graphql_url="https://api.github.com/graphql",
            github_token="tok",
            github_timeout_seconds=10,
            confidence_threshold=0.80,
            max_results=100,
        )

    assert isinstance(second, OrchestrationResult)
    assert second.search_query == "topic:jquery"
