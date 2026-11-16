"""Auto-edit runs on the video worker, which has Whisper (the `video` group) and the ffmpeg binary."""

from pathlib import Path
from typing import Any

from app.core.settings import get_settings
from app.services.storage import build_storage
from app.services.video_editing import EditDependencies, make_edit_handler
from app.workers.celery_app import MAX_RETRIES, celery_app
from app.workers.dna_tasks import _extractor
from app.workers.runner import TransientJobError, execute
from app.workers.tasks import TaskName
from ml.edit.cuts import Word


def _transcribe(video: Path) -> tuple[list[Word], float]:
    words: tuple[list[Word], float] = _extractor().words(video)
    return words


@celery_app.task(
    name=TaskName.VIDEOS_EDIT.value,
    bind=True,
    autoretry_for=(TransientJobError,),
    retry_backoff=True,
    max_retries=MAX_RETRIES,
)
def edit_video(self: Any, job_id: str) -> None:
    settings = get_settings()
    handler = make_edit_handler(EditDependencies(transcribe=_transcribe, storage=build_storage(settings)))
    execute(settings, job_id, handler, final_attempt=self.request.retries >= MAX_RETRIES)
