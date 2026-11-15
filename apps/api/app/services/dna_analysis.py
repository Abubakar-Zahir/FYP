"""The dna.analyse job: video in, DnaRecord out (P1-04, SRS FR-2.1 to FR-2.4).

The extractor is passed in, so this module never imports OpenCV or Whisper, and the API
and tests can load it without the `video` dependency group.
"""

import asyncio
import logging
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import DecryptionFailed, TokenCipher
from app.models.dna import DnaRecordRow
from app.models.reel import Reel, ReelSource
from app.schemas.dna import AnalyseResult
from app.services import instagram, instagram_accounts, llm
from app.services.storage import Storage
from app.workers.runner import JobContext, JobFailure, JobHandler, TransientJobError
from ml.dna.errors import UnreadableVideo, VideoTooLong
from ml.dna.schema import DnaRecord, ReelSignals
from ml.dna.structure import (
    MAX_OUTPUT_TOKENS,
    PROMPT_VERSION,
    CallLlm,
    StructuringError,
    StructuringPrompt,
    structure,
)

logger = logging.getLogger(__name__)

PURPOSE = "dna.structure"
DOWNLOAD_TIMEOUT_S = 120.0
DOWNLOAD_CHUNK_BYTES = 1024 * 1024
VIDEO_FILE_NAME = "reel.mp4"

# Takes the video and a folder for keyframes. Blocking, so it runs in a thread.
Extract = Callable[[Path, Path], ReelSignals]
HttpFactory = Callable[[], httpx.AsyncClient]


@dataclass(frozen=True)
class DnaDependencies:
    extract: Extract
    storage: Storage | None
    http_factory: HttpFactory


def _cipher(context: JobContext) -> TokenCipher:
    key = context.settings.token_encryption_key
    if key is None:
        raise JobFailure("encryption_not_configured")
    return TokenCipher(key.get_secret_value())


async def _download_own_reel(context: JobContext, http: httpx.AsyncClient, reel: Reel, path: Path) -> None:
    """Own reels come from Instagram's media_url, which is fetched fresh because it expires."""
    account = await instagram_accounts.get_account(context.session, reel.user_id)
    if account is None or reel.ig_media_id is None:
        raise JobFailure("instagram_not_connected")
    try:
        token = _cipher(context).decrypt(account.encrypted_token)
    except DecryptionFailed as error:
        raise JobFailure("instagram_reconnect_needed") from error
    url = await instagram.InstagramClient(http, token).media_url(reel.ig_media_id)
    async with http.stream("GET", url, timeout=DOWNLOAD_TIMEOUT_S) as response:
        if response.is_error:
            raise TransientJobError("video_download_failed")
        with path.open("wb") as file:
            async for chunk in response.aiter_bytes(DOWNLOAD_CHUNK_BYTES):
                file.write(chunk)


async def _download(
    context: JobContext, dependencies: DnaDependencies, http: httpx.AsyncClient, reel: Reel, path: Path
) -> None:
    if reel.source == ReelSource.REFERENCE:
        if dependencies.storage is None:
            raise JobFailure("storage_not_configured")
        if not reel.r2_key or await dependencies.storage.size_of(reel.r2_key) is None:
            raise JobFailure("upload_missing")
        await dependencies.storage.download_to(reel.r2_key, path)
    else:
        await _download_own_reel(context, http, reel, path)


def _llm_caller(client: llm.LlmClient, user_id: UUID) -> CallLlm:
    async def call(prompt: StructuringPrompt) -> str:
        return await client.complete(
            llm.LlmPrompt(system=prompt.system, user=prompt.user, max_output_tokens=MAX_OUTPUT_TOKENS),
            purpose=PURPOSE,
            prompt_version=PROMPT_VERSION,
            user_id=user_id,
        )

    return call


async def _structure(context: JobContext, http: httpx.AsyncClient, signals: ReelSignals) -> DnaRecord:
    try:
        client = llm.build_llm_client(context.settings, http, llm.DatabaseLedger(context.session))
        return await structure(signals, _llm_caller(client, context.job.user_id), client.model_version)
    except llm.LlmNotConfigured as error:
        raise JobFailure("llm_not_configured") from error
    except llm.LlmBudgetExceeded as error:
        raise JobFailure("llm_budget_exceeded") from error
    except llm.LlmUnavailable as error:
        raise TransientJobError("llm_unavailable") from error
    except (llm.LlmRequestRejected, llm.LlmBadResponse, StructuringError) as error:
        logger.warning("DNA structuring failed: %s", type(error).__name__)
        raise JobFailure("dna_structuring_failed") from error


async def _save(session: AsyncSession, reel: Reel, record: DnaRecord) -> DnaRecordRow:
    existing = await session.execute(select(DnaRecordRow).where(DnaRecordRow.reel_id == reel.id))
    row = existing.scalar_one_or_none() or DnaRecordRow(
        user_id=reel.user_id, reel_id=reel.id, is_template=False
    )
    # Keyframes lived in the job's temp folder, which is gone. Nothing reads them until OCR is wired.
    stored = record.model_copy(update={"signals": record.signals.model_copy(update={"keyframe_paths": []})})
    row.schema_version = stored.schema_version
    row.hook_type = stored.hook_type.value
    row.hook_text = stored.hook_text
    row.pacing_cuts_per_10s = stored.signals.pacing_cuts_per_10s
    row.length_s = stored.signals.length_s
    row.cta = stored.cta
    row.transcript = " ".join(segment.text.strip() for segment in stored.signals.transcript).strip()
    row.record = stored.model_dump(mode="json")
    row.model_version = stored.model_version
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def _analyse(context: JobContext, dependencies: DnaDependencies) -> AnalyseResult:
    reel = await context.session.get(Reel, context.job.subject_id) if context.job.subject_id else None
    if reel is None or reel.user_id != context.job.user_id:
        raise JobFailure("reel_not_found")
    async with dependencies.http_factory() as http:
        with tempfile.TemporaryDirectory(prefix="dna-") as folder:
            video = Path(folder) / VIDEO_FILE_NAME
            await _download(context, dependencies, http, reel, video)
            await context.progress(0.2)
            try:
                signals = await asyncio.to_thread(dependencies.extract, video, Path(folder) / "keyframes")
            except VideoTooLong as error:
                raise JobFailure("video_too_long") from error
            except UnreadableVideo as error:
                raise JobFailure("video_unreadable") from error
        await context.progress(0.7)
        record = await _structure(context, http, signals)
    row = await _save(context.session, reel, record)
    return AnalyseResult(dna_id=row.id)


def make_analyse_handler(dependencies: DnaDependencies) -> JobHandler:
    async def handle(context: JobContext) -> dict[str, Any]:
        try:
            result = await _analyse(context, dependencies)
        except instagram.InstagramUnavailable as error:
            raise TransientJobError("instagram_unavailable") from error
        except instagram.InstagramError as error:
            raise JobFailure("instagram_rejected") from error
        except httpx.TransportError as error:
            raise TransientJobError("video_download_failed") from error
        return result.model_dump(mode="json")

    return handle
