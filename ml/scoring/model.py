"""The hook scorer (SRS FR-4.1 and FR-4.3): LightGBM on the per-account outlier score.

The target is log(outlier score), so "twice the creator's usual views" means the same for a
small and a large account. A score of 0 to 100 is the prediction's percentile among the
training hooks. The top 3 factors come from LightGBM's own SHAP values (`pred_contrib`), with
the wording parts added up into one factor.
"""

import json
import math
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import lightgbm
import numpy

from ml.dna.schema import HookType
from ml.scoring.features import feature_matrix, feature_names, label_for

SEED = 13
TOP_FACTORS = 3
MODEL_FILE = "model.txt"
META_FILE = "meta.json"
PARAMS: dict[str, object] = {
    "objective": "regression",
    "learning_rate": 0.05,
    "num_leaves": 15,
    "min_data_in_leaf": 5,
    "feature_fraction": 0.9,
    "lambda_l2": 1.0,
    "seed": SEED,
    "deterministic": True,
    "num_threads": 1,
    "verbose": -1,
}
ROUNDS = 200


@dataclass(frozen=True)
class HookExample:
    text: str
    hook_type: HookType | None
    creator: str  # used only to split by creator (rules.md 7.2)
    outlier_score: float


@dataclass(frozen=True)
class Factor:
    label: str
    impact: float


@dataclass(frozen=True)
class HookScore:
    score: int  # 0 to 100
    top_factors: list[Factor]


def target(outlier_score: float) -> float:
    if outlier_score <= 0:
        raise ValueError("Outlier scores must be positive")
    return math.log(outlier_score)


class HookScorer:
    def __init__(
        self, booster: lightgbm.Booster, with_wording: bool, reference: list[float], version: str
    ) -> None:
        self._booster = booster
        self.with_wording = with_wording
        self._reference = sorted(reference)  # training predictions, for the percentile
        self.version = version

    @classmethod
    def train(
        cls, examples: Sequence[HookExample], with_wording: bool = True, version: str = "v1"
    ) -> "HookScorer":
        if len(examples) < 2:
            raise ValueError("Training needs at least two hooks")
        matrix = feature_matrix([e.text for e in examples], [e.hook_type for e in examples], with_wording)
        data = lightgbm.Dataset(
            matrix,
            label=[target(e.outlier_score) for e in examples],
            feature_name=feature_names(with_wording),
        )
        booster = lightgbm.train(PARAMS, data, num_boost_round=ROUNDS)
        reference = [float(value) for value in booster.predict(matrix)]
        name = f"lgbm-{'wording' if with_wording else 'readable'}-{version}"
        return cls(booster, with_wording, reference, name)

    def predict_log_outlier(self, texts: Sequence[str], hook_types: Sequence[HookType | None]) -> list[float]:
        matrix = feature_matrix(texts, hook_types, self.with_wording)
        return [float(value) for value in self._booster.predict(matrix)]

    def _percentile(self, prediction: float) -> int:
        below = int(numpy.searchsorted(self._reference, prediction, side="right"))
        return round(100 * below / len(self._reference))

    def score(self, texts: Sequence[str], hook_types: Sequence[HookType | None]) -> list[HookScore]:
        if not texts:
            return []
        matrix = feature_matrix(texts, hook_types, self.with_wording)
        predictions = self._booster.predict(matrix)
        contributions = self._booster.predict(matrix, pred_contrib=True)  # last column is the bias
        names = feature_names(self.with_wording)
        return [
            HookScore(score=self._percentile(float(prediction)), top_factors=_top_factors(row[:-1], names))
            for prediction, row in zip(predictions, contributions, strict=True)
        ]

    def save(self, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        self._booster.save_model(str(folder / MODEL_FILE))
        meta = {"with_wording": self.with_wording, "reference": self._reference, "version": self.version}
        (folder / META_FILE).write_text(json.dumps(meta), encoding="utf-8")

    @classmethod
    def load(cls, folder: Path) -> "HookScorer":
        meta = json.loads((folder / META_FILE).read_text(encoding="utf-8"))
        booster = lightgbm.Booster(model_file=str(folder / MODEL_FILE))
        return cls(
            booster, bool(meta["with_wording"]), [float(v) for v in meta["reference"]], str(meta["version"])
        )


def _top_factors(contributions: numpy.ndarray, names: list[str]) -> list[Factor]:
    by_label: dict[str, float] = defaultdict(float)
    for name, value in zip(names, contributions, strict=True):
        by_label[label_for(name)] += float(value)
    ranked = sorted(by_label.items(), key=lambda item: abs(item[1]), reverse=True)
    return [
        Factor(label=label, impact=round(value, 4)) for label, value in ranked[:TOP_FACTORS] if value != 0
    ]
