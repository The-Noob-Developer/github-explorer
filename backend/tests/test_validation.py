"""Tests for operator-shape validation and the fail-closed behavior on
malformed Groq output."""

import json

import pytest

from app.models.search_models import Filters, NumericOrDateFilter
from app.utils.errors import GroqInvalidOutputError
from app.utils.validation import parse_and_validate_interpretation, validate_filters


def test_valid_range_filter_passes():
    filters = Filters(stars=NumericOrDateFilter(op="..", value=[10, 100]))
    validate_filters(filters)  # should not raise


def test_range_filter_wrong_length_fails_closed():
    filters = Filters.model_construct(stars=NumericOrDateFilter.model_construct(op="..", value=[10]))
    with pytest.raises(GroqInvalidOutputError):
        validate_filters(filters)


def test_range_filter_min_greater_than_max_fails_closed():
    filters = Filters(stars=NumericOrDateFilter(op="..", value=[100, 10]))
    with pytest.raises(GroqInvalidOutputError):
        validate_filters(filters)


def test_range_filter_mixed_types_fails_closed():
    filters = Filters.model_construct(
        stars=NumericOrDateFilter.model_construct(op="..", value=[10, "2022-01-01"])
    )
    with pytest.raises(GroqInvalidOutputError):
        validate_filters(filters)


def test_bare_number_instead_of_operator_object_fails_closed():
    """Reproduces the exact malformed case from Section 20: `stars` sent as a
    bare number instead of the {"op": ..., "value": ...} shape."""

    raw = json.dumps({"filters": {"stars": 100}, "sort": None})
    with pytest.raises(GroqInvalidOutputError):
        parse_and_validate_interpretation(raw)


def test_invalid_json_fails_closed():
    with pytest.raises(GroqInvalidOutputError):
        parse_and_validate_interpretation("not json at all {")


def test_unknown_filter_key_fails_closed():
    raw = json.dumps({"filters": {"made_up_field": "x"}, "sort": None})
    with pytest.raises(GroqInvalidOutputError):
        parse_and_validate_interpretation(raw)


def test_needs_clarification_without_clarification_text_fails_closed():
    raw = json.dumps({"filters": {}, "needs_clarification": True, "clarification": None})
    with pytest.raises(GroqInvalidOutputError):
        parse_and_validate_interpretation(raw)


def test_well_formed_output_parses_successfully():
    raw = json.dumps(
        {
            "filters": {"language": "Python", "stars": {"op": ">", "value": 10000}},
            "sort": None,
            "unsupported_requests": [],
            "interpretation_notes": "Interpreted as: language Python, stars greater than 10000.",
            "needs_clarification": False,
            "clarification": None,
        }
    )
    interpretation = parse_and_validate_interpretation(raw)
    assert interpretation.filters.language == "Python"
    assert interpretation.filters.stars.op == ">"
    assert interpretation.filters.stars.value == 10000
