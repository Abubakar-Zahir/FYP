from datetime import UTC, datetime
from uuid import UUID

from fastapi import status
from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.core.pagination import Page, decode_cursor, encode_cursor
from app.models.reel import Comment, Reel, ReelSource
from app.schemas.reels import ReelOut

# Reels without a posted date (reference uploads) sort by when they were added.
_SORT_AT = func.coalesce(Reel.posted_at, Reel.created_at)


def reel_not_found() -> ApiError:
    return ApiError(status.HTTP_404_NOT_FOUND, "reel_not_found", "No such reel.")


async def get_reel_for_user(session: AsyncSession, reel_id: UUID, user_id: UUID) -> Reel:
    reel = await session.get(Reel, reel_id)
    if reel is None or reel.user_id != user_id:
        raise reel_not_found()
    return reel


async def list_reels(
    session: AsyncSession, user_id: UUID, limit: int, cursor: str | None, source: ReelSource | None
) -> Page[ReelOut]:
    query = select(Reel, _SORT_AT.label("sort_at")).where(Reel.user_id == user_id)
    if source is not None:
        query = query.where(Reel.source == source)
    if cursor is not None:
        position = decode_cursor(cursor)
        query = query.where(or_(_SORT_AT < position.at, and_(_SORT_AT == position.at, Reel.id < position.id)))
    rows = (await session.execute(query.order_by(_SORT_AT.desc(), Reel.id.desc()).limit(limit + 1))).all()
    page = rows[:limit]
    next_cursor = None
    if len(rows) > limit:
        last_reel, last_at = page[-1]
        next_cursor = encode_cursor(_as_utc(last_at), last_reel.id)
    return Page[ReelOut](items=[ReelOut.model_validate(reel) for reel, _ in page], next_cursor=next_cursor)


def _as_utc(value: datetime) -> datetime:
    # SQLite returns naive datetimes. Postgres returns aware ones.
    return value if value.tzinfo else value.replace(tzinfo=UTC)


async def delete_own_reels(session: AsyncSession, user_id: UUID) -> None:
    """Imported reels and their comments. Reference uploads belong to the user, not the account."""
    own = select(Reel.id).where(Reel.user_id == user_id, Reel.source == ReelSource.OWN)
    await session.execute(delete(Comment).where(Comment.reel_id.in_(own)))
    await session.execute(delete(Reel).where(Reel.user_id == user_id, Reel.source == ReelSource.OWN))
