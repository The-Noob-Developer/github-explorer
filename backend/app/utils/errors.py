"""Typed exception hierarchy for the search pipeline.

Every exception here maps 1:1 to an error `code` + HTTP status + user-facing
`message` from the API contract. Routes catch `AppError` (the common base)
and translate it into the response envelope -- they never let a raw
exception/traceback leak into a client response, which is why every code path
that can fail raises one of these instead of a bare `Exception`.
"""

from __future__ import annotations


class AppError(Exception):
    """Base class for all typed, user-facing application errors."""

    code: str = "unexpected_error"
    http_status: int = 500
    message: str = "Something went wrong on our end. Please try again."

    def __init__(self, message: str | None = None):
        super().__init__(message or self.message)
        if message:
            self.message = message


class GroqUnavailableError(AppError):
    code = "groq_unavailable"
    http_status = 503
    message = "Our search interpreter is temporarily unavailable. Please try again in a moment."


class GroqInvalidOutputError(AppError):
    code = "groq_invalid_output"
    http_status = 502
    message = "We had trouble understanding that request. Try rephrasing it."


class GithubUnavailableError(AppError):
    code = "github_unavailable"
    http_status = 503
    message = "GitHub is temporarily unavailable. Please try again shortly."


class GithubRateLimitedError(AppError):
    code = "github_rate_limited"
    http_status = 429
    message = "GitHub API rate limit reached. Try again shortly."


class TopicNotFoundError(AppError):
    code = "topic_not_found"
    http_status = 200
    message = "I couldn't find a matching GitHub topic for that term."


class InvalidRequestError(AppError):
    code = "invalid_request"
    http_status = 400
    message = "That search request wasn't valid. Please check your input."


class NoUsableFiltersError(AppError):
    code = "no_usable_filters"
    http_status = 400
    message = "I couldn't extract any usable search filters from that request."


class RequestTimeoutError(AppError):
    code = "timeout"
    http_status = 504
    message = "The search took too long to respond. Please try again."


class UnexpectedError(AppError):
    code = "unexpected_error"
    http_status = 500
    message = "Something went wrong on our end. Please try again."


# Alias matching the exact class name requested in the spec. Deliberately
# shadows the builtin `TimeoutError` only within this module's namespace;
# every other module imports it explicitly by name (`from .errors import
# TimeoutError`), which is unambiguous at the call site.
TimeoutError = RequestTimeoutError

