import logfire
from sentence_transformers import SentenceTransformer

from app.config import settings


BATCH_SIZE = 50

# all-mpnet-base-v2 produces 768-dimensional embeddings
_EMBEDDING_DIM = 768

_active_model = None


# ── Model initialization ──────────────────────────────────────────────────────

def _load_model():
    """Load Hugging Face Sentence Transformer model."""
    global _active_model

    if _active_model is None:
        model_name = settings.HUGGINGFACE_EMBEDDING_MODEL

        logfire.info(
            f"Loading Hugging Face embedding model: "
            f"{model_name} ({_EMBEDDING_DIM}-dim)"
        )

        _active_model = SentenceTransformer(model_name)

        logfire.info(
            f"Hugging Face embeddings ready: {model_name}"
        )

    return _active_model


# ── Public helpers ────────────────────────────────────────────────────────────

def get_embedding_dim() -> int:
    """Return the embedding vector dimension."""
    return _EMBEDDING_DIM


# ── Batch embedding ───────────────────────────────────────────────────────────

def _embed_batch(batch: list[str]) -> list[list[float]]:
    """Generate embeddings for a batch of documents."""

    model = _load_model()

    embeddings = model.encode(
        batch,
        batch_size=BATCH_SIZE,
        show_progress_bar=False,
        normalize_embeddings=True,
    )

    return embeddings.tolist()


# ── Public API ─────────────────────────────────────────────────────────────────

def embed_query(query: str) -> list[float]:
    """Generate embedding for a single query."""

    model = _load_model()

    embedding = model.encode(
        query,
        normalize_embeddings=True,
    )

    return embedding.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts in batches."""

    _load_model()

    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]

        with logfire.span(
            "Embed batch",
            model=settings.HUGGINGFACE_EMBEDDING_MODEL,
            start=i,
            size=len(batch),
        ):
            all_embeddings.extend(_embed_batch(batch))

    return all_embeddings
