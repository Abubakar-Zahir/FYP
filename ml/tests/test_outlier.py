import pytest

from ml.dna.outlier import outlier_score

ACCOUNT = [1000, 1200, 800, 1000, 3000]


def test_score_is_views_over_the_account_median() -> None:
    assert outlier_score(2000, ACCOUNT) == 2.0


def test_a_typical_reel_scores_about_one() -> None:
    assert outlier_score(1000, ACCOUNT) == 1.0


def test_too_few_reels_gives_no_score() -> None:
    assert outlier_score(5000, ACCOUNT[:4]) is None


def test_a_zero_median_gives_no_score() -> None:
    assert outlier_score(10, [0, 0, 0, 5, 10]) is None


def test_negative_views_are_rejected() -> None:
    with pytest.raises(ValueError, match="negative"):
        outlier_score(-1, ACCOUNT)
