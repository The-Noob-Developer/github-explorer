"""Unit tests for the pure `query_builder.build` function.

Every row asserts the exact expected query string, matching Section 20's
fixture table literally -- not just "returns something."
"""

from app.models.search_models import Filters, NumericOrDateFilter
from app.services.query_builder import build


def test_language_only():
    filters = Filters(language="Python")
    assert build(filters, resolved_topic=None) == "language:Python"


def test_resolved_topic_with_stars_filter():
    filters = Filters(stars=NumericOrDateFilter(op=">", value=1000))
    assert build(filters, resolved_topic="react") == "topic:react stars:>1000"


def test_created_after_date():
    filters = Filters(created=NumericOrDateFilter(op=">", value="2022-01-01"))
    assert build(filters, resolved_topic=None) == "created:>2022-01-01"


def test_user_filter():
    filters = Filters(user="The-Noob-Developer")
    assert build(filters, resolved_topic=None) == "user:The-Noob-Developer"


def test_forks_range():
    filters = Filters(
        language="JavaScript", forks=NumericOrDateFilter(op="..", value=[100, 500])
    )
    assert build(filters, resolved_topic=None) == "language:JavaScript forks:100..500"


def test_archived_topic():
    filters = Filters(archived=True)
    assert build(filters, resolved_topic="machine-learning") == "topic:machine-learning archived:true"


def test_is_public_with_stars():
    filters = Filters(is_public=True, stars=NumericOrDateFilter(op=">", value=10000))
    assert build(filters, resolved_topic=None) == "is:public stars:>10000"


def test_keyword_with_search_in():
    filters = Filters(keyword="parser", search_in=["name", "description"])
    assert build(filters, resolved_topic=None) == "parser in:name,description"


def test_boolean_flags_omit_false_only_true_fragments():
    filters = Filters(is_sponsorable=False, has_funding_file=False)
    assert build(filters, resolved_topic=None) == ""


def test_boolean_flags_true_fragments():
    filters = Filters(is_sponsorable=True, has_funding_file=True, mirror=True, template=False)
    assert build(filters, resolved_topic=None) == "is:sponsorable mirror:true template:false has:funding-file"


def test_props_fragment():
    filters = Filters(props={"team": "platform"})
    assert build(filters, resolved_topic=None) == "props.team:platform"


def test_full_ordering_of_all_fragment_types():
    filters = Filters(
        keyword="cli",
        search_in=["readme"],
        language="Go",
        license="mit",
        user="octocat",
        org="github",
        repo="octocat/hello-world",
        archived=False,
        is_public=True,
        mirror=False,
        template=True,
        stars=NumericOrDateFilter(op=">=", value=50),
        created=NumericOrDateFilter(op="<", value="2023-06-01"),
    )
    result = build(filters, resolved_topic="cli-tools")
    expected = (
        "topic:cli-tools cli in:readme language:Go license:mit user:octocat org:github "
        "repo:octocat/hello-world archived:false is:public mirror:false template:true "
        "stars:>=50 created:<2023-06-01"
    )
    assert result == expected
