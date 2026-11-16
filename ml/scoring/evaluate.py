"""Evaluates the hook scorer the way prd.md asks: Spearman on held-out creators, with baselines.

Folds are split by creator (rules.md 7.2), so the model is never scored on an account it saw.
Out-of-fold predictions from every fold are pooled, then Spearman's rho gets a bootstrap 95%
interval. Small data gives wide intervals, and the report shows them as they are (SRS risks).
"""

import random
from collections.abc import Callable, Sequence

import numpy
from pydantic import BaseModel
from scipy.stats import spearmanr
from sklearn.model_selection import GroupKFold

from ml.scoring.model import HookExample, HookScorer, target

BOOTSTRAP_ROUNDS = 1000
SEED = 13
MAX_FOLDS = 5
MIN_CREATORS = 2


class CorrelationReport(BaseModel):
    model: str
    hooks: int
    creators: int
    folds: int
    spearman: float
    spearman_low: float
    spearman_high: float


Predict = Callable[[Sequence[HookExample], Sequence[HookExample]], list[float]]


def _spearman(truth: Sequence[float], predicted: Sequence[float]) -> float:
    if len(set(predicted)) < 2 or len(set(truth)) < 2:
        return 0.0  # a constant prediction has no rank order to correlate
    return float(spearmanr(truth, predicted).statistic)


def _interval(truth: list[float], predicted: list[float]) -> tuple[float, float]:
    generator = random.Random(SEED)  # noqa: S311 (statistics, not security)
    size = len(truth)
    scores = []
    for _ in range(BOOTSTRAP_ROUNDS):
        sample = [generator.randrange(size) for _ in range(size)]
        scores.append(_spearman([truth[i] for i in sample], [predicted[i] for i in sample]))
    scores.sort()
    return scores[int(0.025 * BOOTSTRAP_ROUNDS)], scores[int(0.975 * BOOTSTRAP_ROUNDS) - 1]


def cross_validate(name: str, examples: Sequence[HookExample], predict: Predict) -> CorrelationReport:
    creators = sorted({example.creator for example in examples})
    if len(creators) < MIN_CREATORS:
        raise ValueError("Need hooks from at least two creators to hold one out")
    folds = min(MAX_FOLDS, len(creators))
    groups = [creators.index(example.creator) for example in examples]
    truth: list[float] = []
    predicted: list[float] = []
    for train_index, test_index in GroupKFold(n_splits=folds).split(
        numpy.zeros(len(examples)), groups=groups
    ):
        train = [examples[i] for i in train_index]
        test = [examples[i] for i in test_index]
        truth += [target(example.outlier_score) for example in test]
        predicted += predict(train, test)
    low, high = _interval(truth, predicted)
    return CorrelationReport(
        model=name,
        hooks=len(examples),
        creators=len(creators),
        folds=folds,
        spearman=round(_spearman(truth, predicted), 4),
        spearman_low=round(low, 4),
        spearman_high=round(high, 4),
    )


def length_baseline(train: Sequence[HookExample], test: Sequence[HookExample]) -> list[float]:
    """Shorter hooks do better: the simplest rule a creator might already follow."""
    return [-float(len(example.text.split())) for example in test]


def hook_type_baseline(train: Sequence[HookExample], test: Sequence[HookExample]) -> list[float]:
    """The average outcome of each hook type in the training creators."""
    sums: dict[object, list[float]] = {}
    for example in train:
        sums.setdefault(example.hook_type, []).append(target(example.outlier_score))
    overall = float(numpy.mean([target(example.outlier_score) for example in train]))
    return [float(numpy.mean(sums[e.hook_type])) if e.hook_type in sums else overall for e in test]


def scorer_predict(with_wording: bool) -> Predict:
    def predict(train: Sequence[HookExample], test: Sequence[HookExample]) -> list[float]:
        model = HookScorer.train(train, with_wording=with_wording)
        return model.predict_log_outlier([e.text for e in test], [e.hook_type for e in test])

    return predict


def full_report(examples: Sequence[HookExample]) -> list[CorrelationReport]:
    """Both baselines and both ablations (readable features only, plus wording)."""
    return [
        cross_validate("baseline: shorter is better", examples, length_baseline),
        cross_validate("baseline: hook type average", examples, hook_type_baseline),
        cross_validate("lgbm: readable features", examples, scorer_predict(with_wording=False)),
        cross_validate("lgbm: readable + wording", examples, scorer_predict(with_wording=True)),
    ]
