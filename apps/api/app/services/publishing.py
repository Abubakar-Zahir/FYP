"""The experiments.publish job (SRS FR-6.4 to FR-6.8, NFR-7).

Each variant gets its own hook line burned onto the edited video, then goes out as a Trial
Reel: create the container, wait until Instagram has processed it, publish. The quota is
checked first. If the account can't post Trial Reels, only the learner's top pick goes out,
as a normal reel, because posting every variant publicly would look like duplicate content.
A retried job never republishes a variant that is already live.
"""

import asyncio
import logging
import tempfile
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import DecryptionFailed, TokenCipher
from app.models.experiment import Experiment, ExperimentStatus, Variant, VariantStatus
from app.models.instagram_account import InstagramAccount
from app.models.video import Video
from app.services import instagram, instagram_accounts
from app.services.storage import Storage
from app.services.videos import OUTPUT_CONTENT_TYPE
from app.workers.runner import JobContext, JobFailure, JobHandler, TransientJobError
from ml.edit.render import RenderFailed

logger = logging.getLogger(__name__)

STATUS_POLL_S = 60.0  # Meta: check once a minute, for at most 5 minutes
STATUS_MAX_POLLS = 5
SOURCE_FILE = "edited.mp4"
# The cover frame Instagram shows, by the variant's opener type.
THUMB_OFFSET_MS = {"face": 500, "product": 2000, "text": 0}
TRIAL_UNAVAILABLE = "trial_reels_unavailable"

Sleep = Callable[[float], Awaitable[None]]
HttpFactory = Callable[[], httpx.AsyncClient]
# (source, output, hook text) -> None. Blocking FFmpeg, run in a thread.
RenderHook = Callable[[Path, Path, str], None]


@dataclass(frozen=True)
class PublishDependencies:
    http_factory: HttpFactory
    storage: Storage | None
    render_hook: RenderHook
    sleep: Sleep = asyncio.sleep


def variant_key(user_id: object, experiment_id: object, label: str) -> str:
    return f"users/{user_id}/experiments/{experiment_id}/{label}.mp4"


async def _wait_until_finished(client: instagram.InstagramClient, container_id: str, sleep: Sleep) -> None:
    status = "unknown"
    for attempt in range(STATUS_MAX_POLLS):
        if attempt:
            await sleep(STATUS_POLL_S)
        status = await client.container_status(container_id)
        if status == instagram.FINISHED_STATUS:
            return
        if status in instagram.FAILED_STATUSES:
            raise instagram.InstagramError(f"Container ended with status {status}")
    raise instagram.InstagramUnavailable(f"Container still {status} after {STATUS_MAX_POLLS} checks")


async def _account_and_client(
    context: JobContext, http: httpx.AsyncClient
) -> tuple[InstagramAccount, instagram.InstagramClient]:
    account = await instagram_accounts.get_account(context.session, context.job.user_id)
    if account is None:
        raise JobFailure("instagram_not_connected")
    key = context.settings.token_encryption_key
    if key is None:
        raise JobFailure("encryption_not_configured")
    try:
        token = TokenCipher(key.get_secret_value()).decrypt(account.encrypted_token)
    except DecryptionFailed as error:
        raise JobFailure("instagram_reconnect_needed") from error
    return account, instagram.InstagramClient(http, token)


async def _check_quota(client: instagram.InstagramClient, account: InstagramAccount, needed: int) -> None:
    limit = await client.publishing_limit(account.ig_user_id)
    if limit.quota_total is not None and limit.quota_usage + needed > limit.quota_total:
        raise JobFailure("publish_quota_reached")


async def _publish_one(
    client: instagram.InstagramClient,
    account: InstagramAccount,
    variant: Variant,
    video_url: str,
    trial: instagram.GraduationStrategy | None,
    sleep: Sleep,
) -> None:
    container = await client.create_reel_container(
        account.ig_user_id, video_url, variant.caption, trial, THUMB_OFFSET_MS.get(variant.opener_type)
    )
    await _wait_until_finished(client, container, sleep)
    variant.ig_media_id = await client.publish(account.ig_user_id, container)
    variant.permalink = await client.permalink(variant.ig_media_id)
    variant.is_trial = trial is not None
    variant.status = VariantStatus.LIVE
    variant.published_at = datetime.now(UTC)
    variant.error = None


