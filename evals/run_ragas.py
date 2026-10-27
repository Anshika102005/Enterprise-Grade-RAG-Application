"""
RAGAS evaluation runner.

Usage:
    # Against the running backend, record the raw samples for later replay
    python -m evals.run_ragas --record evals/fixtures/samples.json

    # Replay recorded samples (offline — no backend, no Qdrant needed)
    python -m evals.run_ragas --samples evals/fixtures/samples.json

Exits non-zero if any metric falls below its threshold, so it works as a CI gate.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import evals._compat  # noqa: F401  — MUST precede `import ragas`

from evals.backend_client import collect_samples, load_samples, save_samples
from evals.dataset import load_dataset
from evals.judge import get_ragas_embeddings, get_ragas_llm
from evals.thresholds import RAGAS_THRESHOLDS

RESULTS_DIR = Path(__file__).parent / "results"


def _build_dataset(samples: list[dict]):
    from ragas import EvaluationDataset, SingleTurnSample

    return EvaluationDataset(
        samples=[
            SingleTurnSample(
                user_input=s["question"],
                response=s["answer"],
                retrieved_contexts=s["contexts"],
                reference=s["ground_truth"],
            )
            for s in samples
        ]
    )


def _get_samples(args) -> list[dict]:
    if args.samples:
        print(f"Replaying recorded samples from {args.samples}")
        return load_samples(args.samples)

    items = load_dataset(args.dataset)
    print(f"Running {len(items)} golden questions through the backend...")
    samples = collect_samples(items, base_url=args.base_url)
    if args.record:
        save_samples(samples, args.record)
        print(f"Recorded samples -> {args.record}")
    return samples


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the RAGAS evaluation.")
    parser.add_argument("--samples", help="Replay recorded samples JSON instead of calling the backend.")
    parser.add_argument("--record", help="Write collected samples to this JSON path for replay.")
    parser.add_argument("--dataset", default=None, help="Path to a golden dataset JSONL file.")
    parser.add_argument("--base-url", default=None, help="Backend base URL (defaults to $BACKEND_URL).")
    args = parser.parse_args()

    samples = _get_samples(args)

    from ragas import evaluate
    from ragas.metrics import (
        answer_relevancy,
        context_precision,
        context_recall,
        faithfulness,
    )

    metrics = [faithfulness, answer_relevancy, context_precision, context_recall]
    metric_names = [m.name for m in metrics]

    print("Evaluating with RAGAS (this makes judge LLM calls)...")
    result = evaluate(
        _build_dataset(samples),
        metrics=metrics,
        llm=get_ragas_llm(),
        embeddings=get_ragas_embeddings(),
        raise_exceptions=False,
        show_progress=True,
    )

    df = result.to_pandas()
    summary = {
        name: round(float(df[name].mean()), 4)
        for name in metric_names
        if name in df.columns
    }

    print("\n=== RAGAS Results ===")
    for name, score in summary.items():
        threshold = RAGAS_THRESHOLDS.get(name)
        flag = ""
        if threshold is not None:
            flag = "  PASS" if score >= threshold else f"  FAIL (< {threshold})"
        print(f"  {name:<20} {score:.3f}{flag}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report = {
        "generated_at": stamp,
        "num_samples": len(samples),
        "metrics": summary,
        "thresholds": RAGAS_THRESHOLDS,
    }
    out_path = RESULTS_DIR / f"ragas_{stamp}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nReport written -> {out_path}")

    failures = [
        (name, score, RAGAS_THRESHOLDS[name])
        for name, score in summary.items()
        if name in RAGAS_THRESHOLDS and score < RAGAS_THRESHOLDS[name]
    ]
    if failures:
        print("\n❌ Quality gate failed:")
        for name, score, threshold in failures:
            print(f"   {name}: {score:.3f} < {threshold}")
        return 1

    print("\n✅ All RAGAS metrics passed their thresholds.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
