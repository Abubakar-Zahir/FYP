"""Outlier score: how a reel did compared with the same account's usual reel (SRS FR-2.4).

Views are compared within one account, never across accounts, because a 2,000-follower
creator and a 200,000-follower creator have different normal ranges.
"""

from collections.abc import Sequence
from statistics import median

# Fewer reels than this make the median too noisy to call anything an outlier.
MIN_REELS_FOR_BASELINE = 5


def outlier_score(views: int, account_views: Sequence[int]) -> float | None:
    """Views divided by the account's median views. 2.0 means twice the usual reach.

    None when the account has too few reels with views, or a median of zero, so the
    frontend shows "not enough data" instead of a made-up number.
    """
    if views < 0:
        raise ValueError("views can't be negative")
    if len(account_views) < MIN_REELS_FOR_BASELINE:
        return None
    baseline = median(account_views)
    if baseline <= 0:
        return None
    return round(views / baseline, 2)
