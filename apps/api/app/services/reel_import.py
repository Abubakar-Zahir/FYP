"""Imports a creator's recent reels, their insights and comments (P1-03, SRS FR-1.3).

Runs inside the instagram.import job. Re-running it updates rows in place, so a retried
or repeated import never duplicates reels or comments.
"""

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import DecryptionFailed, TokenCipher
from app.models.reel import Comment, Reel, ReelSource
from app.schemas.reels import ImportResult
from app.services import instagram, instagram_accounts
from app.workers.runner import JobContext, JobFailure, JobHandler, TransientJobError
from ml.dna.outlier import outlier_score

logger = logging.getLogger(__name__)

REELS_TO_IMPORT = 50
TITLE_FROM_CAPTION_LENGTH = 80
UNTITLED = "Untitled reel"
INSTAGRAM_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

HttpFactory = Callable[[], httpx.AsyncClient]


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, INSTAGRAM_TIMESTAMP_FORMAT).astimezone(UTC)
    except ValueError:
        return None


def title_from_caption(caption: str | None) -> str:
    first_line = (caption or "").strip().split("\n", 1)[0].strip()
    if not first_line:
        return UNTITLED
    if len(first_line) <= TITLE_FROM_CAPTION_LENGTH:
        return first_line
    return first_line[: TITLE_FROM_CAPTION_LENGTH - 1].rstrip() + "…"


def _as_int(value: float | None) -> int | None:
    return None if value is None else int(value)


def _apply_insights(reel: Reel, insights: dict[str, float], fetched_at: datetime) -> None:
    reel.views = _as_int(insights.get("views"))
    reel.reach = _as_int(insights.get("reach"))
    reel.saves = _as_int(insights.get("saved"))
    reel.shares = _as_int(insights.get("shares"))
    watch_time_ms = insights.get("ig_reels_avg_watch_time")
    # Meta reports average watch time in milliseconds.
    reel.avg_watch_time_s = None if watch_time_ms is None else round(watch_time_ms / 1000, 2)
    reel.metrics_fetched_at = fetched_at


async def _upsert_reel(session: AsyncSession, user_id: UUID, media: instagram.Media) -> Reel:
    query = select(Reel).where(Reel.user_id == user_id, Reel.ig_media_id == media.id)
    reel = (await session.execute(query)).scalar_one_or_none()
    if reel is None:
        reel = Reel(user_id=user_id, source=ReelSource.OWN, ig_media_id=media.id)
        session.add(reel)
    reel.title = title_from_caption(media.caption)
    reel.caption = media.caption
    reel.permalink = media.permalink
    reel.posted_at = parse_timestamp(media.timestamp)
    return reel


async def _upsert_comments(
    session: AsyncSession, user_id: UUID, reel: Reel, comments: list[instagram.Comment]
) -> int:
    await session.flush()  # gives a new reel its id
    known = set(
        (await session.execute(select(Comment.ig_comment_id).where(Comment.reel_id == reel.id))).scalars()
    )
    for comment in comments:
        if comment.id not in known:
            session.add(
                Comment(
                    user_id=user_id,
                    reel_id=reel.id,
                    ig_comment_id=comment.id,
                    text=comment.text,
                    posted_at=parse_timestamp(comment.timestamp),
                )
            )
    return len(comments)


async def _optional_insights(client: instagram.InstagramClient, media_id: str) -> dict[str, float]:
    """Some reels (very new, or posted before the account turned professional) have no insights."""
    try:
        return await client.reel_insights(media_id)
    except instagram.InstagramUnavailable:
        raise
    except instagram.InstagramError:
        logger.info("No insights for one reel", extra={"media_id": media_id})
        return {}


def score_outliers(reels: list[Reel]) -> None:
    views = [reel.views for reel in reels if reel.views is not None]
    for reel in reels:
        reel.outlier_score = None if reel.views is None else outlier_score(reel.views, views)


def _token(context: JobContext, encrypted_token: str) -> str:
    key = context.settings.token_encryption_key
    if key is None:
        raise JobFailure("encryption_not_configured")
    try:
        return TokenCipher(key.get_secret_value()).decrypt(encrypted_token)
    except DecryptionFailed as error:
        # The key changed since the account connected. Only reconnecting fixes it.
        raise JobFailure("instagram_reconnect_needed") from error


async def _import(context: JobContext, http: httpx.AsyncClient) -> ImportResult:
    session, user_id = context.session, context.job.user_id
    account = await instagram_accounts.get_account(session, user_id)
    if account is None:
        raise JobFailure("instagram_not_connected")
    client = instagram.InstagramClient(http, _token(context, account.encrypted_token))
    media_list = await client.recent_reels(REELS_TO_IMPORT)
    fetched_at = datetime.now(UTC)
    imported: list[Reel] = []
    comment_count = 0
    for index, media in enumerate(media_list, start=1):
        reel = await _upsert_reel(session, user_id, media)
        _apply_insights(reel, await _optional_insights(client, media.id), fetched_at)
        comment_count += await _upsert_comments(session, user_id, reel, await client.comments(media.id))
        imported.append(reel)
        await context.progress(index / (len(media_list) + 1))
    all_own = (
        await session.execute(select(Reel).where(Reel.user_id == user_id, Reel.source == ReelSource.OWN))
    ).scalars()
    score_outliers(list(all_own))
    await session.commit()
    return ImportResult(reels=len(imported), comments=comment_count)


def make_import_handler(http_factory: HttpFactory) -> JobHandler:
    async def handle(context: JobContext) -> dict[str, Any]:
        try:
            async with http_factory() as http:
                result = await _import(context, http)
        except instagram.InstagramUnavailable as error:
            raise TransientJobError("instagram_unavailable") from error
        except instagram.InstagramError as error:
            logger.warning("Instagram refused the import: %s", error)
            raise JobFailure("instagram_rejected") from error
        return result.model_dump()

    return handle
