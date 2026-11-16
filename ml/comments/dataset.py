"""Labelled comments from a Label Studio export, and the train/test split (rules.md 7.1).

The split is by reel, as the label guideline says, so near-identical comments under one reel
can't sit on both sides. It is deterministic: the same export always gives the same split.
"""

import hashlib
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from ml.comments.agreement import LABEL_FIELD
from ml.comments.labels import CommentLabel

TEXT_FIELD = "text"
GROUP_FIELDS = ("reel_id", "media_id")
LANGUAGE_FIELD = "language"
DEFAULT_TEST_FRACTION = 0.2
HASH_BUCKETS = 10_000


@dataclass(frozen=True)
class LabelledComment:
    id: str
    text: str
    label: CommentLabel
    language: str | None
    group: str  # the reel the comment came from


def _choice(annotation: dict[str, Any], field: str) -> str | None:
    for result in annotation.get("result", []):
        if result.get("from_name") == field:
            choices = result.get("value", {}).get("choices", [])
            if choices:
                return str(choices[0])
    return None


def from_label_studio(tasks: Iterable[dict[str, Any]]) -> list[LabelledComment]:
    """Takes the first finished annotation of each task. Skips tasks without a valid label."""
    items: list[LabelledComment] = []
    for task in tasks:
        data = task.get("data", {})
        annotations = [item for item in task.get("annotations", []) if not item.get("was_cancelled")]
        if not annotations or not data.get(TEXT_FIELD):
            continue
        label = _choice(annotations[0], LABEL_FIELD)
        if label not in {item.value for item in CommentLabel}:
            continue
        group = next((str(data[field]) for field in GROUP_FIELDS if data.get(field)), str(task.get("id")))
        items.append(
            LabelledComment(
                id=str(task.get("id")),
                text=str(data[TEXT_FIELD]),
                label=CommentLabel(label),
                language=_choice(annotations[0], LANGUAGE_FIELD),
                group=group,
            )
        )
    return items


def _bucket(group: str, seed: str) -> float:
    digest = hashlib.sha256(f"{seed}:{group}".encode()).hexdigest()
    return (int(digest, 16) % HASH_BUCKETS) / HASH_BUCKETS


def split_by_group(
    items: Sequence[LabelledComment], test_fraction: float = DEFAULT_TEST_FRACTION, seed: str = "v1"
) -> tuple[list[LabelledComment], list[LabelledComment]]:
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between 0 and 1")
    train = [item for item in items if _bucket(item.group, seed) >= test_fraction]
    test = [item for item in items if _bucket(item.group, seed) < test_fraction]
    return train, test
