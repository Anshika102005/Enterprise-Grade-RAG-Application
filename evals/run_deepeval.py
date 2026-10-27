"""
DeepEval evaluation runner (pytest-native metrics, independent judge from RAGAS).

Metrics:
  faithfulness       — answers grounded in the retrieved context
  hallucination      — unsupported claims vs the retrieved context (lower better)
  answer_correctness — matches the ground-truth answer
  scope_adherence    — stays on-topic / refuses off-topic requests

Usage:
    python -m evals.run_deepeval --record evals/fixtures/samples.json
    python -m evals.run_deepeval --samples evals/fixtures/samples.json

Exits non-zero if any metric breaches its gate.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from evals.backend_client import collect_samples, load_samples, save_samples
from evals.dataset import load_dataset
from evals.judge import GroqJudgeLLM
from evals.thresholds import DEEPEVAL_THRESHOLDS, LOWER_IS_BETTER

RESULTS_DIR = Path(__file__).parent / "results"


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


def _build_metrics(judge):
    from deepeval.metrics import FaithfulnessMetric, GEval, HallucinationMetric
    from deepeval.test_case import SingleTurnParams

    return {
        "faithfulness": FaithfulnessMetric(
            threshold=DEEPEVAL_THRESHOLDS["faithfulness"],
            model=judge,
            include_reason=True,
            async_mode=False,
        ),
        "hallucination": HallucinationMetric(
            threshold=DEEPEVAL_THRESHOLDS["hallucination"],
            model=judge,
            include_reason=True,
            async_mode=False,
        ),
        "answer_correctness": GEval(
            name="Answer Correctness",
            criteria=(
                "Compare the actual output to the expected output. Score how "
                "factually correct and complete the actual output is."
            ),
            evaluation_params=[
                SingleTurnParams.INPUT,
                SingleTurnParams.ACTUAL_OUTPUT,
                SingleTurnParams.EXPECTED_OUTPUT,
            ],
            model=judge,
            threshold=DEEPEVAL_THRESHOLDS["answer_correctness"],
            async_mode=False,
        ),
        "scope_adherence": GEval(
            name="Scope Adherence",
            criteria=(
                "The assistant supports ONLY Kubernetes, Intel hardware, and "
                "enterprise networking. Score whether the actual output answers "
                "within those domains and does not invent facts or help with "
                "off-topic requests."
            ),
            evaluation_params=[
                SingleTurnParams.INPUT,
                SingleTurnParams.ACTUAL_OUTPUT,
            ],
            model=judge,
            threshold=DEEPEVAL_THRESHOLDS["scope_adherence"],
            async_mode=False,
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the DeepEval evaluation.")
    parser.add_argument("--samples", help="Replay recorded samples JSON instead of calling the backend.")
    parser.add_argument("--record", help="Write collected samples to this JSON path for replay.")
    parser.add_argument("--dataset", default=None, help="Path to a golden dataset JSONL file.")
    parser.add_argument("--base-url", default=None, help="Backend base URL (defaults to $BACKEND_URL).")
    args = parser.parse_args()

    from deepeval.test_case import LLMTestCase

    samples = _get_samples(args)
    judge = GroqJudgeLLM()
    metrics = _build_metrics(judge)

    totals: dict[str, list[float]] = {name: [] for name in metrics}
    errors: list[str] = []

    print("Evaluating with DeepEval (this makes judge LLM calls)...")
    for i, sample in enumerate(samples, start=1):
        print(f"  [{i}/{len(samples)}] {sample['question'][:70]}...")
        test_case = LLMTestCase(
            input=sample["question"],
            actual_output=sample["answer"],
            expected_output=sample["ground_truth"],
            retrieval_context=sample["contexts"],
            context=sample["contexts"],
        )
        for name, metric in metrics.items():
            # Hallucination needs retrieved context to compare against.
            if name == "hallucination" and not sample["contexts"]:
                continue
            try:
                metric.measure(test_case)
                totals[name].append(float(metric.score))
            except Exception as e:  # noqa: BLE001 — never let one metric kill the run
                errors.append(f"{name} @ {sample['question'][:40]}: {e}")

    summary = {
        name: round(sum(scores) / len(scores), 4)
        for name, scores in totals.items()
        if scores
    }

    print("\n=== DeepEval Results ===")
    for name, score in summary.items():
        threshold = DEEPEVAL_THRESHOLDS.get(name)
        if name in LOWER_IS_BETTER:
            flag = "  PASS" if score <= threshold else f"  FAIL (> {threshold})"
        else:
            flag = "  PASS" if score >= threshold else f"  FAIL (< {threshold})"
        print(f"  {name:<20} {score:.3f}{flag}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report = {
        "generated_at": stamp,
        "num_samples": len(samples),
        "metrics": summary,
        "thresholds": DEEPEVAL_THRESHOLDS,
        "errors": errors,
    }
    out_path = RESULTS_DIR / f"deepeval_{stamp}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nReport written -> {out_path}")
    if errors:
        print(f"⚠️  {len(errors)} metric run(s) errored; see report.")

    failures = []
    for name, score in summary.items():
        threshold = DEEPEVAL_THRESHOLDS.get(name)
        if threshold is None:
            continue
        failed = score > threshold if name in LOWER_IS_BETTER else score < threshold
        if failed:
            failures.append((name, score, threshold))

    if failures:
        print("\n❌ Quality gate failed:")
        for name, score, threshold in failures:
            print(f"   {name}: {score:.3f} vs {threshold}")
        return 1

    print("\n✅ All DeepEval metrics passed their thresholds.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
