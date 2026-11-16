from pathlib import Path
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.crypto import TokenCipher
from app.core.settings import get_settings
from app.services import insights
from app.services.experiments import make_create_handler
from app.services.publishing import PublishDependencies, make_publish_handler
from app.services.storage import build_storage
from app.workers.celery_app import MAX_RETRIES, celery_app
from app.workers.runner import TransientJobError, execute, run_with_sessions
from app.workers.tasks import TaskName
from ml.edit.pipeline import overlay_hook

_create = make_create_handler(httpx.AsyncClient)


def _render_hook(source: Path, output: Path, hook_text: str) -> None:
    overlay_hook(get_settings().ffmpeg_path, source, output, hook_text)


@celery_app.task(
    name=TaskName.EXPERIMENTS_CREATE.value,
    bind=True,
    autoretry_for=(TransientJobError,),
    retry_backoff=True,
    max_retries=MAX_RETRIES,
)
def create_experiment(self: Any, job_id: str) -> None:
    execute(get_settings(), job_id, _create, final_attempt=self.request.retries >= MAX_RETRIES)


@celery_app.task(
    name=TaskName.EXPERIMENTS_PUBLISH.value,
    bind=True,
    autoretry_for=(TransientJobError,),
    retry_backoff=True,
    max_retries=MAX_RETRIES,
)
def publish_experiment(self: Any, job_id: str) -> None:
    settings = get_settings()
    handler = make_publish_handler(
        PublishDependencies(
            http_factory=httpx.AsyncClient, storage=build_storage(settings), render_hook=_render_hook
        )
    )
    execute(settings, job_id, handler, final_attempt=self.request.retries >= MAX_RETRIES)


@celery_app.task(name=TaskName.EXPERIMENTS_COLLECT_INSIGHTS.value)
def collect_insights() -> dict[str, int]:
    settings = get_settings()
    if settings.token_encryption_key is None:
        raise RuntimeError("TOKEN_ENCRYPTION_KEY is required to read insights.")
    cipher = TokenCipher(settings.token_encryption_key.get_secret_value())

    async def work(factory: async_sessionmaker[AsyncSession]) -> dict[str, int]:
        async with factory() as session, httpx.AsyncClient() as http:
            return await insights.collect(session, http, cipher)

    return run_with_sessions(settings, work)
