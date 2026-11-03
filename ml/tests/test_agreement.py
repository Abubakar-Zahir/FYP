from typing import Any

import pytest

from ml.comments.agreement import cohen_kappa, paired_labels
from ml.comments.labels import CommentLabel


def annotation(labeller: int, label: str, cancelled: bool = False) -> dict[str, Any]:
    return {
        "completed_by": labeller,
        "was_cancelled": cancelled,
        "result": [
            {"from_name": "language", "value": {"choices": ["mixed"]}},
            {"from_name": "label", "value": {"choices": [label]}},
        ],
    }


def test_perfect_agreement_is_one() -> None:
    assert cohen_kappa(["a", "b", "a"], ["a", "b", "a"]) == pytest.approx(1.0)


def test_chance_level_agreement_is_zero() -> None:
    assert cohen_kappa(["a", "a", "b", "b"], ["a", "b", "a", "b"]) == pytest.approx(0.0)


def test_known_value() -> None:
    # Observed 0.7, expected 0.5 * 0.6 + 0.5 * 0.4 = 0.5, so kappa = 0.2 / 0.5.
    first = ["a"] * 5 + ["b"] * 5
    second = ["a"] * 4 + ["b"] + ["a"] * 2 + ["b"] * 3

    assert cohen_kappa(first, second) == pytest.approx(0.4)


def test_mismatched_lengths_are_rejected() -> None:
    with pytest.raises(ValueError, match="same items"):
        cohen_kappa(["a"], ["a", "b"])


def test_single_shared_label_is_undefined() -> None:
    with pytest.raises(ValueError, match="undefined"):
        cohen_kappa(["a", "a"], ["a", "a"])


def test_paired_labels_keeps_only_shared_tasks() -> None:
    tasks = [
        {"annotations": [annotation(1, "praise"), annotation(2, "spam")]},
        {"annotations": [annotation(1, "praise")]},
        {"annotations": [annotation(1, "praise"), annotation(2, "spam", cancelled=True)]},
    ]

    assert paired_labels(tasks, 1, 2) == (["praise"], ["spam"])


def test_six_classes_match_the_srs() -> None:
    assert {label.value for label in CommentLabel} == {
        "question",
        "request",
        "praise",
        "objection",
        "complaint",
        "spam",
    }
