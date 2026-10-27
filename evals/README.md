# Evaluation Harness

Two independent judges over the same pipeline so metrics are not a single
vendor's opinion:

| Suite | Metrics | Role |
|-------|---------|------|
| **RAGAS** | faithfulness, answer_relevancy, context_precision, context_recall | retrieval + grounding quality |
| **DeepEval** | faithfulness, hallucination, answer_correctness, scope_adherence | grounding + correctness + guardrail scope |

The judge LLM uses a dedicated **`JUDGE_GROQ`** key (falls back to
`GROQ_API_KEY`) so evaluation spend never eats production quota. Embeddings use
the same local sentence-transformer as the pipeline.

## Metric meanings

- **faithfulness** — share of answer claims supported by retrieved context.
- **answer_relevancy** — does the answer actually address the question?
- **context_precision** — are the *relevant* retrieved chunks ranked first?
- **context_recall** — does retrieved context cover the ground-truth answer?
- **hallucination** — unsupported claims (lower is better).
- **answer_correctness** — agreement with the ground-truth answer.
- **scope_adherence** — stays within Kubernetes / Intel / networking scope.

## Golden dataset

`golden_dataset.jsonl` — one JSON object per line:

```json
{"question": "...", "ground_truth": "..."}
```

Replace the seed questions with ones grounded in **your own** ingested corpus;
metrics are only meaningful when the corpus can actually answer the questions.

## Running

Start the backend first (`uvicorn app.main:app`), then:

```bash
# Call the backend, record the raw outputs, and score with RAGAS
python -m evals.run_ragas --record evals/fixtures/samples.json

# Same, with DeepEval
python -m evals.run_deepeval --record evals/fixtures/samples.json

# Re-score previously recorded outputs (no backend / Qdrant required)
python -m evals.run_ragas --samples evals/fixtures/samples.json
python -m evals.run_deepeval --samples evals/fixtures/samples.json
```

Both runners write a timestamped JSON report to `evals/results/` and **exit
non-zero** when a metric breaches its gate in `thresholds.py`, so they work
directly as CI gates.

## Tuning thresholds

Thresholds live in `thresholds.py`. Start by running both suites once, then set
each threshold slightly *below* your observed baseline. That turns the eval into
a regression detector — a PR that degrades retrieval or grounding fails the build.
