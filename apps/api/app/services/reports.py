"""Builds and stores weekly reports (ml/reports/weekly.py). Weeks start on Monday, in UTC."""

from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.models.dna import DnaRecordRow
from app.models.experiment import BanditBelief
from app.models.reel import CommentTheme, Reel, ReelSource
from app.models.report import WeeklyReport
from app.models.user import User
from ml.bandit.thompson import PRIOR_ALPHA, PRIOR_BETA
from ml.reports.weekly import LearnerHint, ReelResult, ThemeSummary, WeeklyReportContent, build_report

MIN_TESTS_FOR_HINT = 3


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


async def build_for_user(session: AsyncSession, user_id: UUID, now: datetime | None = None) -> WeeklyReport:
    when = now or datetime.now(UTC)
    monday = week_start(when.date())
    since = datetime(monday.year, monday.month, monday.day, tzinfo=UTC) - timedelta(days=7)
    reels = (
        await session.execute(
            select(Reel, DnaRecordRow.hook_type)
            .outerjoin(DnaRecordRow, DnaRecordRow.reel_id == Reel.id)
            .where(Reel.user_id == user_id, Reel.source == ReelSource.OWN, Reel.posted_at >= since)
        )
    ).all()
    themes = (
        await session.execute(
            select(CommentTheme).where(CommentTheme.user_id == user_id).order_by(CommentTheme.size.desc())
        )
    ).scalars()
    beliefs = (await session.execute(select(BanditBelief).where(BanditBelief.user_id == user_id))).scalars()
    hints = [
        LearnerHint(
            feature=b.feature,
            value=b.value,
            win_rate=(b.alpha - PRIOR_ALPHA) / tests,
            observations=tests,
        )
        for b in beliefs
        if (tests := b.alpha + b.beta - PRIOR_ALPHA - PRIOR_BETA) >= MIN_TESTS_FOR_HINT
    ]
    content: WeeklyReportContent = build_report(
        week_start=(monday - timedelta(days=7)).isoformat(),
        reels=[ReelResult(r.title, kind, r.views, r.outlier_score) for r, kind in reels],
        themes=[ThemeSummary(t.theme, t.idea, t.size) for t in themes],
        hints=hints,
    )
    report_week = monday - timedelta(days=7)
    existing = (
        await session.execute(
            select(WeeklyReport).where(
                WeeklyReport.user_id == user_id, WeeklyReport.week_start == report_week
            )
        )
    ).scalar_one_or_none()
    report = existing or WeeklyReport(user_id=user_id, week_start=report_week)
    report.content = content.model_dump()
    session.add(report)
    await session.commit()
    return report


async def latest(session: AsyncSession, user_id: UUID) -> WeeklyReportContent:
    report = (
        await session.execute(
            select(WeeklyReport)
            .where(WeeklyReport.user_id == user_id)
            .order_by(WeeklyReport.week_start.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if report is None:
        raise ApiError(
            status.HTTP_404_NOT_FOUND,
            "report_not_ready",
            "No weekly report yet. The first one arrives on Monday.",
        )
    return WeeklyReportContent.model_validate(report.content)


async def build_all(session: AsyncSession, now: datetime | None = None) -> int:
    """Run weekly by beat, for every creator who finished onboarding."""
    users = list((await session.execute(select(User.id))).scalars())
    for user_id in users:
        await build_for_user(session, user_id, now)
    return len(users)
