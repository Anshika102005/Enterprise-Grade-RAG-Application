"""
Quality gates for CI.

Every metric here is a *floor* (higher is better) EXCEPT the two marked
lower-is-better. Tune these once you have a stable baseline; set them slightly
below your current score so regressions fail the build without flapping.

Metric definitions (RAGAS):
  faithfulness       — answer claims grounded in retrieved context
  answer_relevancy   — answer actually addresses the question
  context_precision  — retrieved chunks that are relevant rank higher
  context_recall     — retrieved context covers the ground-truth answer
"""

RAGAS_THRESHOLDS = {
    "faithfulness": 0.80,
    "answer_relevancy": 0.80,
    "context_precision": 0.70,
    "context_recall": 0.75,
}

# DeepEval. `hallucination` is lower-is-better; everything else is a floor.
DEEPEVAL_THRESHOLDS = {
    "faithfulness": 0.80,       # floor
    "hallucination": 0.30,      # ceiling — must be <= this
    "answer_correctness": 0.75,  # floor
    "scope_adherence": 0.90,     # floor — stays on-topic / refuses off-topic
}

# Metrics where a lower score is better.
LOWER_IS_BETTER = {"hallucination"}
