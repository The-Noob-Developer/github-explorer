"""Pydantic models for the search pipeline's request/response contract.

`Filters` / `NumericOrDateFilter` / `SearchInterpretation` mirror exactly what
we ask Groq to produce (see `config/prompts.py`) -- keeping the schema and the
prompt in the same shape is what lets `parse_and_validate` fail closed instead
of guessing when Groq's output doesn't match.
"""

from typing import Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class NumericOrDateFilter(BaseModel):
    """A single comparison filter, e.g. {"op": ">", "value": 1000}.

    `value` is a `Union[int, str, list]` because the same shape is reused for
    numeric filters (stars, forks, ...) and date filters (created, pushed),
    and for ".." it becomes a two-element list of matching types.
    """

    model_config = ConfigDict(extra="forbid")

    op: Literal[">", "<", ">=", "<=", "=", ".."]
    value: Union[int, str, list]


class Filters(BaseModel):
    """All filters Groq is allowed to populate. Unknown keys are rejected
    (`extra="forbid"`) so a malformed or hallucinated field fails validation
    immediately instead of silently passing through to the query builder.
    """

    model_config = ConfigDict(extra="forbid")

    topic: Optional[str] = None
    keyword: Optional[str] = None
    search_in: Optional[list[Literal["name", "description", "readme"]]] = None
    language: Optional[str] = None
    license: Optional[str] = None
    user: Optional[str] = None
    org: Optional[str] = None
    repo: Optional[str] = None
    archived: Optional[bool] = None
    is_public: Optional[bool] = None
    is_sponsorable: Optional[bool] = None
    mirror: Optional[bool] = None
    template: Optional[bool] = None
    has_funding_file: Optional[bool] = None
    stars: Optional[NumericOrDateFilter] = None
    forks: Optional[NumericOrDateFilter] = None
    followers: Optional[NumericOrDateFilter] = None
    size: Optional[NumericOrDateFilter] = None
    topics_count: Optional[NumericOrDateFilter] = None
    good_first_issues: Optional[NumericOrDateFilter] = None
    help_wanted_issues: Optional[NumericOrDateFilter] = None
    created: Optional[NumericOrDateFilter] = None
    pushed: Optional[NumericOrDateFilter] = None
    props: Optional[dict[str, str]] = None


class SearchInterpretation(BaseModel):
    """The full structured interpretation of a natural-language query."""

    model_config = ConfigDict(extra="forbid")

    filters: Filters
    sort: Optional[
        Literal["stars_desc", "forks_desc", "pushed_desc", "created_desc", "created_asc"]
    ] = None
    unsupported_requests: list[str] = Field(default_factory=list)
    interpretation_notes: str = ""
    needs_clarification: bool = False
    clarification: Optional[str] = None


class SearchRequest(BaseModel):
    """Incoming payload for POST /api/search."""

    query: str = Field(min_length=1, max_length=500)
    limit: Optional[int] = Field(default=25, ge=1)
    clarification_answer: Optional[str] = Field(default=None, alias="clarificationAnswer")
    cursor: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class PaginationInfo(BaseModel):
    has_next_page: bool
    end_cursor: Optional[str] = None


class RepositoryResultModel(BaseModel):
    name: str
    owner: str
    description: Optional[str] = None
    url: str
    stars: int
    forks: int
    primaryLanguage: Optional[str] = None
    isArchived: bool
    createdAt: str
    pushedAt: str


class InterpretationOut(BaseModel):
    filters: dict
    sort: Optional[str] = None
    unsupported_requests: list[str] = Field(default_factory=list)
    interpretation_notes: str = ""


class ClarificationOut(BaseModel):
    question: str
    context: Optional[str] = None


class ErrorOut(BaseModel):
    code: str
    message: str


class FactResponseModel(BaseModel):
    """Response body for GET /api/facts."""

    fact: str


class HealthResponseModel(BaseModel):
    """Response body for GET /api/health."""

    status: str


class SearchResponse(BaseModel):
    """The single response envelope returned by POST /api/search.

    Only the fields relevant to `status` are populated; the rest stay None so
    the JSON body matches the exact shapes documented in the API contract.
    """

    status: Literal["ok", "needs_clarification", "error"]
    search_query: Optional[str] = None
    results: Optional[list[RepositoryResultModel]] = None
    repository_count: Optional[int] = None
    pagination: Optional[PaginationInfo] = None
    interpretation: Optional[InterpretationOut] = None
    clarification: Optional[ClarificationOut] = None
    error: Optional[ErrorOut] = None
