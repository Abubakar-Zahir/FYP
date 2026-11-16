"""Runs on the video worker, which has the `video` dependency group installed."""

from functools import cache
from pathlib import Path
from typing import Any

import httpx

from app.core.settings import get_settings
from app.services.dna_analysis import DnaDependencies, make_analyse_handler
from app.services.storage import build_storage
from app.workers.celery_app import MAX_RETRIES, celery_app
from app.workers.runner import TransientJobError, execute
from app.workers.tasks import TaskName
from ml.dna.schema import ReelSignals


@cache
def _extractor() -> Any:
    """Loaded on first use and kept, because loading Whisper takes seconds.

    Any: the Extractor type lives in ml.dna.extract, which needs OpenCV, so it is imported here only.
    """
    from ml.dna.extract import ExtractOptions, Extractor

    settings = get_settings()
    return Extractor(
        ExtractOptions(whisper_model=settings.whisper_model, cut_threshold=settings.dna_cut_threshold)
    )


def _extract(video: Path, keyframes: Path) -> ReelSignals:
    signals: ReelSignals = _extractor().extract(video, keyframes)
    return signals


@celery_app.task(
    name=TaskName.DNA_ANALYSE.value,
    bind=True,
    autoretry_for=(TransientJobError,),
    retry_backoff=True,
    max_retries=MAX_RETRIES,
)
def analyse_reel(self: Any, job_id: str) -> None:
    settings = get_settings()
    handler = make_analyse_handler(
        DnaDependencies(extract=_extract, storage=build_storage(settings), http_factory=httpx.AsyncClient)
    )
    execute(settings, job_id, handler, final_attempt=self.request.retries >= MAX_RETRIES)
