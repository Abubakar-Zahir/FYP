from typing import Any

import httpx

from app.core.settings import get_settings
from app.services.comment_intelligence import make_sync_handler
from app.workers.celery_app import MAX_RETRIES, celery_app
from app.workers.runner import TransientJobError, execute
from app.workers.tasks import TaskName

_handler = make_sync_handler(httpx.AsyncClient)


@celery_app.task(
    name=TaskName.COMMENTS_SYNC.value,
    bind=True,
    autoretry_for=(TransientJobError,),
    retry_backoff=True,
    max_retries=MAX_RETRIES,
)
def sync_comments(self: Any, job_id: str) -> None:
    execute(get_settings(), job_id, _handler, final_attempt=self.request.retries >= MAX_RETRIES)
