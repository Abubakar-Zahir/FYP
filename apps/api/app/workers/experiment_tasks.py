from typing import Any

import httpx

from app.core.settings import get_settings
from app.services.experiments import make_create_handler
from app.workers.celery_app import MAX_RETRIES, celery_app
from app.workers.runner import TransientJobError, execute
from app.workers.tasks import TaskName

_create = make_create_handler(httpx.AsyncClient)


@celery_app.task(
    name=TaskName.EXPERIMENTS_CREATE.value,
    bind=True,
    autoretry_for=(TransientJobError,),
    retry_backoff=True,
    max_retries=MAX_RETRIES,
)
def create_experiment(self: Any, job_id: str) -> None:
    execute(get_settings(), job_id, _create, final_attempt=self.request.retries >= MAX_RETRIES)
