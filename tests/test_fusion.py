"""Unit tests for reciprocal_rank_fusion (pure, no external deps)."""
from app.services.Retrieval.fusion import reciprocal_rank_fusion


def test_single_ranking_preserves_order():
    fused = reciprocal_rank_fusion([["a", "b", "c"]], k=60)
    assert [doc_id for doc_id, _ in fused] == ["a", "b", "c"]


def test_document_in_both_rankings_wins():
    # x appears in both lists (rank 0 and rank 1); y and c only once.
    fused = reciprocal_rank_fusion([["x", "c"], ["y", "x"]], k=60)
    assert fused[0][0] == "x"


def test_scores_match_formula():
    fused = dict(reciprocal_rank_fusion([["a"]], k=60))
    assert fused["a"] == 1.0 / 61


def test_empty_input_returns_empty():
    assert reciprocal_rank_fusion([]) == []
    assert reciprocal_rank_fusion([[], []]) == []


def test_weights_bias_the_ranking():
    fused = reciprocal_rank_fusion([["a"], ["b"]], k=60, weights=[2.0, 1.0])
    assert fused[0][0] == "a"
    assert fused[0][1] > fused[1][1]


def test_ties_break_deterministically():
    fused = reciprocal_rank_fusion([["b"], ["a"]], k=60)
    # equal scores -> sorted by string id
    assert [doc_id for doc_id, _ in fused] == ["a", "b"]
