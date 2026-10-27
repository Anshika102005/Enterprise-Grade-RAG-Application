"""
Hugging Face environment defaults — import this FIRST, before qdrant_client,
sentence-transformers, fastembed, or huggingface_hub.

This project only ever loads *public* models (all-mpnet-base-v2, Qdrant/bm25).
A stale/expired token stored by `huggingface-cli login` (~/.cache/huggingface/token)
makes huggingface_hub send an invalid Authorization header, so public downloads
fail with a 401 "Repository Not Found" — which is exactly the failure that
breaks BM25 sparse-vector inference.

`HF_HUB_DISABLE_IMPLICIT_TOKEN=1` drops that stored token while still honouring
an explicitly exported `HF_TOKEN` (set one only if you use gated models).
"""
import os

os.environ.setdefault("HF_HUB_DISABLE_IMPLICIT_TOKEN", "1")
