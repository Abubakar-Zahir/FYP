"""Offline simulator for the variant learner (prd.md Member B acceptance 4: regret curve).

Each simulated creator has hidden true effects per feature value. Every round, a policy picks
which variants to publish from the full set of candidates, each published variant "beats the
median" with its true probability, and the policy learns from the outcomes. Regret is how much
worse the picks were than always picking the truly best variants. Lower is better.

Thompson sampling is compared with random choice and epsilon-greedy, on the same creators and
the same random draws, so the curves are directly comparable.
"""

import itertools
import math
import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from pydantic import BaseModel

from ml.bandit.thompson import BanditState, Features, choose

FEATURES: dict[str, list[str]] = {
    "hook_style": ["question", "bold_claim", "story", "list"],
    "opener": ["face", "product", "text"],
    "caption_length": ["short", "long"],
}
EPSILON = 0.1
BASE_LOGIT = -0.4
EFFECT_SPREAD = 0.8

Policy = Callable[[BanditState, Sequence[Features], int, random.Random], list[int]]


def all_candidates() -> list[Features]:
    names = list(FEATURES)
    return [dict(zip(names, values, strict=True)) for values in itertools.product(*FEATURES.values())]


@dataclass(frozen=True)
class Creator:
    effects: dict[tuple[str, str], float]

    def win_probability(self, features: Features) -> float:
        logit = BASE_LOGIT + sum(self.effects[(name, value)] for name, value in features.items())
        return 1 / (1 + math.exp(-logit))


def random_creator(rng: random.Random) -> Creator:
    return Creator({(f, v): rng.gauss(0, EFFECT_SPREAD) for f, values in FEATURES.items() for v in values})


def random_policy(
    state: BanditState, candidates: Sequence[Features], count: int, rng: random.Random
) -> list[int]:
    return rng.sample(range(len(candidates)), count)


def epsilon_greedy(
    state: BanditState, candidates: Sequence[Features], count: int, rng: random.Random
) -> list[int]:
    def expected(index: int) -> float:
        return sum(state.belief(f, v).mean for f, v in candidates[index].items())

    ranked = sorted(range(len(candidates)), key=expected, reverse=True)
    picks: list[int] = []
    for best in ranked:
        if len(picks) == count:
            break
        if rng.random() < EPSILON:
            options = [i for i in range(len(candidates)) if i not in picks]
            picks.append(rng.choice(options))
        elif best not in picks:
            picks.append(best)
    return picks[:count]


POLICIES: dict[str, Policy] = {
    "thompson_sampling": choose,
    "epsilon_greedy": epsilon_greedy,
    "random": random_policy,
}


class RegretCurve(BaseModel):
    policy: str
    creators: int
    rounds: int
    variants_per_round: int
    # Mean cumulative regret after each round, averaged over creators.
    cumulative_regret: list[float]

    @property
    def final(self) -> float:
        return self.cumulative_regret[-1]


def simulate(
    policy_name: str, creators: int = 50, rounds: int = 20, per_round: int = 3, seed: int = 13
) -> RegretCurve:
    candidates = all_candidates()
    totals = [0.0] * rounds
    for creator_index in range(creators):
        world = random.Random(seed * 1000 + creator_index)  # noqa: S311 (simulation). Same creator for every policy
        creator = random_creator(world)
        probabilities = [creator.win_probability(features) for features in candidates]
        best = sum(sorted(probabilities, reverse=True)[:per_round])
        choices = random.Random(seed * 7919 + creator_index)  # noqa: S311
        outcomes = random.Random(seed * 104729 + creator_index)  # noqa: S311
        state = BanditState()
        regret = 0.0
        for round_index in range(rounds):
            picks = POLICIES[policy_name](state, candidates, per_round, choices)
            regret += best - sum(probabilities[i] for i in picks)
            for index in picks:
                state.update(candidates[index], outcomes.random() < probabilities[index])
            totals[round_index] += regret
    return RegretCurve(
        policy=policy_name,
        creators=creators,
        rounds=rounds,
        variants_per_round=per_round,
        cumulative_regret=[round(total / creators, 4) for total in totals],
    )


def compare(creators: int = 50, rounds: int = 20, per_round: int = 3) -> list[RegretCurve]:
    return [simulate(name, creators, rounds, per_round) for name in POLICIES]
