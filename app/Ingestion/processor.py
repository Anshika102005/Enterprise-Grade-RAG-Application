import app._hf_env  # noqa: F401 — must precede qdrant_client/fastembed (BM25 inference)
from logfire._internal import collect_system_info
import json
from qdrant_client import QdrantClient
import logfire
import os 
import sys
import traceback

from qdrant_client import models
import uuid
from app.config import settings
from app.services.Retrieval.embeddings import embed_texts, get_embedding_dim
from app.services.Retrieval.schema import DENSE_VECTOR_NAME, SPARSE_VECTOR_NAME, BM25_MODEL
from app.Ingestion.Loaders.pdf import parse_pdf
from app.Ingestion.Loaders.html import parse_html
from app.Ingestion.Loaders.text import parse_text
from app.Ingestion.Chunking.splitter import chunk_text

import logfire

logfire.configure(
    service_name="enterprise-ingestion-service",
    send_to_logfire="if-token-present",
    token=settings.LOGFIRE_TOKEN
)


# Local folder where parsed + chunked JSON metadata is saved (replaces GCS processed bucket)
PROCESSED_DATA_DIR = "processed_data"   

# Initialize Qdrant Client
qdrant_client = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY,
    timeout=180
)


def preflight_sparse_model() -> bool:
    """
    Load the BM25 sparse model once, up front, so a broken environment fails
    loudly with a fixable message instead of failing per file. (Logfire scrubs
    auth-looking download errors, which otherwise hides the real cause.)
    """
    try:
        from fastembed import SparseTextEmbedding

        SparseTextEmbedding(model_name=BM25_MODEL)
        logfire.info(f"BM25 sparse model ready ({BM25_MODEL}).")
        return True
    except Exception as e:
        logfire.error(f"BM25 sparse model unavailable: {type(e).__name__}")
        print(
            "\n[INGESTION ERROR] Could not load the BM25 sparse model "
            f"'{BM25_MODEL}'.\n"
            f"  {type(e).__name__}: {e}\n"
            "  Most common cause: an expired Hugging Face token stored by\n"
            "  `huggingface-cli login` (~/.cache/huggingface/token).\n"
            "  Fix: run `huggingface-cli logout` (or export a valid HF_TOKEN), "
            "then retry.\n",
            file=sys.stderr,
        )
        return False


