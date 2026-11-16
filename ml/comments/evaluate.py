"""Scores a comment classifier on the held-out set (prd.md Member C acceptance 1).

Macro F1 weighs every class equally, so a model can't look good by only getting praise right.
The 95% interval comes from resampling the test set, because the test set is small.
"""

import random
from collections.abc import Sequence

from pydantic import BaseModel
from sklearn.metrics import confusion_matrix, f1_score

from ml.comments.labels import CommentLabel

BOOTSTRAP_ROUNDS = 1000
CONFIDENCE = 0.95
SEED = 13
LABELS = [item.value for item in CommentLabel]


class EvaluationReport(BaseModel):
    model: str
    test_size: int
    macro_f1: float
    macro_f1_low: float
    macro_f1_high: float
    f1_by_label: dict[str, float]
    # Rows are the true label, columns the predicted one, both in LABELS order.
    confusion: list[list[int]]
    labels: list[str]


def _macro_f1(truth: Sequence[str], predicted: Sequence[str]) -> float:
    return float(f1_score(truth, predicted, labels=LABELS, average="macro", zero_division=0))


def bootstrap_interval(
    truth: Sequence[str], predicted: Sequence[str], rounds: int = BOOTSTRAP_ROUNDS, seed: int = SEED
) -> tuple[float, float]:
    generator = random.Random(seed)  # noqa: S311 (statistics, not security)
    size = len(truth)
    scores = sorted(
        _macro_f1([truth[i] for i in sample], [predicted[i] for i in sample])
        for sample in ([generator.randrange(size) for _ in range(size)] for _ in range(rounds))
    )
    tail = (1 - CONFIDENCE) / 2
    return scores[int(tail * rounds)], scores[min(rounds - 1, int((1 - tail) * rounds))]


def evaluate(model: str, truth: Sequence[str], predicted: Sequence[str]) -> EvaluationReport:
    if len(truth) != len(predicted) or not truth:
        raise ValueError("Need one prediction per test comment, and at least one comment")
    low, high = bootstrap_interval(truth, predicted)
    per_label = f1_score(truth, predicted, labels=LABELS, average=None, zero_division=0)
    return EvaluationReport(
        model=model,
        test_size=len(truth),
        macro_f1=round(_macro_f1(truth, predicted), 4),
        macro_f1_low=round(low, 4),
        macro_f1_high=round(high, 4),
        f1_by_label={label: round(float(score), 4) for label, score in zip(LABELS, per_label, strict=True)},
        confusion=confusion_matrix(truth, predicted, labels=LABELS).tolist(),
        labels=LABELS,
    )
