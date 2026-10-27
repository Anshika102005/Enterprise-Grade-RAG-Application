"""Unit tests for parse_grade_response (pure, no external deps)."""
from app.agents.nodes.grading import parse_grade_response


def test_plain_json():
    idx, conf = parse_grade_response('{"relevant": [0, 2], "confidence": 0.9}', 3)
    assert idx == [0, 2]
    assert conf == 0.9


def test_fenced_json_block():
    text = '```json\n{"relevant": [1], "confidence": 0.5}\n```'
    idx, conf = parse_grade_response(text, 3)
    assert idx == [1]
    assert conf == 0.5


def test_json_with_surrounding_prose():
    text = 'Sure! Here is the verdict: {"relevant": [0], "confidence": 0.7} Enjoy.'
    idx, conf = parse_grade_response(text, 2)
    assert idx == [0]
    assert conf == 0.7


def test_malformed_fails_open_keeps_all_docs():
    idx, conf = parse_grade_response("not json at all", 4)
    assert idx == [0, 1, 2, 3]
    assert conf == 0.5


def test_out_of_range_indices_are_dropped():
    idx, _ = parse_grade_response('{"relevant": [0, 9, -1], "confidence": 0.5}', 3)
    assert idx == [0]


def test_non_numeric_indices_are_ignored():
    idx, _ = parse_grade_response('{"relevant": ["0", "abc", 2], "confidence": 0.5}', 3)
    assert idx == [0, 2]


def test_confidence_is_clamped():
    _, high = parse_grade_response('{"relevant": [0], "confidence": 5.0}', 1)
    _, low = parse_grade_response('{"relevant": [0], "confidence": -3.0}', 1)
    assert high == 1.0
    assert low == 0.0


def test_missing_confidence_defaults_neutral():
    _, conf = parse_grade_response('{"relevant": [0]}', 1)
    assert conf == 0.5


def test_no_documents_returns_empty():
    assert parse_grade_response('{"relevant": []}', 0) == ([], 0.0)


def test_non_dict_json_fails_open():
    idx, conf = parse_grade_response("[1, 2, 3]", 3)
    assert idx == [0, 1, 2]
    assert conf == 0.5
