"""Comment classifiers that train on CPU in seconds (prd.md Member C deliverable 4).

- `CharNgramClassifier`: character n-grams of the normalised text. Robust to Roman Urdu's
  spelling variety and to Urdu script, so it is the main CPU model and the fallback when
  no XLM-R model is deployed.
- `EnglishOnlyBaseline`: word features learned from English comments only. It is the
  "English-only model" baseline: it shows how much a monolingual approach loses.

Both are scikit-learn pipelines saved with joblib, with a fixed seed (rules.md 3.10).
"""

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from ml.comments.dataset import LabelledComment
from ml.comments.labels import CommentLabel
from ml.comments.normalise import normalise

SEED = 13
MAX_ITERATIONS = 2000
ENGLISH = "english"


class CommentClassifier(Protocol):
    name: str

    def predict(self, texts: Sequence[str]) -> list[CommentLabel]: ...


class _SklearnClassifier:
    name = "base"

    def __init__(self, pipeline: Pipeline) -> None:
        self._pipeline = pipeline

    def fit(self, items: Sequence[LabelledComment]) -> "_SklearnClassifier":
        if len({item.label for item in items}) < 2:
            raise ValueError("Training needs at least two different labels")
        self._pipeline.fit([normalise(item.text) for item in items], [item.label.value for item in items])
        return self

    def predict(self, texts: Sequence[str]) -> list[CommentLabel]:
        if not texts:
            return []
        return [CommentLabel(label) for label in self._pipeline.predict([normalise(text) for text in texts])]

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"name": self.name, "pipeline": self._pipeline}, path)


def _logistic() -> LogisticRegression:
    # Balanced weights, because praise usually outnumbers objection and complaint many times over.
    return LogisticRegression(max_iter=MAX_ITERATIONS, class_weight="balanced", random_state=SEED)


class CharNgramClassifier(_SklearnClassifier):
    name = "char-ngram-logreg-v1"

    def __init__(self) -> None:
        super().__init__(
            Pipeline(
                [
                    (
                        "features",
                        TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=1, sublinear_tf=True),
                    ),
                    ("model", _logistic()),
                ]
            )
        )


class EnglishOnlyBaseline(_SklearnClassifier):
    name = "english-only-word-logreg-v1"

    def __init__(self) -> None:
        super().__init__(
            Pipeline(
                [
                    ("features", TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=1)),
                    ("model", _logistic()),
                ]
            )
        )

    def fit(self, items: Sequence[LabelledComment]) -> "_SklearnClassifier":
        return super().fit([item for item in items if item.language == ENGLISH])


def load_sklearn_classifier(path: Path) -> CommentClassifier:
    saved = joblib.load(path)
    classifier = _SklearnClassifier(saved["pipeline"])
    classifier.name = str(saved["name"])
    return classifier