async def _render_and_upload(
    dependencies: PublishDependencies, storage: Storage, source: Path, folder: Path, variant: Variant
) -> str:
    output = folder / f"{variant.label}.mp4"
    try:
        await asyncio.to_thread(dependencies.render_hook, source, output, variant.hook_line)
    except RenderFailed as error:
        raise JobFailure("render_failed") from error
    key = variant_key(variant.user_id, variant.experiment_id, variant.label)
    await storage.upload_file(output, key, OUTPUT_CONTENT_TYPE)
    variant.r2_key = key
    # Instagram fetches the file within minutes of the container call, well inside the link's hour.
    return storage.download_url(key)


async def _load(session: AsyncSession, context: JobContext) -> tuple[Experiment, Video, list[Variant]]:
    experiment = await session.get(Experiment, context.job.subject_id) if context.job.subject_id else None
    if experiment is None or experiment.user_id != context.job.user_id:
        raise JobFailure("experiment_not_found")
    video = await session.get(Video, experiment.video_id)
    if video is None or not video.output_r2_key:
        raise JobFailure("video_not_edited")
    variants = list(
        (
            await session.execute(
                select(Variant)
                .where(Variant.experiment_id == experiment.id, Variant.status != VariantStatus.LIVE)
                .order_by(Variant.label)
            )
        ).scalars()
    )
    return experiment, video, variants


async def _publish(context: JobContext, dependencies: PublishDependencies) -> dict[str, Any]:
    session, storage = context.session, dependencies.storage
    if storage is None:
        raise JobFailure("storage_not_configured")
    experiment, video, pending = await _load(session, context)
    trial = instagram.GraduationStrategy(context.settings.trial_graduation_strategy)
    async with dependencies.http_factory() as http:
        account, client = await _account_and_client(context, http)
        await _check_quota(client, account, len(pending))
        experiment.status = ExperimentStatus.PUBLISHING
        for variant in pending:
            variant.status = VariantStatus.PUBLISHING
        await session.commit()
        with tempfile.TemporaryDirectory(prefix="publish-") as folder:
            source = Path(folder) / SOURCE_FILE
            await storage.download_to(str(video.output_r2_key), source)
            for index, variant in enumerate(pending):
                url = await _render_and_upload(dependencies, storage, source, Path(folder), variant)
                try:
                    await _publish_one(
                        client,
                        account,
                        variant,
                        url,
                        None if account.trial_reels_eligible is False else trial,
                        dependencies.sleep,
                    )
                    if not variant.is_trial:
                        _skip_rest(pending[index + 1 :])
                        break
                    account.trial_reels_eligible = True
                except instagram.InstagramUnavailable:
                    await session.commit()
                    raise
                except instagram.InstagramError as error:
                    logger.warning("Publishing variant %s failed: %s", variant.label, error)
                    if variant.is_trial and account.trial_reels_eligible is None:
                        # The first Trial Reel was refused. Fall back to one normal reel (FR-6.8).
                        account.trial_reels_eligible = False
                        await _publish_one(client, account, variant, url, None, dependencies.sleep)
                        _skip_rest(pending[index + 1 :])
                        break
                    variant.status = VariantStatus.FAILED
                    variant.error = "instagram_rejected"
                await context.progress((index + 1) / len(pending))
                await session.commit()
    live = await session.execute(
        select(Variant).where(Variant.experiment_id == experiment.id, Variant.status == VariantStatus.LIVE)
    )
    live_variants = list(live.scalars())
    experiment.status = ExperimentStatus.LIVE if live_variants else ExperimentStatus.DRAFT
    await session.commit()
    if not live_variants:
        raise JobFailure("publish_failed")
    return {
        "experiment_id": str(experiment.id),
        "live": len(live_variants),
        "trial": any(v.is_trial for v in live_variants),
    }


def _skip_rest(variants: list[Variant]) -> None:
    for variant in variants:
        variant.status = VariantStatus.FAILED
        variant.error = TRIAL_UNAVAILABLE


def make_publish_handler(dependencies: PublishDependencies) -> JobHandler:
    async def handle(context: JobContext) -> dict[str, Any]:
        try:
            return await _publish(context, dependencies)
        except instagram.InstagramUnavailable as error:
            raise TransientJobError("instagram_unavailable") from error
        except instagram.InstagramError as error:
            raise JobFailure("instagram_rejected") from error

    return handle
