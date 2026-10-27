"""Golden dataset loading for the eval harness."""
import json
from dataclasses import dataclass, field
from pathlib import Path

DATASET_PATH = Path(__file__).parent / "golden_dataset.jsonl"


@dataclass
class EvalItem:
    question: str
    ground_truth: str
    ground_truth_contexts: list = field(default_factory=list)


def load_dataset(path: Path | str = DATASET_PATH) -> list[EvalItem]:
    """Load a JSONL dataset. Blank lines and '#' comments are ignored."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Golden dataset not found: {path}")

    items: list[EvalItem] = []
    with path.open(encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {lineno} of {path}: {e}") from e
            items.append(
                EvalItem(
                    question=obj["question"],
                    ground_truth=obj.get("ground_truth", ""),
                    ground_truth_contexts=obj.get("ground_truth_contexts", []),
                )
            )
    if not items:
        raise ValueError(f"Golden dataset {path} contained no items.")
    return items
