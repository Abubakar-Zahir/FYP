from datetime import UTC, datetime
from pathlib import PurePath
from uuid import UUID, uuid4

from fastapi import status
from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.core.pagination import Page, decode_cursor, encode_cursor
from app.models.dna import DnaRecordRow
from app.models.reel import Comment, Reel, ReelSource
from app.models.script import Script
from app.schemas.reels import ReelOut
from app.schemas.uploads import EXTENSIONS, ReferenceUpload, ReferenceUploadRequest
from app.services.storage import Storage, storage_not_configured

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
    query = (
        select(Reel, _SORT_AT.label("sort_at"), DnaRecordRow.hook_type)
        .outerjoin(DnaRecordRow, DnaRecordRow.reel_id == Reel.id)
        .where(Reel.user_id == user_id)
    )
    if source is not None:
        query = query.where(Reel.source == source)
    if cursor is not None:
        position = decode_cursor(cursor)
        query = query.where(or_(_SORT_AT < position.at, and_(_SORT_AT == position.at, Reel.id < position.id)))
    rows = (await session.execute(query.order_by(_SORT_AT.desc(), Reel.id.desc()).limit(limit + 1))).all()
    page = rows[:limit]
    next_cursor = None
    if len(rows) > limit:
        last_reel, last_at, _ = page[-1]
        next_cursor = encode_cursor(as_utc(last_at), last_reel.id)
    items = [ReelOut.from_reel(reel, hook_type) for reel, _, hook_type in page]
    return Page[ReelOut](items=items, next_cursor=next_cursor)


def as_utc(value: datetime) -> datetime:
    # SQLite returns naive datetimes. Postgres returns aware ones.
    return value if value.tzinfo else value.replace(tzinfo=UTC)


async def delete_own_reels(session: AsyncSession, user_id: UUID) -> None:
    """Imported reels and their comments. Reference uploads belong to the user, not the account."""
    own = select(Reel.id).where(Reel.user_id == user_id, Reel.source == ReelSource.OWN)
    await session.execute(delete(Comment).where(Comment.reel_id.in_(own)))
    own_dna = select(DnaRecordRow.id).where(DnaRecordRow.reel_id.in_(own))
    await session.execute(delete(Script).where(Script.template_id.in_(own_dna)))
    await session.execute(delete(DnaRecordRow).where(DnaRecordRow.reel_id.in_(own)))
    await session.execute(delete(Reel).where(Reel.user_id == user_id, Reel.source == ReelSource.OWN))


def reference_key(user_id: UUID, reel_id: UUID, extension: str) -> str:
    """Keys start with the user id, so one prefix holds everything a user uploaded."""
    return f"users/{user_id}/reference/{reel_id}{extension}"


def title_from_filename(filename: str) -> str:
    # PurePath drops any folder part a browser sends, and the stem drops the extension.
    return PurePath(filename.replace("\\", "/")).stem.strip() or "Reference reel"


async def create_reference(
    session: AsyncSession, storage: Storage, user_id: UUID, request: ReferenceUploadRequest
) -> ReferenceUpload:
    reel_id = uuid4()
    key = reference_key(user_id, reel_id, EXTENSIONS[request.content_type])
    reel = Reel(
        id=reel_id,
        user_id=user_id,
        source=ReelSource.REFERENCE,
        title=title_from_filename(request.filename),
        r2_key=key,
    )
    session.add(reel)
    await session.commit()
    await session.refresh(reel)
    return ReferenceUpload(
        reel=ReelOut.from_reel(reel),
        upload_url=storage.upload_url(key, request.content_type.value, request.size_bytes),
        upload_headers={"Content-Type": request.content_type.value},
    )


async def delete_reel(session: AsyncSession, storage: Storage | None, reel: Reel) -> None:
    if reel.r2_key:
        if storage is None:
            raise storage_not_configured()
        await storage.delete([reel.r2_key])
    await session.execute(delete(Comment).where(Comment.reel_id == reel.id))
    reel_dna = select(DnaRecordRow.id).where(DnaRecordRow.reel_id == reel.id)
    await session.execute(delete(Script).where(Script.template_id.in_(reel_dna)))
    await session.execute(delete(DnaRecordRow).where(DnaRecordRow.reel_id == reel.id))
    await session.delete(reel)
    await session.commit()


async def stored_keys(session: AsyncSession, user_id: UUID) -> list[str]:
    query = select(Reel.r2_key).where(Reel.user_id == user_id, Reel.r2_key.is_not(None))
    return [key for key in (await session.execute(query)).scalars() if key]
