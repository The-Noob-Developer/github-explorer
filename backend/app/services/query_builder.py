"""Deterministic translation from validated `Filters` into a GitHub search
query string.

This module is a **pure function with zero I/O** on purpose: given the same
`Filters` and resolved topic, it must always produce the same string, with no
network calls, no randomness, no reliance on wall-clock time. That is what
makes it trivially unit-testable against the fixture table in Section 20,
and it is what guarantees Groq's output can never smuggle in arbitrary
GitHub query syntax -- only the fragments explicitly enumerated below are
ever emitted, in a fixed, deterministic order.
"""

from __future__ import annotations

from app.models.search_models import Filters, NumericOrDateFilter

# Field -> GitHub qualifier name, for the numeric/date comparison filters.
# Order here also fixes the order fragments are emitted in the final string.
_NUMERIC_QUALIFIER_NAMES: dict[str, str] = {
    "stars": "stars",
    "forks": "forks",
    "followers": "followers",
    "size": "size",
    "topics_count": "topics",
    "good_first_issues": "good-first-issues",
    "help_wanted_issues": "help-wanted-issues",
}

_DATE_QUALIFIER_NAMES: dict[str, str] = {
    "created": "created",
    "pushed": "pushed",
}


def _format_operator_value(qualifier: str, filt: NumericOrDateFilter) -> str:
    """Render one `NumericOrDateFilter` as `qualifier:<op><value>` or
    `qualifier:<min>..<max>` for the range operator."""

    if filt.op == "..":
        low, high = filt.value
        return f"{qualifier}:{low}..{high}"
    # ">=" / "<=" / ">" / "<" prefix the value directly; "=" has no prefix.
    prefix = "" if filt.op == "=" else filt.op
    return f"{qualifier}:{prefix}{filt.value}"


def build(filters: Filters, resolved_topic: str | None) -> str:
    """Build the GitHub search-query string from validated filters.

    `resolved_topic` is the already-resolved topic slug (from
    `topic_resolver.resolve`), or None if `filters.topic` was not set. This
    function never re-resolves or fuzzy-matches anything itself -- that is
    entirely `topic_resolver`'s job, kept separate so this function can stay
    pure and so topic resolution (which needs I/O and fuzzy matching) doesn't
    contaminate the one piece of the pipeline that must be side-effect free.

    Fragments are joined in the exact order of Section 4's mapping table so
    output is deterministic and directly comparable in tests.
    """

    fragments: list[str] = []

    if resolved_topic:
        fragments.append(f"topic:{resolved_topic}")

    if filters.keyword:
        fragments.append(filters.keyword)
        if filters.search_in:
            fragments.append(f"in:{','.join(filters.search_in)}")

    if filters.language:
        fragments.append(f"language:{filters.language}")

    if filters.license:
        fragments.append(f"license:{filters.license}")

    if filters.user:
        fragments.append(f"user:{filters.user}")

    if filters.org:
        fragments.append(f"org:{filters.org}")

    if filters.repo:
        fragments.append(f"repo:{filters.repo}")

    if filters.archived is not None:
        fragments.append(f"archived:{'true' if filters.archived else 'false'}")

    if filters.is_public is not None:
        fragments.append("is:public" if filters.is_public else "is:private")

    if filters.is_sponsorable:
        fragments.append("is:sponsorable")

    if filters.mirror is not None:
        fragments.append(f"mirror:{'true' if filters.mirror else 'false'}")

    if filters.template is not None:
        fragments.append(f"template:{'true' if filters.template else 'false'}")

    if filters.has_funding_file:
        fragments.append("has:funding-file")

    for field_name, qualifier in _NUMERIC_QUALIFIER_NAMES.items():
        filt = getattr(filters, field_name)
        if filt is not None:
            fragments.append(_format_operator_value(qualifier, filt))

    for field_name, qualifier in _DATE_QUALIFIER_NAMES.items():
        filt = getattr(filters, field_name)
        if filt is not None:
            fragments.append(_format_operator_value(qualifier, filt))

    if filters.props:
        # Best-effort custom-properties search. GitHub's exact syntax for
        # organization custom properties in repository search is not
        # publicly documented as of this writing; `props.<key>:<value>` is
        # our best-effort assumption, kept consistent for testability.
        for key, value in filters.props.items():
            fragments.append(f"props.{key}:{value}")

    return " ".join(fragments)
