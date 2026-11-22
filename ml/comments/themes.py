"""Groups comments into themes and ranks them by size (SRS FR-7.4).

The plan named BERTopic, which needs torch. This CPU version uses NMF topics over TF-IDF of
the normalised text: fast, deterministic with a seed, and good enough to rank what comments
keep asking for. Spam is left out before grouping.
"""

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

import numpy
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer

from ml.comments.labels import CommentLabel
from ml.comments.normalise import normalise

SEED = 13
MIN_COMMENTS = 30
COMMENTS_PER_THEME = 15
MAX_THEMES = 8
TOP_TERMS = 5
EXAMPLES_PER_THEME = 3


@dataclass(frozen=True)
class Theme:
    terms: list[str]
    members: list[int]  # indexes into the input lists
    examples: list[int]  # the most typical members, best first
    dominant_label: CommentLabel

    @property
    def size(self) -> int:
        return len(self.members)


def find_themes(
    texts: Sequence[str], labels: Sequence[CommentLabel], max_themes: int = MAX_THEMES
) -> list[Theme]:
    """Largest theme first. Empty when there are too few comments to group honestly."""
    if len(texts) != len(labels):
        raise ValueError("Need one label per comment")
    kept = [index for index, label in enumerate(labels) if label != CommentLabel.SPAM]
    if len(kept) < MIN_COMMENTS:
        return []
    vectoriser = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=2, max_df=0.9, sublinear_tf=True)
    try:
        matrix = vectoriser.fit_transform([normalise(texts[index]) for index in kept])
    except ValueError:
        return []  # nothing repeats across comments, so there is nothing to group
    count = max(1, min(max_themes, len(kept) // COMMENTS_PER_THEME, matrix.shape[1]))
    model = NMF(n_components=count, init="nndsvda", random_state=SEED, max_iter=500)
    weights = model.fit_transform(matrix)
    vocabulary = vectoriser.get_feature_names_out()
    themes = [
        _theme(topic, weights, model.components_[topic], vocabulary, kept, labels) for topic in range(count)
    ]
    return sorted((theme for theme in themes if theme.members), key=lambda theme: theme.size, reverse=True)


def _theme(
    topic: int,
    weights: numpy.ndarray,
    component: numpy.ndarray,
    vocabulary: numpy.ndarray,
    kept: list[int],
    labels: Sequence[CommentLabel],
) -> Theme:
    rows = [
        row for row in range(weights.shape[0]) if weights[row].max() > 0 and weights[row].argmax() == topic
    ]
    best_first = sorted(rows, key=lambda row: weights[row, topic], reverse=True)
    members = [kept[row] for row in best_first]
    dominant = Counter(labels[index] for index in members).most_common(1)
    return Theme(
        terms=[str(vocabulary[index]) for index in component.argsort()[::-1][:TOP_TERMS]],
        members=members,
        examples=members[:EXAMPLES_PER_THEME],
        dominant_label=dominant[0][0] if dominant else CommentLabel.PRAISE,
    )
