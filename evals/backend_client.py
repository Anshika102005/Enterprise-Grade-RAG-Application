"""
Collect RAG outputs to evaluate.

Two modes:
  1. Live  — POST each question to the running FastAPI backend (/query) and
             capture the answer + retrieved contexts it returns.
  2. Fixture — replay previously recorded samples so metrics can be recomputed
             offline / in CI without any external services.

Both produce the same sample shape:
    {"question", "answer", "contexts": [...], "ground_truth"}
"""
import json
import os
import time
import uuid
from pathlib import Path

import requests

from evals.dataset import EvalItem

DEFAULT_BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def query_backend(question: str, base_url: str | None = None, timeout: int = 90) -> dict:
    """Send one question to the backend and return the parsed JSON response."""
    base_url = base_url or DEFAULT_BASE_URL
    response = requests.post(
        f"{base_url}/query",
        # Unique thread_id per question so memory never bleeds between items.
        json={"q": question, "thread_id": f"eval-{uuid.uuid4().hex[:8]}"},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def collect_samples(
    items: list[EvalItem],
    base_url: str | None = None,
    sleep: float = 0.5,
) -> list[dict]:
    """Run every golden item through the live backend."""
    samples = []
    for i, item in enumerate(items, start=1):
        print(f"  [{i}/{len(items)}] {item.question[:70]}...")
        data = query_backend(item.question, base_url=base_url)
        samples.append(
            {
                "question": item.question,
                "answer": data.get("answer") or "",
                "contexts": data.get("sources") or [],
                "ground_truth": item.ground_truth,
            }
        )
        if sleep:
            time.sleep(sleep)
    return samples


def save_samples(samples: list[dict], path: Path | str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(samples, indent=2, ensure_ascii=False), encoding="utf-8")


def load_samples(path: Path | str) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
