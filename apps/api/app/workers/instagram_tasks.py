from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.crypto import TokenCipher
from app.core.settings import get_settings
from app.services.reel_import import make_import_handler
from app.services.token_refresh import refresh_expiring_tokens
from app.workers.celery_app import MAX_RETRIES, celery_app
from app.workers.runner import TransientJobError, execute, run_with_sessions
from app.workers.tasks import TaskName

_import_handler = make_import_handler(httpx.AsyncClient)


# Any: Celery's bound task type ships without type information.
@celery_app.task(
    name=TaskName.INSTAGRAM_IMPORT.value,
    bind=True,
    autoretry_for=(TransientJobError,),
    retry_backoff=True,
    max_retries=MAX_RETRIES,
)
def import_reels(self: Any, job_id: str) -> None:
    execute(get_settings(), job_id, _import_handler, final_attempt=self.request.retries >= MAX_RETRIES)


@celery_app.task(name=TaskName.INSTAGRAM_REFRESH_TOKENS.value)
def refresh_tokens() -> int:
    settings = get_settings()
    if settings.token_encryption_key is None:
        raise RuntimeError("TOKEN_ENCRYPTION_KEY is required to refresh Instagram tokens.")
    cipher = TokenCipher(settings.token_encryption_key.get_secret_value())

    async def work(factory: async_sessionmaker[AsyncSession]) -> int:
        async with factory() as session, httpx.AsyncClient() as http:
            return await refresh_expiring_tokens(session, http, cipher, datetime.now(UTC))

    return run_with_sessions(settings, work)
