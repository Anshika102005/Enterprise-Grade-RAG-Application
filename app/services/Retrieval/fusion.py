"""
Reciprocal Rank Fusion (RRF) for hybrid retrieval.

Dense (semantic) and sparse (BM25 lexical) searches each return a ranked list
of candidate ids. RRF combines them into one ranking without needing to
normalise their incomparable scores — it only uses rank position:

    score(d) = Σ_r  1 / (k + rank_r(d))

k (default 60) dampens the influence of top ranks so a single retriever cannot
dominate. This is the same fusion used by Qdrant's server-side RRF and is the
industry default for hybrid search.
"""


def reciprocal_rank_fusion(
    rankings,
    k: int = 60,
    weights=None,
):
    """
    Fuse several ranked id lists into one.

    Args:
        rankings: list of ranked id lists, e.g. [[dense ids...], [bm25 ids...]].
                  Ids may be strings or ints.
        k: RRF damping constant (higher = flatter weighting).
        weights: optional per-ranking weights (defaults to all 1.0).

    Returns:
        List of (doc_id, fused_score) sorted by descending score. Ties are
        broken by id for deterministic output.
    """
    if not rankings:
        return []

    if weights is None:
        weights = [1.0] * len(rankings)

    scores: dict = {}
    for ranking, weight in zip(rankings, weights):
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0.0) + weight * (1.0 / (k + rank + 1))

    return sorted(scores.items(), key=lambda kv: (-kv[1], str(kv[0])))
