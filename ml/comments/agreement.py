from collections import Counter
from collections.abc import Sequence
from typing import Any

LABEL_FIELD = "label"


def cohen_kappa(first: Sequence[str], second: Sequence[str]) -> float:
    """Agreement between two labellers, corrected for the agreement chance alone would give."""
    if len(first) != len(second):
        raise ValueError("Both labellers must label the same items")
    if not first:
        raise ValueError("No items to compare")
    total = len(first)
    observed = sum(a == b for a, b in zip(first, second, strict=True)) / total
    first_counts = Counter(first)
    second_counts = Counter(second)
    expected = sum(first_counts[label] * second_counts[label] for label in first_counts) / total**2
    if expected == 1:
        raise ValueError("Kappa is undefined when both labellers use one single label")
    return (observed - expected) / (1 - expected)


def _chosen_label(annotation: dict[str, Any]) -> str | None:
    for result in annotation.get("result", []):
        if result.get("from_name") == LABEL_FIELD:
            choices = result.get("value", {}).get("choices", [])
            if choices:
                return str(choices[0])
    return None


def paired_labels(
    tasks: Sequence[dict[str, Any]], first_id: int, second_id: int
) -> tuple[list[str], list[str]]:
    """Reads a Label Studio JSON export and keeps tasks both labellers answered."""
    first: list[str] = []
    second: list[str] = []
    for task in tasks:
        by_labeller = {
            annotation.get("completed_by"): _chosen_label(annotation)
            for annotation in task.get("annotations", [])
            if not annotation.get("was_cancelled")
        }
        first_label = by_labeller.get(first_id)
        second_label = by_labeller.get(second_id)
        if first_label is not None and second_label is not None:
            first.append(first_label)
            second.append(second_label)
    return first, second
