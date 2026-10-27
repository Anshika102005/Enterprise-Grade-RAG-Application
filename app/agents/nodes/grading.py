"""
Pure parsing logic for the Self-RAG grader verdict.

Kept free of LangChain / logfire / network imports so it can be unit-tested
with nothing but pytest.
"""
import json
import re


def parse_grade_response(text: str, n_docs: int) -> tuple[list[int], float]:
    """
    Defensively parse the grader LLM's JSON verdict.

    Returns (relevant_indices, confidence). On any malformed output we
    fail-open: keep every passage and report neutral confidence, so a flaky
    grader never degrades a good answer.
    """
    if n_docs <= 0:
        return [], 0.0

    raw = (text or "").strip()
    # Strip ```json ... ``` fences if the model added them.
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()

    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not match:
        return list(range(n_docs)), 0.5

    try:
        data = json.loads(match.group(0))
    except (json.JSONDecodeError, TypeError):
        return list(range(n_docs)), 0.5

    if not isinstance(data, dict):
        return list(range(n_docs)), 0.5

    raw_relevant = data.get("relevant", [])
    relevant: set[int] = set()
    if isinstance(raw_relevant, list):
        for item in raw_relevant:
            try:
                idx = int(item)
            except (TypeError, ValueError):
                continue
            if 0 <= idx < n_docs:
                relevant.add(idx)

    try:
        confidence = float(data.get("confidence", 0.5))
    except (TypeError, ValueError):
        confidence = 0.5
    confidence = min(1.0, max(0.0, confidence))

    return sorted(relevant), confidence
