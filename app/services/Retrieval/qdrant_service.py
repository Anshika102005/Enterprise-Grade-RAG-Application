import app._hf_env  # noqa: F401 — must precede qdrant_client/fastembed (BM25 inference)
import logfire
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

from app.config import settings
from app.services.Retrieval.embeddings import embed_query
from app.services.Retrieval.fusion import reciprocal_rank_fusion
from app.services.Retrieval.schema import (
    DENSE_VECTOR_NAME,
    SPARSE_VECTOR_NAME,
    BM25_MODEL,
)


# Initialize Qdrant Client
client = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY
)


class RetrievalUnavailableError(RuntimeError):
    """
    Raised when the vector database could not be reached at all.

    A query that legitimately matched nothing returns an empty list; an outage
    raises this instead, so the agent can report the difference to the user
    rather than presenting an infrastructure failure as "no relevant context".
    """


def _point_id(point):
    return str(point.id)


def _result_from_points(points, limit):
    """Map Qdrant scored points to the public result shape."""
    return [
        {
            "content": point.payload.get("text", ""),
            "source": point.payload.get("source", "Unknown"),
            "source_type": point.payload.get("source_type", "Unknown"),
            "score": point.score,
        }
        for point in points[:limit]
    ]


def _dense_search(query: str, limit: int):
    """Semantic search over the named 'dense' vector."""
    query_vector = embed_query(query)
    response = client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=query_vector,
        using=DENSE_VECTOR_NAME,
        limit=limit,
        with_payload=True,
    )
    return response.points


def _sparse_search(query: str, limit: int):
    """Lexical BM25 search over the named 'bm25' sparse vector."""
    response = client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=rest.Document(text=query, model=BM25_MODEL),
        using=SPARSE_VECTOR_NAME,
        limit=limit,
        with_payload=True,
    )
    return response.points


def _legacy_dense_search(query: str, limit: int):
    """
    Fallback for a collection created before hybrid ingestion (single,
    unnamed dense vector). Keeps the service usable during migration.
    """
    query_vector = embed_query(query)
    response = client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=query_vector,
        limit=limit,
        with_payload=True,
    )
    return response.points


def search_enterprise_knowledge(query: str, limit: int | None = None):
    """
    Hybrid retrieval: dense semantic + BM25 lexical, fused with Reciprocal
    Rank Fusion, returned as a single ranked list.

    Falls back to dense-only (or the legacy unnamed vector) so a missing
    sparse index never takes retrieval down.
    """
    limit = limit or settings.RETRIEVAL_FUSED_TOP_K

    try:
        with logfire.span("🔀 Hybrid Retrieval (Dense + BM25 → RRF)"):
            dense_points = _dense_search(query, settings.RETRIEVAL_DENSE_TOP_K)
            logfire.info(f"Dense retrieved {len(dense_points)} candidates.")

            try:
                sparse_points = _sparse_search(query, settings.RETRIEVAL_SPARSE_TOP_K)
                logfire.info(f"BM25 retrieved {len(sparse_points)} candidates.")
            except Exception as e:
                logfire.warning(f"BM25 search unavailable ({e}) — dense-only.")
                return _result_from_points(dense_points, limit)

            # Index every point by id so the fused ranking can resolve payloads.
            by_id = {_point_id(p): p for p in dense_points}
            by_id.update({_point_id(p): p for p in sparse_points})

            rankings = [
                [_point_id(p) for p in dense_points],
                [_point_id(p) for p in sparse_points],
            ]
            fused = reciprocal_rank_fusion(rankings, k=settings.RRF_K)

            results = []
            for doc_id, fused_score in fused[:limit]:
                point = by_id.get(doc_id)
                if point is None:
                    continue
                results.append({
                    "content": point.payload.get("text", ""),
                    "source": point.payload.get("source", "Unknown"),
                    "source_type": point.payload.get("source_type", "Unknown"),
                    "score": fused_score,
                })

            logfire.info(f"RRF fused {len(fused)} unique candidates → top {len(results)}.")
            return results

    except Exception as e:
        logfire.error(f"❌ Hybrid Qdrant search failed: {e} — trying legacy dense search.")
        try:
            return _result_from_points(
                _legacy_dense_search(query, settings.RETRIEVAL_FUSED_TOP_K), limit
            )
        except Exception as legacy_error:
            # Both the hybrid and the legacy path failed: the vector DB itself is
            # unreachable. Surface it — retrying the query cannot fix this.
            logfire.error(f"❌ Qdrant unreachable: {legacy_error}")
            raise RetrievalUnavailableError(str(legacy_error)) from legacy_error
