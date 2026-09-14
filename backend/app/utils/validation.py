"""Shared validation helpers used to enforce the schema in Section 5 before
anything reaches `query_builder.py`.

We validate here -- and fail closed on any violation -- rather than in
`query_builder.py` itself, because the query builder is meant to stay a pure,
trivial function: given already-valid filters, deterministically produce a
string. Mixing "is this shape even legal" checks into that function would
make it harder to unit test and harder to reason about. Failing closed
(raising `GroqInvalidOutputError` instead of coercing/guessing) matters
because a guessed value (e.g. silently treating a malformed range as a
single value) could return results the user never asked for, which is worse
than surfacing a clear "try rephrasing" error.
"""

from __future__ import annotations

import json
import re
from datetime import date

from app.models.search_models import Filters, NumericOrDateFilter, SearchInterpretation
from app.utils.errors import GroqInvalidOutputError

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def is_date_string(value: object) -> bool:
    """Return True if `value` is a `YYYY-MM-DD` string that actually parses."""

    if not isinstance(value, str) or not _DATE_RE.match(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def validate_numeric_or_date_filter(field_name: str, filt: NumericOrDateFilter) -> None:
    """Enforce the operator-shape rules from Section 5.

    - `op == ".."` requires `value` to be a 2-element list, min <= max, both
      the same type (both int, or both date strings).
    - Any other op requires a scalar int or a date string, never a list.
    """

    if filt.op == "..":
        if not isinstance(filt.value, list) or len(filt.value) != 2:
            raise GroqInvalidOutputError(
                f"Filter '{field_name}' uses the '..' range operator but its value "
                "is not a two-element list."
            )
        low, high = filt.value
        both_int = isinstance(low, int) and isinstance(high, int) and not isinstance(low, bool)
        both_date = is_date_string(low) and is_date_string(high)
        if not (both_int or both_date):
            raise GroqInvalidOutputError(
                f"Filter '{field_name}' range values must both be numbers or both be "
                "YYYY-MM-DD dates."
            )
        if both_int and low > high:
            raise GroqInvalidOutputError(
                f"Filter '{field_name}' range minimum is greater than its maximum."
            )
        if both_date and low > high:
            raise GroqInvalidOutputError(
                f"Filter '{field_name}' date range start is after its end."
            )
    else:
        if isinstance(filt.value, list):
            raise GroqInvalidOutputError(
                f"Filter '{field_name}' uses operator '{filt.op}' which requires a single "
                "value, not a list."
            )
        is_plain_int = isinstance(filt.value, int) and not isinstance(filt.value, bool)
        if not (is_plain_int or is_date_string(filt.value)):
            raise GroqInvalidOutputError(
                f"Filter '{field_name}' value must be a number or a YYYY-MM-DD date."
            )


_NUMERIC_OR_DATE_FIELDS = (
    "stars",
    "forks",
    "followers",
    "size",
    "topics_count",
    "good_first_issues",
    "help_wanted_issues",
    "created",
    "pushed",
)


def validate_filters(filters: Filters) -> None:
    """Run every operator-shape check across all numeric/date filter fields."""

    for field_name in _NUMERIC_OR_DATE_FIELDS:
        filt = getattr(filters, field_name)
        if filt is not None:
            validate_numeric_or_date_filter(field_name, filt)


def parse_and_validate_interpretation(raw: str) -> SearchInterpretation:
    """Parse Groq's raw JSON text and validate it into a `SearchInterpretation`.

    Fails closed: any JSON parse error, any Pydantic validation error (wrong
    types, unknown keys thanks to `extra="forbid"`, malformed operator
    objects), or any operator-shape violation raises `GroqInvalidOutputError`.
    We deliberately do not attempt to repair or coerce the payload -- retrying
    with a "fixed" guess could silently misrepresent what the user asked for.
    """

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GroqInvalidOutputError() from exc

    try:
        interpretation = SearchInterpretation.model_validate(payload)
    except Exception as exc:  # pydantic ValidationError, or any other shape issue
        raise GroqInvalidOutputError() from exc

    validate_filters(interpretation.filters)

    if interpretation.needs_clarification and not (interpretation.clarification or "").strip():
        raise GroqInvalidOutputError(
            "Groq flagged needs_clarification but did not provide a clarification question."
        )

    return interpretation


def has_any_usable_filter(filters: Filters) -> bool:
    """True if at least one filter field is populated (used to short-circuit
    with `no_usable_filters` before we ever call GitHub)."""

    return any(
        value is not None
        for field, value in filters.model_dump().items()
    )
