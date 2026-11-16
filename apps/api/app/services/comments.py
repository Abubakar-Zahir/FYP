from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Page
from app.models.reel import Comment, CommentTheme
from app.schemas.comments import CommentSummaryOut, CommentThemeOut, LabelCount
from ml.comments.labels import CommentLabel

SUMMARY_PERIOD_DAYS = 30


async def summary(session: AsyncSession, user_id: UUID, now: datetime | None = None) -> CommentSummaryOut:
    since = (now or datetime.now(UTC)) - timedelta(days=SUMMARY_PERIOD_DAYS)
    query = (
        select(Comment.label, func.count())
        .where(Comment.user_id == user_id, Comment.label.is_not(None), Comment.posted_at >= since)
        .group_by(Comment.label)
    )
    counts = {str(label): int(count) for label, count in (await session.execute(query)).all()}
    by_label = [
        LabelCount(label=label, count=counts[label.value])
        for label in CommentLabel
        if counts.get(label.value)
    ]
    by_label.sort(key=lambda item: item.count, reverse=True)
    return CommentSummaryOut(total=sum(counts.values()), period_days=SUMMARY_PERIOD_DAYS, by_label=by_label)


async def themes(session: AsyncSession, user_id: UUID) -> Page[CommentThemeOut]:
    """At most MAX_THEMES rows, so the whole list is one page."""
    rows = list(
        (
            await session.execute(
                select(CommentTheme).where(CommentTheme.user_id == user_id).order_by(CommentTheme.size.desc())
            )
        ).scalars()
    )
    example_ids = {UUID(value) for row in rows for value in row.example_comment_ids}
    texts: dict[UUID, str] = {}
    if example_ids:
        found = await session.execute(select(Comment.id, Comment.text).where(Comment.id.in_(example_ids)))
        texts = {comment_id: text for comment_id, text in found.all()}
    items = [
        CommentThemeOut(
            id=row.id,
            theme=row.theme,
            size=row.size,
            dominant_label=CommentLabel(row.dominant_label),
            examples=[texts[UUID(value)] for value in row.example_comment_ids if UUID(value) in texts],
            idea=row.idea,
        )
        for row in rows
    ]
    return Page[CommentThemeOut](items=items, next_cursor=None)
