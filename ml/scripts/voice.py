"""Voice matching (prd.md Member C deliverable 7): pick the creator's own writing closest to the brief.

Captions and transcripts are turned into hashed character n-gram vectors (no model download)
and ranked by cosine similarity to the topic plus the template's hook. A creator has at most a
few hundred samples, so exact search in memory is as good as pgvector and simpler. When nothing
is similar, the newest samples are used, so the script still sounds like the creator.
"""

from collections.abc import Sequence

import numpy
from sklearn.feature_extraction.text import HashingVectorizer

from ml.comments.normalise import normalise
from ml.scripts.schema import MAX_VOICE_SAMPLES

VECTOR_SIZE = 512

_hasher = HashingVectorizer(
    analyzer="char_wb", ngram_range=(2, 4), n_features=VECTOR_SIZE, alternate_sign=False, norm="l2"
)


def vectors(texts: Sequence[str]) -> numpy.ndarray:
    matrix: numpy.ndarray = _hasher.transform([normalise(text) for text in texts]).toarray()
    return matrix


def pick_samples(
    query: str, samples_newest_first: Sequence[str], limit: int = MAX_VOICE_SAMPLES
) -> list[str]:
    """The most similar samples first, ties broken by recency. Empty samples are skipped."""
    samples = [sample.strip() for sample in samples_newest_first if sample and sample.strip()]
    if not samples:
        return []
    similarity = vectors(samples) @ vectors([query])[0]
    if not similarity.any():
        return samples[:limit]
    order = sorted(range(len(samples)), key=lambda index: (-float(similarity[index]), index))
    return [samples[index] for index in order[:limit]]
