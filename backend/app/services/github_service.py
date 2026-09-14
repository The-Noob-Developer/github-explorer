"""Wraps GitHub's REST `/search/topics` endpoint and the fixed GraphQL
repository-search query.

This is the only module that constructs GitHub HTTP requests. Rate-limit and
timeout handling live here so every caller gets the same typed exceptions
(`GithubRateLimitedError`, `GithubUnavailableError`, `TimeoutError`) instead
of raw `httpx` exceptions leaking upward.
"""

from __future__ import annotations

import logging

import httpx

from app.models.github_models import GraphQLSearchResult, PageInfo, RepositoryResult, TopicCandidate
from app.utils.errors import GithubRateLimitedError, GithubUnavailableError
from app.utils.errors import TimeoutError as AppTimeoutError

logger = logging.getLogger("app.github_service")

REPO_SEARCH_QUERY = """
query RepoSearch($searchQuery: String!, $first: Int!, $after: String) {
  search(query: $searchQuery, type: REPOSITORY, first: $first, after: $after) {
    repositoryCount
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      node {
        ... on Repository {
          name
          owner { login }
          description
          url
          stargazerCount
          forkCount
          primaryLanguage { name }
          isArchived
          createdAt
          pushedAt
        }
      }
    }
  }
}
"""


def _raise_for_rate_limit_or_status(response: httpx.Response) -> None:
    """Translate GitHub's rate-limit headers and HTTP status into typed
    exceptions. GitHub calls are never retried automatically when
    rate-limited (Section 10) -- we surface the error immediately so the
    caller can inform the user rather than silently burning more quota."""

    remaining = response.headers.get("X-RateLimit-Remaining")
    if response.status_code == 403 and remaining == "0":
        raise GithubRateLimitedError()
    if response.status_code == 429:
        raise GithubRateLimitedError()
    if response.status_code >= 500:
        raise GithubUnavailableError()
    if response.status_code >= 400:
        raise GithubUnavailableError(f"GitHub API error: {response.status_code}")


async def search_topics(
    client: httpx.AsyncClient,
    query: str,
    *,
    github_rest_url: str,
    github_token: str,
    timeout_seconds: float,
) -> list[TopicCandidate]:
    """Call `GET /search/topics?q=<query>` and return candidate topics."""

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        response = await client.get(
            f"{github_rest_url}/search/topics",
            params={"q": query},
            headers=headers,
            timeout=timeout_seconds,
        )
    except httpx.TimeoutException as exc:
        raise AppTimeoutError() from exc
    except httpx.HTTPError as exc:
        raise GithubUnavailableError() from exc

    _raise_for_rate_limit_or_status(response)

    data = response.json()
    return [
        TopicCandidate(name=item["name"], display_name=item.get("display_name"))
        for item in data.get("items", [])
    ]


async def search_repositories(
    client: httpx.AsyncClient,
    search_query: str,
    first: int,
    after: str | None,
    *,
    github_graphql_url: str,
    github_token: str,
    timeout_seconds: float,
) -> GraphQLSearchResult:
    """Run the fixed `RepoSearch` GraphQL query with cursor pagination.

    Only `$searchQuery`, `$first`, and `$after` are ever dynamic -- the query
    document itself is never modified, which keeps the surface area GitHub
    actually receives fully auditable.
    """

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
    }
    variables = {"searchQuery": search_query, "first": first, "after": after}

    try:
        response = await client.post(
            github_graphql_url,
            json={"query": REPO_SEARCH_QUERY, "variables": variables},
            headers=headers,
            timeout=timeout_seconds,
        )
    except httpx.TimeoutException as exc:
        raise AppTimeoutError() from exc
    except httpx.HTTPError as exc:
        raise GithubUnavailableError() from exc

    _raise_for_rate_limit_or_status(response)

    payload = response.json()
    if "errors" in payload and payload["errors"]:
        logger.error("GitHub GraphQL errors: %s", payload["errors"])
        raise GithubUnavailableError()

    search = payload["data"]["search"]
    repositories = []
    for edge in search["edges"]:
        node = edge["node"]
        repositories.append(
            RepositoryResult(
                name=node["name"],
                owner=node["owner"]["login"],
                description=node.get("description"),
                url=node["url"],
                stars=node["stargazerCount"],
                forks=node["forkCount"],
                primary_language=(node.get("primaryLanguage") or {}).get("name"),
                is_archived=node["isArchived"],
                created_at=node["createdAt"],
                pushed_at=node["pushedAt"],
            )
        )

    page_info = search["pageInfo"]
    return GraphQLSearchResult(
        repository_count=search["repositoryCount"],
        page_info=PageInfo(
            has_next_page=page_info["hasNextPage"], end_cursor=page_info.get("endCursor")
        ),
        repositories=repositories,
    )
