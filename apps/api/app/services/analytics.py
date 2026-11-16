"""Account analytics for the dashboard (roadmap Phase 3, item 5).

Built from imported reels only. Missing metrics count as no data rather than zero in averages,
but as zero in totals, because a total of "unknown" would hide every other reel.
"""

from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from statistics import mean, median
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dna import DnaRecordRow
from app.models.reel import Reel, ReelSource
from ml.dna.schema import HookType

PERIOD_DAYS = 30
METRICS = ("views", "reach", "saves", "shares")


class Totals(BaseModel):
    views: float
    reach: float
    saves: float
    shares: float
    avg_watch_time_s: float


class TrendPoint(BaseModel):
    date: str
    views: int


class FormatPerformance(BaseModel):
    hook_type: HookType
    reels: int
    median_outlier: float


class AnalyticsOverview(BaseModel):
    """Field names match apps/web. `change` is the fraction up or down on the previous period."""

    period_days: int
    totals: Totals
    change: Totals
    trend: list[TrendPoint]
    best_formats: list[FormatPerformance]


def _totals(reels: list[Reel]) -> Totals:
    watch = [r.avg_watch_time_s for r in reels if r.avg_watch_time_s is not None]
    return Totals(
        **{metric: float(sum(getattr(r, metric) or 0 for r in reels)) for metric in METRICS},
        avg_watch_time_s=round(mean(watch), 2) if watch else 0.0,
    )


def _change(current: Totals, previous: Totals) -> Totals:
    def ratio(now: float, before: float) -> float:
        return round((now - before) / before, 4) if before else 0.0

    return Totals(
        **{field: ratio(getattr(current, field), getattr(previous, field)) for field in Totals.model_fields}
    )


def _trend(reels: list[Reel], start: date, days: int) -> list[TrendPoint]:
    by_day: dict[date, int] = defaultdict(int)
    for reel in reels:
        if reel.posted_at is not None:
            by_day[reel.posted_at.date()] += reel.views or 0
    return [
        TrendPoint(
            date=(start + timedelta(days=offset)).isoformat(), views=by_day[start + timedelta(days=offset)]
        )
        for offset in range(days)
    ]


async def _best_formats(session: AsyncSession, user_id: UUID) -> list[FormatPerformance]:
    rows = (
        await session.execute(
            select(DnaRecordRow.hook_type, Reel.outlier_score)
            .join(Reel, Reel.id == DnaRecordRow.reel_id)
            .where(Reel.user_id == user_id, Reel.source == ReelSource.OWN, Reel.outlier_score.is_not(None))
        )
    ).all()
    grouped: dict[str, list[float]] = defaultdict(list)
    for hook_type, score in rows:
        if score is not None:  # the query filters these out, this tells the type checker
            grouped[str(hook_type)].append(float(score))
    formats = [
        FormatPerformance(
            hook_type=HookType(kind), reels=len(scores), median_outlier=round(median(scores), 2)
        )
        for kind, scores in grouped.items()
    ]
    return sorted(formats, key=lambda item: item.median_outlier, reverse=True)


async def overview(session: AsyncSession, user_id: UUID, now: datetime | None = None) -> AnalyticsOverview:
    end = now or datetime.now(UTC)
    start = end - timedelta(days=PERIOD_DAYS)
    before = start - timedelta(days=PERIOD_DAYS)
    own = list(
        (
            await session.execute(
                select(Reel).where(
                    Reel.user_id == user_id, Reel.source == ReelSource.OWN, Reel.posted_at >= before
                )
            )
        ).scalars()
    )

    def in_range(reel: Reel, low: datetime, high: datetime) -> bool:
        posted = (
            reel.posted_at.replace(tzinfo=UTC)
            if reel.posted_at and reel.posted_at.tzinfo is None
            else reel.posted_at
        )
        return posted is not None and low <= posted < high

    current = [reel for reel in own if in_range(reel, start, end)]
    previous = [reel for reel in own if in_range(reel, before, start)]
    totals = _totals(current)
    return AnalyticsOverview(
        period_days=PERIOD_DAYS,
        totals=totals,
        change=_change(totals, _totals(previous)),
        trend=_trend(current, (start + timedelta(days=1)).date(), PERIOD_DAYS),
        best_formats=await _best_formats(session, user_id),
    )
