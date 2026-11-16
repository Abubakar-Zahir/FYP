import random

import pytest

from ml.bandit.simulator import all_candidates, compare, simulate
from ml.bandit.thompson import BanditState, Belief, best_known, choose, with_shared_prior

QUESTION = {"hook_style": "question", "opener": "face"}
STORY = {"hook_style": "story", "opener": "face"}


def test_updates_move_the_belief() -> None:
    state = BanditState()

    state.update(QUESTION, success=True)
    state.update(QUESTION, success=True)
    state.update(STORY, success=False)

    assert state.belief("hook_style", "question").mean == pytest.approx(0.75)
    assert state.belief("hook_style", "story").mean == pytest.approx(1 / 3)
    assert state.belief("opener", "face").observations == 3


def test_after_clear_evidence_it_mostly_picks_the_winner() -> None:
    state = BanditState()
    for _ in range(40):
        state.update(QUESTION, success=True)
        state.update(STORY, success=False)
    rng = random.Random(1)

    picks = [choose(state, [STORY, QUESTION], 1, rng)[0] for _ in range(200)]

    assert picks.count(1) > 190
    assert best_known(state, [STORY, QUESTION]) == 1


def test_with_no_evidence_it_explores_both() -> None:
    rng = random.Random(2)

    picks = [choose(BanditState(), [STORY, QUESTION], 1, rng)[0] for _ in range(200)]

    assert 60 < picks.count(1) < 140


def test_choose_needs_a_positive_count() -> None:
    with pytest.raises(ValueError):
        choose(BanditState(), [QUESTION], 0, random.Random(0))


def test_shared_prior_counts_as_a_few_observations_only() -> None:
    shared = BanditState({("hook_style", "question"): Belief(alpha=101, beta=1)})

    combined = with_shared_prior(BanditState(), shared, weight=4)

    belief = combined.belief("hook_style", "question")
    assert belief.observations == pytest.approx(4)
    assert belief.mean > 0.8


def test_own_results_soon_outweigh_the_shared_prior() -> None:
    shared = BanditState({("hook_style", "question"): Belief(alpha=101, beta=1)})
    own = BanditState({("hook_style", "question"): Belief(alpha=1, beta=21)})

    assert with_shared_prior(own, shared).belief("hook_style", "question").mean < 0.3


def test_candidates_cover_every_combination() -> None:
    assert len(all_candidates()) == 4 * 3 * 2


def test_simulation_is_reproducible_and_regret_grows() -> None:
    first = simulate("thompson_sampling", creators=5, rounds=8)

    assert first == simulate("thompson_sampling", creators=5, rounds=8)
    assert first.cumulative_regret == sorted(first.cumulative_regret)


def test_thompson_sampling_beats_random_choice() -> None:
    curves = {curve.policy: curve for curve in compare(creators=40, rounds=25)}

    assert curves["thompson_sampling"].final < curves["random"].final
