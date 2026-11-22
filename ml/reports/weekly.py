"""The weekly report (roadmap Phase 3, item 5): wins, losses, what comments asked, what to make next.

Built from the creator's own numbers with plain rules, no LLM, so it costs nothing and says
nothing the data doesn't support. A win beats the creator's usual views, a loss falls short.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from pydantic import BaseModel

TOP = 2
MAX_IDEAS = 5
MAX_THEMES = 5


@dataclass(frozen=True)
class ReelResult:
    title: str
    hook_type: str | None
    views: int | None
    outlier_score: float | None


@dataclass(frozen=True)
class ThemeSummary:
    name: str
    idea: str
    size: int


@dataclass(frozen=True)
class LearnerHint:
    feature: str  # "hook_style", "opener" or "caption_length"
    value: str
    win_rate: float
    observations: float


class Item(BaseModel):
    title: str
    detail: str


class Idea(BaseModel):
    title: str
    why: str


class WeeklyReportContent(BaseModel):
    """Field names match apps/web."""

    week_start: str
    headline: str
    wins: list[Item]
    losses: list[Item]
    themes: list[str]
    ideas: list[Idea]


FEATURE_WORDS = {"hook_style": "hook", "opener": "opening frame", "caption_length": "caption"}


def _times(score: float) -> str:
    return f"{score:.1f}x your usual views"


def build_report(
    week_start: str,
    reels: Sequence[ReelResult],
    themes: Sequence[ThemeSummary],
    hints: Sequence[LearnerHint],
) -> WeeklyReportContent:
    scored = sorted((r for r in reels if r.outlier_score is not None), key=lambda r: r.outlier_score or 0)
    wins = [r for r in reversed(scored) if (r.outlier_score or 0) >= 1][:TOP]
    losses = [r for r in scored if (r.outlier_score or 0) < 1][:TOP]
    if not reels:
        headline = "No new reels this week. Post one, and next week's report will compare it."
    elif wins:
        headline = f"{len(reels)} reels this week. The best did {_times(wins[0].outlier_score or 0)}."
    else:
        headline = f"{len(reels)} reels this week. None beat your usual views yet."
    ideas = [Idea(title=theme.idea, why=f"{theme.size} comments are about {theme.name}") for theme in themes]
    for hint in sorted(hints, key=lambda item: item.win_rate, reverse=True):
        if hint.win_rate > 0.5:
            word = FEATURE_WORDS.get(hint.feature, hint.feature)
            ideas.append(
                Idea(
                    title=f"Keep testing a {hint.value.replace('_', ' ')} {word}",
                    why=f"It beat your usual views in {hint.win_rate:.0%} of {hint.observations:.0f} tests",
                )
            )
    return WeeklyReportContent(
        week_start=week_start,
        headline=headline,
        wins=[
            Item(title=r.title, detail=f"{_times(r.outlier_score or 0)}, {r.hook_type or 'unanalysed'} hook")
            for r in wins
        ],
        losses=[
            Item(title=r.title, detail=f"{_times(r.outlier_score or 0)}, {r.hook_type or 'unanalysed'} hook")
            for r in losses
        ],
        themes=[theme.name for theme in themes[:MAX_THEMES]],
        ideas=ideas[:MAX_IDEAS],
    )
