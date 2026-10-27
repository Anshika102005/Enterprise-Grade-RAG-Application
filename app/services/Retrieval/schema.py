"""
Shared vector schema for the hybrid Qdrant collection.

The collection stores two named vectors per point:
  - "dense": the semantic embedding (all-mpnet-base-v2, 768-dim, cosine)
  - "bm25":  a sparse BM25 lexical vector produced by Qdrant's inference

Keeping the names in one place means ingestion and retrieval can never drift
out of sync.
"""

DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "bm25"
BM25_MODEL = "Qdrant/bm25"
