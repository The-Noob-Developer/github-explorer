"""Typed models for data coming back from GitHub's GraphQL/REST APIs."""

from typing import Optional

from pydantic import BaseModel


class RepositoryResult(BaseModel):
    """A single repository node, flattened out of the GraphQL response shape."""

    name: str
    owner: str
    description: Optional[str] = None
    url: str
    stars: int
    forks: int
    primary_language: Optional[str] = None
    is_archived: bool
    created_at: str
    pushed_at: str


class PageInfo(BaseModel):
    has_next_page: bool
    end_cursor: Optional[str] = None


class GraphQLSearchResult(BaseModel):
    """The parsed result of the fixed `RepoSearch` GraphQL query."""

    repository_count: int
    page_info: PageInfo
    repositories: list[RepositoryResult]


class TopicCandidate(BaseModel):
    """A single candidate returned by GitHub's `/search/topics`."""

    name: str
    display_name: Optional[str] = None
    score: float = 0.0


class TopicResolution(BaseModel):
    """Outcome of `topic_resolver.resolve()`."""

    resolved_slug: Optional[str] = None
    confidence: float = 0.0
    matched: bool = False
    needs_clarification: bool = False
    clarification: Optional[str] = None
    not_found: bool = False
