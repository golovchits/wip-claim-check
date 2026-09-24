import pytest

from app.checker import parse_verdict, run_output_check

PASSAGES = [
    {"id": 1, "page": 1, "text": "Keys come from the environment, never committed, never baked in."},
    {"id": 2, "page": 4, "text": "Use free tiers throughout."},
]


def test_clean_answer_has_no_flags():
    text = 'SUPPORTED The brief says keys are "never   COMMITTED".'

    result = run_output_check(text, ["1"], PASSAGES)

    assert result == {
        "verdict": "supported",
        "explanation": 'The brief says keys are "never   COMMITTED".',
        "cited_ids": [1],
        "flags": [],
    }


def test_unknown_id_is_dropped_and_flagged():
    result = run_output_check("SUPPORTED Yes.", ["1", "99"], PASSAGES)

    assert result["cited_ids"] == [1]
    assert result["flags"] == ["unknown passage ID: 99"]


def test_fake_quote_is_flagged_with_curly_quotes():
    result = run_output_check("CONTRADICTED It says “use paid tiers”.", ["2"], PASSAGES)

    assert result["flags"] == ["unverified quote: use paid tiers"]


def test_trailing_punctuation_inside_quote_is_ignored():
    result = run_output_check('SUPPORTED It says "never committed, never baked in,".', ["1"], PASSAGES)

    assert result["flags"] == []


def test_missing_verdict_word_needs_review():
    result = run_output_check("I think this is true.", ["1"], PASSAGES)

    assert result["verdict"] == "needs_review"
    assert result["flags"] == ["missing verdict word"]


def test_supported_without_citations_needs_review():
    result = run_output_check("SUPPORTED Trust me.", [], PASSAGES)

    assert result["verdict"] == "needs_review"
    assert result["flags"] == ["no citations"]


def test_not_found_without_citations_is_accepted():
    result = run_output_check("NOT_FOUND No passage mentions Berlin.", [], PASSAGES)

    assert result["verdict"] == "not_found"
    assert result["flags"] == []


@pytest.mark.parametrize("text, verdict", [
    ("**SUPPORTED** Yes.", "supported"),
    ("Verdict: MIXED Partly.", "mixed"),
    ("**Verdict:** _CONTRADICTED_ No.", "contradicted"),
    ("NOT_FOUND. Nothing.", "not_found"),
    ("Probably SUPPORTED.", None),
])
def test_verdict_word_parsing(text, verdict):
    assert parse_verdict(text)[0] == verdict
