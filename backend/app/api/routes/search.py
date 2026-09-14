"""POST /api/search.

Deliberately thin: validate the request, delegate to
`search_service.orchestrate`, and map whatever comes back (a result, a
clarification, or a typed error) onto the exact response envelope from
Section 9. No pipeline logic lives here.
"""

from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.api.dependencies import get_cache, get_http_client
from app.config.settings import Settings, get_settings
from app.models.search_models import (
    ClarificationOut,
    ErrorOut,
    InterpretationOut,
    PaginationInfo,
    RepositoryResultModel,
    SearchRequest,
    SearchResponse,
)
from app.services.search_service import ClarificationResult, OrchestrationResult, orchestrate
from app.utils.cache import Cache
from app.utils.errors import AppError, UnexpectedError
from app.utils.rate_limit import limiter

logger = logging.getLogger("app.api.search")

router = APIRouter()


def _to_response(result: OrchestrationResult | ClarificationResult) -> SearchResponse:
    if isinstance(result, ClarificationResult):
        return SearchResponse(
            status="needs_clarification",
            clarification=ClarificationOut(question=result.question, context=result.context),
        )

    graphql = result.graphql_result
    interpretation = result.interpretation
    return SearchResponse(
        status="ok",
        search_query=result.search_query,
        results=[
            RepositoryResultModel(
                name=repo.name,
                owner=repo.owner,
                description=repo.description,
                url=repo.url,
                stars=repo.stars,
                forks=repo.forks,
                primaryLanguage=repo.primary_language,
                isArchived=repo.is_archived,
                createdAt=repo.created_at,
                pushedAt=repo.pushed_at,
            )
            for repo in graphql.repositories
        ],
        repository_count=graphql.repository_count,
        pagination=PaginationInfo(
            has_next_page=graphql.page_info.has_next_page,
            end_cursor=graphql.page_info.end_cursor,
        ),
        interpretation=InterpretationOut(
            filters=interpretation.filters.model_dump(exclude_none=True),
            sort=interpretation.sort,
            unsupported_requests=interpretation.unsupported_requests,
            interpretation_notes=interpretation.interpretation_notes,
        ),
    )


@router.post("/api/search", response_model=SearchResponse)
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
async def search(
    request: Request,
    body: SearchRequest,
    client: httpx.AsyncClient = Depends(get_http_client),
    cache: Cache = Depends(get_cache),
    settings: Settings = Depends(get_settings),
):
    try:
        outcome = await orchestrate(
            client=client,
            cache=cache,
            query=body.query,
            limit=body.limit or 25,
            clarification_answer=body.clarification_answer,
            cursor=body.cursor,
            groq_api_key=settings.groq_api_key,
            groq_model=settings.groq_model,
            groq_timeout_seconds=settings.groq_timeout_seconds,
            github_rest_url=settings.github_rest_url,
            github_graphql_url=settings.github_graphql_url,
            github_token=settings.github_token,
            github_timeout_seconds=settings.github_timeout_seconds,
            confidence_threshold=settings.confidence_threshold,
            max_results=settings.max_results,
        )
    except AppError as exc:
        # Each typed error carries its own HTTP status (e.g. 503 for
        # groq_unavailable, 200 for the "soft" topic_not_found, ...) per
        # Section 9's table -- we never fall back to a generic 500 here.
        logger.warning("Search failed with %s: %s", exc.code, exc)
        body_out = SearchResponse(status="error", error=ErrorOut(code=exc.code, message=exc.message))
        return JSONResponse(status_code=exc.http_status, content=body_out.model_dump(exclude_none=True))
    except Exception:  # noqa: BLE001 -- last line of defense, never leak a traceback
        logger.exception("Unexpected error while handling /api/search")
        err = UnexpectedError()
        body_out = SearchResponse(status="error", error=ErrorOut(code=err.code, message=err.message))
        return JSONResponse(status_code=err.http_status, content=body_out.model_dump(exclude_none=True))

    return _to_response(outcome)
