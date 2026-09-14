"""Orchestrates the full search pipeline (Section 3, steps 1-5).

`orchestrate()` is the *only* function allowed to call `groq_service`,
`topic_resolver`, `query_builder`, and `github_service` together in
sequence -- every other module talks to at most one of those. That keeps the
call graph shallow: route handlers call this one function, this one function
calls the specialist services, and nothing else reaches across layers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from app.models.github_models import GraphQLSearchResult, TopicResolution
from app.models.search_models import SearchInterpretation
from app.services import github_service, groq_service, query_builder, topic_resolver
from app.utils.cache import Cache
from app.utils.errors import NoUsableFiltersError, TopicNotFoundError
from app.utils.validation import has_any_usable_filter

logger = logging.getLogger("app.search_service")


@dataclass
class OrchestrationResult:
    """Everything a route handler needs to build the `ok` response shape."""

    interpretation: SearchInterpretation
    search_query: str
    graphql_result: GraphQLSearchResult


@dataclass
class ClarificationResult:
    question: str
    context: str | None


async def orchestrate(
    *,
    client: httpx.AsyncClient,
    cache: Cache,
    query: str,
    limit: int,
    clarification_answer: str | None,
    cursor: str | None,
    groq_api_key: str,
    groq_model: str,
    groq_timeout_seconds: float,
    github_rest_url: str,
    github_graphql_url: str,
    github_token: str,
    github_timeout_seconds: float,
    confidence_threshold: float,
    max_results: int,
) -> OrchestrationResult | ClarificationResult:
    """Run the full pipeline for one `/api/search` request.

    Returns either an `OrchestrationResult` (ready to serialize as `status:
    ok`) or a `ClarificationResult` (ready to serialize as `status:
    needs_clarification`). Errors are raised as one of the typed exceptions
    in `utils/errors.py` and are expected to be caught by the route handler.
    """

    # Step 1 + 2: interpret the NL query, and validate the shape strictly.
    raw = await groq_service.interpret(
        client,
        query,
        api_key=groq_api_key,
        model=groq_model,
        timeout_seconds=groq_timeout_seconds,
        clarification_context=clarification_answer,
    )
    interpretation = groq_service.parse_and_validate(raw)

    # If Groq itself already flagged an ambiguity unrelated to topic
    # resolution (e.g. an ambiguous date), short-circuit immediately -- we
    # must not proceed to topic resolution or query building per Section 5.
    if interpretation.needs_clarification and not clarification_answer:
        return ClarificationResult(
            question=interpretation.clarification or "Could you clarify your request?",
            context=None,
        )

    if not has_any_usable_filter(interpretation.filters):
        raise NoUsableFiltersError()

    # Step 3: topic resolution, only when filters.topic is set.
    resolved_topic: str | None = None
    if interpretation.filters.topic:
        topic_candidate = (
            clarification_answer if clarification_answer else interpretation.filters.topic
        )
        resolution: TopicResolution | None = await topic_resolver.resolve(
            client,
            topic_candidate,
            github_rest_url=github_rest_url,
            github_token=github_token,
            timeout_seconds=github_timeout_seconds,
            confidence_threshold=confidence_threshold,
            cache=cache,
        )
        if resolution is not None:
            if resolution.not_found:
                raise TopicNotFoundError()
            if resolution.needs_clarification and not clarification_answer:
                return ClarificationResult(
                    question=resolution.clarification or "Could you clarify that topic?",
                    context=f"topic:{topic_candidate}",
                )
            if resolution.needs_clarification and clarification_answer:
                # The user already answered once but the clarification
                # answer itself didn't resolve confidently either -- surface
                # topic_not_found rather than looping clarification forever.
                raise TopicNotFoundError()
            resolved_topic = resolution.resolved_slug

    # Step 4: pure, I/O-free translation into a GitHub search-query string.
    search_query = query_builder.build(interpretation.filters, resolved_topic)

    # Step 5: fixed GraphQL call with cursor pagination, clamped server-side.
    clamped_first = min(max(limit, 1), max_results)
    graphql_result = await github_service.search_repositories(
        client,
        search_query,
        first=clamped_first,
        after=cursor,
        github_graphql_url=github_graphql_url,
        github_token=github_token,
        timeout_seconds=github_timeout_seconds,
    )

    return OrchestrationResult(
        interpretation=interpretation,
        search_query=search_query,
        graphql_result=graphql_result,
    )