def save_processed_locally(data: dict, source_type: str, filename: str) -> str:
    """Save parsed chunk metadata as JSON in processed_data/<source_type>/."""
    folder = os.path.join(PROCESSED_DATA_DIR, source_type)
    os.makedirs(folder, exist_ok=True)
    dest = os.path.join(folder, f"{filename}.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return dest


def process_file(file_path: str, filename: str, source_type: str):
    """Parse → chunk → save locally → embed → index in Qdrant."""
    with logfire.span("Processing File", file=filename, source=source_type):
        try:
            # 1. Extract text based on file extension
            ext = filename.lower().rsplit(".", 1)[-1]
            if ext == "pdf":
                full_text = parse_pdf(file_path)
            elif ext == "html":
                    full_text = parse_html(file_path)
            elif ext in ("txt","md"):
                full_text = parse_text(file_path)
            elif ext in ("docx", "pptx"):
                # pyrefly: ignore [missing-import]
                from app.Ingestion.Loaders.office import parse_office
                full_text = parse_office(file_path)
            else:
                logfire.warning(f"Skipping unsupported file type: {filename}")
                return

            if not full_text or not full_text.strip():
                logfire.warning(f"No text extracted from {filename} — skipping.")
                return

            # 2. Chunk text
            chunks = chunk_text(full_text)
            if not chunks:
                return

            # 3. Save processed metadata locally
            processed_data = {
                "filename": filename,
                "source_type": source_type,
                "chunks": chunks,
            }
            local_path = save_processed_locally(processed_data, source_type, filename)
            logfire.info(f"Saved processed data → {local_path}")

            # 4. Embed and index in Qdrant
            with logfire.span("Vectorizing & Indexing"):
                embeddings = embed_texts(chunks)
                points = [
                    models.PointStruct(
                        id=str(uuid.uuid4()),
                        vector={
                            DENSE_VECTOR_NAME: vector,
                            SPARSE_VECTOR_NAME: models.Document(
                                text=chunk, model=BM25_MODEL
                            ),
                        },
                        payload={
                            "text": chunk,
                            "source": filename,
                            "source_type": source_type,
                        },
                    )
                    for chunk, vector in zip(chunks, embeddings)
                ]

                qdrant_client.upsert(
                    collection_name=settings.QDRANT_COLLECTION,
                    points=points,
                )
                logfire.info(f"Indexed {len(points)} points to Qdrant from {filename}.")

        except Exception as e:
            # Logfire scrubs exception text that looks like auth/secrets, which
            # hides the real error — print the full traceback for the operator.
            logfire.error(f"Failed to process {filename}: {type(e).__name__}")
            traceback.print_exc()


def process_directory(dir_path: str, source_type: str):
    """Process every file in a directory."""
    with logfire.span("Scanning Directory", path=dir_path, source=source_type):
        files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
        logfire.info(f"Found {len(files)} files in {dir_path}.")
        for filename in files:
            process_file(os.path.join(dir_path, filename), filename, source_type)


def run_universal_ingestion(base_dir: str, explicit_source_type: str = None, wipe: bool = False):
    """
    Scan base_dir, map sub-folders to source types, and ingest all documents.
    Pass --wipe to drop and recreate the Qdrant collection before ingestion.
    """
    if not preflight_sparse_model():
        raise RuntimeError(
            "Hybrid ingestion requires the BM25 sparse model. See the error above."
        )

    with logfire.span("Universal Ingestion Started", base_directory=base_dir):

        # Wipe collection if requested
        if wipe:
            with logfire.span("Wiping Collection"):
                if qdrant_client.collection_exists(settings.QDRANT_COLLECTION):
                    qdrant_client.delete_collection(settings.QDRANT_COLLECTION)
                    logfire.info(f"Collection '{settings.QDRANT_COLLECTION}' deleted.")

        # Recreate collection — dimension resolved at runtime after embedding model probe
        if not qdrant_client.collection_exists(settings.QDRANT_COLLECTION):
            dim = get_embedding_dim()
            # Hybrid schema: named dense vector + sparse BM25 vector, so the
            # retriever can run semantic and lexical search over the same points.
            qdrant_client.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config={
                    DENSE_VECTOR_NAME: models.VectorParams(
                        size=dim,
                        distance=models.Distance.COSINE,
                    ),
                },
                sparse_vectors_config={
                    SPARSE_VECTOR_NAME: models.SparseVectorParams(),
                },
            )
            logfire.info(
                f"Created hybrid collection '{settings.QDRANT_COLLECTION}' "
                f"({dim}-dim dense + bm25 sparse)."
            )

        # Route to sub-folders or treat the whole dir as one source
        subdirs = [
            d for d in os.listdir(base_dir)
            if os.path.isdir(os.path.join(base_dir, d))
        ]

        if not subdirs:
            if explicit_source_type:
                source_type = explicit_source_type
            else:
                base_name = os.path.basename(os.path.normpath(base_dir)).lower()
                source_type = (
                    "true" if "true" in base_name
                    else "noisy" if "noisy" in base_name
                    else "general"
                )
            logfire.info(f"No sub-folders found — processing '{base_dir}' as '{source_type}'.")
            process_directory(base_dir, source_type)
        else:
            for subdir in subdirs:
                source_type = (
                    "true" if "true" in subdir.lower()
                    else "noisy" if "noisy" in subdir.lower()
                    else subdir
                )
                process_directory(os.path.join(base_dir, subdir), source_type)


if __name__ == "__main__":
    wipe_requested = "--wipe" in sys.argv
    clean_args = [a for a in sys.argv if a != "--wipe"]

    target_dir = clean_args[1] if len(clean_args) > 1 else "DATA"
    explicit_type = clean_args[2] if len(clean_args) > 2 else None

    if not os.path.exists(target_dir):
        print(f"Error: path '{target_dir}' does not exist.")
        sys.exit(1)

    with logfire.span(
        "Universal Ingestion",
        target_dir=target_dir,
        source_type=explicit_type,
        wipe=wipe_requested,
    ):
        run_universal_ingestion(
            target_dir,
            explicit_source_type=explicit_type,
            wipe=wipe_requested,
        )

    logfire.info("Ingestion job completed.")


    ##It takes raw True/Noisy documents → extracts their text → splits text into chunks → saves processed metadata
    ##→ converts chunks into embeddings → stores those embeddings + metadata in Qdrant for later RAG retrieval.



#Point
# ├── id: "a8f2..."
# ├── vector: [768 numbers]
# └── payload
#     ├── text: "Kubernetes uses..."
#     ├── source: "architecture.pptx"
#     └── source_type: "true"
