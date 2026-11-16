"""The variant learner (prd.md Member B deliverable 6, roadmap Phase 3): Thompson sampling.

A variant is described by a few features (hook style, opener, caption length). Each value of
each feature has a Beta belief about how often it beats the creator's usual views. To choose
variants, one draw per belief is summed per candidate and the best candidates win. The draws
make it explore when unsure and exploit once it knows.

New creators start from a shared prior (what all creators taught it), shrunk so their own
results soon dominate. The reward is per account: did the variant beat this creator's median
views? So big and small accounts teach the same thing.
"""

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

PRIOR_ALPHA = 1.0
PRIOR_BETA = 1.0
# How many observations the shared prior counts as, at most, for a new creator.
SHARED_PRIOR_WEIGHT = 4.0

Features = Mapping[str, str]  # feature name -> value, for example {"hook_style": "question"}


@dataclass
class Belief:
    alpha: float = PRIOR_ALPHA
    beta: float = PRIOR_BETA

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    @property
    def observations(self) -> float:
        return self.alpha + self.beta - PRIOR_ALPHA - PRIOR_BETA


@dataclass
class BanditState:
    beliefs: dict[tuple[str, str], Belief] = field(default_factory=dict)

    def belief(self, feature: str, value: str) -> Belief:
        return self.beliefs.setdefault((feature, value), Belief())

    def update(self, features: Features, success: bool) -> None:
        for feature, value in features.items():
            belief = self.belief(feature, value)
            if success:
                belief.alpha += 1
            else:
                belief.beta += 1


def with_shared_prior(
    own: BanditState, shared: BanditState, weight: float = SHARED_PRIOR_WEIGHT
) -> BanditState:
    """The creator's beliefs plus the shared ones, scaled down to at most `weight` observations."""
    combined = BanditState()
    for key in set(own.beliefs) | set(shared.beliefs):
        mine = own.beliefs.get(key, Belief())
        theirs = shared.beliefs.get(key, Belief())
        scale = min(1.0, weight / theirs.observations) if theirs.observations > 0 else 0.0
        combined.beliefs[key] = Belief(
            alpha=mine.alpha + scale * (theirs.alpha - PRIOR_ALPHA),
            beta=mine.beta + scale * (theirs.beta - PRIOR_BETA),
        )
    return combined


def sample_score(state: BanditState, features: Features, rng: random.Random) -> float:
    return sum(rng.betavariate(*_params(state.belief(f, v))) for f, v in features.items())


def _params(belief: Belief) -> tuple[float, float]:
    return belief.alpha, belief.beta


def choose(state: BanditState, candidates: Sequence[Features], count: int, rng: random.Random) -> list[int]:
    """Indexes of the `count` candidates to publish, best draw first."""
    if count < 1:
        raise ValueError("Choose at least one candidate")
    scored = sorted(
        range(len(candidates)), key=lambda i: sample_score(state, candidates[i], rng), reverse=True
    )
    return scored[:count]


def best_known(state: BanditState, candidates: Sequence[Features]) -> int:
    """The candidate with the best expected score, with no exploring. For reports."""
    return max(
        range(len(candidates)), key=lambda i: sum(state.belief(f, v).mean for f, v in candidates[i].items())
    )
