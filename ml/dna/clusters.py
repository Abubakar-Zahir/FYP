"""Groups DNA records into formats for the niche view (roadmap Phase 2, item 5).

Each record becomes a small vector: hook type, pacing, length, number of beats and whether it
has a call to action. K-means with a fixed seed groups them. Each cluster is described in
plain terms (most common hook type, median pacing and length, median outlier score), so the
creator sees which formats work, not just which reels are alike.
"""

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from statistics import median

import numpy
from sklearn.cluster import KMeans

from ml.dna.schema import DnaRecord, HookType

SEED = 13
MIN_RECORDS = 6
RECORDS_PER_CLUSTER = 3
MAX_CLUSTERS = 5
# Scales that bring each number to roughly 0 to 1, so no single one dominates the distance.
PACING_SCALE = 5.0
LENGTH_SCALE = 90.0
BEATS_SCALE = 8.0


@dataclass(frozen=True)
class FormatCluster:
    members: list[int]  # indexes into the input
    hook_type: HookType
    median_pacing: float
    median_length_s: float
    median_outlier: float | None

    @property
    def label(self) -> str:
        speed = "fast" if self.median_pacing >= 2 else "steady" if self.median_pacing >= 1 else "slow"
        hook = self.hook_type.value.replace("_", " ").capitalize()
        return f"{hook} hook, {speed} cuts, ~{self.median_length_s:.0f} s"


def _vector(record: DnaRecord) -> list[float]:
    hook = [float(record.hook_type == item) for item in HookType]
    return hook + [
        min(record.signals.pacing_cuts_per_10s / PACING_SCALE, 1.0),
        min(record.signals.length_s / LENGTH_SCALE, 1.0),
        min(len(record.beats) / BEATS_SCALE, 1.0),
        float(bool(record.cta.strip())),
    ]


def cluster_formats(records: Sequence[DnaRecord], outliers: Sequence[float | None]) -> list[FormatCluster]:
    """Largest cluster first. Empty below MIN_RECORDS, where clusters would mean nothing."""
    if len(records) != len(outliers):
        raise ValueError("Need one outlier score (or None) per record")
    if len(records) < MIN_RECORDS:
        return []
    count = min(MAX_CLUSTERS, len(records) // RECORDS_PER_CLUSTER)
    labels = KMeans(n_clusters=count, random_state=SEED, n_init=10).fit_predict(
        numpy.array([_vector(record) for record in records])
    )
    clusters = []
    for cluster in range(count):
        members = [index for index, label in enumerate(labels) if label == cluster]
        if not members:
            continue
        scores = [score for index in members if (score := outliers[index]) is not None]
        clusters.append(
            FormatCluster(
                members=members,
                hook_type=Counter(records[index].hook_type for index in members).most_common(1)[0][0],
                median_pacing=round(median(records[i].signals.pacing_cuts_per_10s for i in members), 2),
                median_length_s=round(median(records[i].signals.length_s for i in members), 1),
                median_outlier=round(median(scores), 2) if scores else None,
            )
        )
    return sorted(clusters, key=lambda item: len(item.members), reverse=True)
