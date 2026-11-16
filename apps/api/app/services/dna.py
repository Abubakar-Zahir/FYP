import asyncio
from uuid import UUID

from fastapi import status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.core.pagination import Page, decode_cursor, encode_cursor
from app.models.dna import DnaRecordRow
from app.models.job import Job
from app.models.reel import Reel, ReelSource
from app.schemas.dna import DnaClusterOut, DnaRecordOut
from app.services import instagram_accounts, jobs, reels
from app.services.reels import as_utc
from app.services.storage import Storage, storage_not_configured
from app.workers.queue import JobQueue
from app.workers.tasks import TaskName
from ml.dna.clusters import cluster_formats
from ml.dna.schema import DnaRecord


def dna_not_found() -> ApiError:
    return ApiError(status.HTTP_404_NOT_FOUND, "dna_not_found", "No such DNA record.")


def to_out(row: DnaRecordRow, reel: Reel) -> DnaRecordOut:
    record = DnaRecord.model_validate(row.record)
    return DnaRecordOut(
        id=row.id,
        reel_id=reel.id,
        schema_version=row.schema_version,
        title=reel.title,
        source=ReelSource(reel.source),
        hook_type=record.hook_type,
        hook_text=row.hook_text,
        pacing_cuts_per_10s=row.pacing_cuts_per_10s,
        length_s=row.length_s,
        beats=record.beats,
        overlays=record.overlays,
        cta=row.cta,
        outlier_score=reel.outlier_score,
        transcript=row.transcript,
        is_template=row.is_template,
        model_version=row.model_version,
    )


async def get_for_user(session: AsyncSession, dna_id: UUID, user_id: UUID) -> tuple[DnaRecordRow, Reel]:
    row = await session.get(DnaRecordRow, dna_id)
    if row is None or row.user_id != user_id:
        raise dna_not_found()
    reel = await session.get(Reel, row.reel_id)
    if reel is None:
        raise dna_not_found()
    return row, reel


async def list_for_user(
    session: AsyncSession, user_id: UUID, limit: int, cursor: str | None, templates_only: bool
) -> Page[DnaRecordOut]:
    query = select(DnaRecordRow, Reel).join(Reel, Reel.id == DnaRecordRow.reel_id)
    query = query.where(DnaRecordRow.user_id == user_id)
    if templates_only:
        query = query.where(DnaRecordRow.is_template.is_(True))
    if cursor is not None:
        position = decode_cursor(cursor)
        query = query.where(
            or_(
                DnaRecordRow.created_at < position.at,
                and_(DnaRecordRow.created_at == position.at, DnaRecordRow.id < position.id),
            )
        )
    order = (DnaRecordRow.created_at.desc(), DnaRecordRow.id.desc())
    rows = (await session.execute(query.order_by(*order).limit(limit + 1))).all()
    page = rows[:limit]
    next_cursor = None
    if len(rows) > limit:
        last_row, _ = page[-1]
        next_cursor = encode_cursor(as_utc(last_row.created_at), last_row.id)
    return Page[DnaRecordOut](items=[to_out(row, reel) for row, reel in page], next_cursor=next_cursor)


async def set_template(session: AsyncSession, row: DnaRecordRow, is_template: bool) -> None:
    row.is_template = is_template
    await session.commit()


def upload_missing() -> ApiError:
    return ApiError(
        status.HTTP_409_CONFLICT,
        "upload_missing",
        "The video has not finished uploading. Upload it, then try again.",
    )


async def start_analysis(
    session: AsyncSession, queue: JobQueue, storage: Storage | None, user_id: UUID, reel_id: UUID
) -> Job:
    """Checks the video can be reached before queueing, so the job doesn't fail for an obvious reason."""
    reel = await reels.get_reel_for_user(session, reel_id, user_id)
    if reel.source == ReelSource.REFERENCE:
        if storage is None:
            raise storage_not_configured()
        if not reel.r2_key or await storage.size_of(reel.r2_key) is None:
            raise upload_missing()
    elif await instagram_accounts.get_account(session, user_id) is None:
        raise instagram_accounts.not_connected()
    return await jobs.start_job(session, queue, user_id, TaskName.DNA_ANALYSE, subject_id=reel.id)


MAX_CLUSTERED_RECORDS = 500


async def clusters(session: AsyncSession, user_id: UUID) -> list[DnaClusterOut]:
    """K-means on a few hundred short vectors takes milliseconds, so it runs off the event loop
    in the request rather than as a job."""
    rows = (
        await session.execute(
            select(DnaRecordRow, Reel.outlier_score)
            .join(Reel, Reel.id == DnaRecordRow.reel_id)
            .where(DnaRecordRow.user_id == user_id)
            .order_by(DnaRecordRow.created_at.desc())
            .limit(MAX_CLUSTERED_RECORDS)
        )
    ).all()
    records = [DnaRecord.model_validate(row.record) for row, _ in rows]
    found = await asyncio.to_thread(cluster_formats, records, [score for _, score in rows])
    return [
        DnaClusterOut(
            label=cluster.label,
            size=len(cluster.members),
            hook_type=cluster.hook_type,
            median_pacing_cuts_per_10s=cluster.median_pacing,
            median_length_s=cluster.median_length_s,
            median_outlier=cluster.median_outlier,
            dna_ids=[rows[index][0].id for index in cluster.members],
        )
        for cluster in found
    ]
