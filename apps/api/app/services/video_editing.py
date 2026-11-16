"""The videos.edit job (roadmap Phase 2, item 3): raw footage in, a captioned, cut video out.

Transcription is passed in, so this module never imports Whisper or OpenCV and the API and
tests load it without the `video` group.
"""

import asyncio
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.models.video import Video
from app.schemas.videos import EditRequest, EditResult
from app.services.storage import Storage
from app.services.videos import OUTPUT_CONTENT_TYPE, output_key
from app.workers.runner import JobContext, JobFailure, JobHandler
from ml.dna.errors import UnreadableVideo, VideoTooLong
from ml.edit.captions import CaptionStyle
from ml.edit.cuts import Word
from ml.edit.pipeline import EditOptions, edit_video
from ml.edit.render import RenderFailed

SOURCE_FILE = "source.mp4"
OUTPUT_FILE = "edited.mp4"

# Video in, word timings and length out. Blocking, so it runs in a thread.
Transcribe = Callable[[Path], tuple[list[Word], float]]


@dataclass(frozen=True)
class EditDependencies:
    transcribe: Transcribe
    storage: Storage | None


def _options(request: EditRequest) -> EditOptions:
    return EditOptions(
        caption_style=CaptionStyle(request.caption_style),
        cut_silences=request.cut_silences,
        progress_bar=request.progress_bar,
        hook_overlay=request.hook_overlay,
        roman_urdu_captions=request.roman_urdu_captions,
    )


async def _edit(context: JobContext, dependencies: EditDependencies) -> EditResult:
    storage = dependencies.storage
    if storage is None:
        raise JobFailure("storage_not_configured")
    video = await context.session.get(Video, context.job.subject_id) if context.job.subject_id else None
    if video is None or video.user_id != context.job.user_id:
        raise JobFailure("video_not_found")
    request = EditRequest.model_validate(context.job.payload or {})
    with tempfile.TemporaryDirectory(prefix="edit-") as folder:
        source, output = Path(folder) / SOURCE_FILE, Path(folder) / OUTPUT_FILE
        if await storage.size_of(video.source_r2_key) is None:
            raise JobFailure("upload_missing")
        await storage.download_to(video.source_r2_key, source)
        await context.progress(0.1)
        try:
            words, length_s = await asyncio.to_thread(dependencies.transcribe, source)
        except VideoTooLong as error:
            raise JobFailure("video_too_long") from error
        except UnreadableVideo as error:
            raise JobFailure("video_unreadable") from error
        await context.progress(0.5)
        try:
            outcome = await asyncio.to_thread(
                edit_video,
                context.settings.ffmpeg_path,
                source,
                output,
                words,
                length_s,
                _options(request),
                request.hook_text,
            )
        except RenderFailed as error:
            raise JobFailure("render_failed") from error
        key = output_key(video.user_id, video.id)
        await storage.upload_file(output, key, OUTPUT_CONTENT_TYPE)
    video.output_r2_key = key
    video.duration_s = outcome.duration_s
    video.removed_silence_s = outcome.removed_silence_s
    video.options = request.model_dump(mode="json")
    await context.session.commit()
    return EditResult(
        output_url=storage.download_url(key),
        duration_s=outcome.duration_s,
        removed_silence_s=outcome.removed_silence_s,
    )


def make_edit_handler(dependencies: EditDependencies) -> JobHandler:
    async def handle(context: JobContext) -> dict[str, Any]:
        return (await _edit(context, dependencies)).model_dump()

    return handle
