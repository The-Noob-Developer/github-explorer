"""Verifies hasNextPage/endCursor propagate correctly across two sequential
paginated `github_service.search_repositories` calls."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.services import github_service


def _graphql_response(has_next_page: bool, end_cursor):
    return {
        "data": {
            "search": {
                "repositoryCount": 2,
                "pageInfo": {"hasNextPage": has_next_page, "endCursor": end_cursor},
                "edges": [
                    {
                        "node": {
                            "name": "repo-a",
                            "owner": {"login": "octocat"},
                            "description": "desc",
                            "url": "https://github.com/octocat/repo-a",
                            "stargazerCount": 10,
                            "forkCount": 1,
                            "primaryLanguage": {"name": "Python"},
                            "isArchived": False,
                            "createdAt": "2020-01-01T00:00:00Z",
                            "pushedAt": "2021-01-01T00:00:00Z",
                        }
                    }
                ],
            }
        }
    }


class _FakeResponse:
    def __init__(self, payload, status_code=200, headers=None):
        self._payload = payload
        self.status_code = status_code
        self.headers = headers or {}

    def json(self):
        return self._payload


@pytest.mark.asyncio
async def test_first_page_has_next_page_true():
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post = AsyncMock(return_value=_FakeResponse(_graphql_response(True, "CURSOR_1")))

    result = await github_service.search_repositories(
        client,
        "language:Python",
        first=1,
        after=None,
        github_graphql_url="https://api.github.com/graphql",
        github_token="tok",
        timeout_seconds=10,
    )

    assert result.page_info.has_next_page is True
    assert result.page_info.end_cursor == "CURSOR_1"


@pytest.mark.asyncio
async def test_second_page_using_cursor_has_next_page_false():
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post = AsyncMock(return_value=_FakeResponse(_graphql_response(False, None)))

    result = await github_service.search_repositories(
        client,
        "language:Python",
        first=1,
        after="CURSOR_1",
        github_graphql_url="https://api.github.com/graphql",
        github_token="tok",
        timeout_seconds=10,
    )

    assert result.page_info.has_next_page is False
    assert result.page_info.end_cursor is None

    # Confirm the cursor was actually forwarded as the GraphQL `after` variable.
    _, kwargs = client.post.call_args
    assert kwargs["json"]["variables"]["after"] == "CURSOR_1"
