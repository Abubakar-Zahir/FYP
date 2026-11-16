from typing import Any

import httpx

from app.core.settings import get_settings
from app.services.hook_scoring import make_score_handler
from app.services.script_generation import make_generate_handler
from app.workers.celery_app import MAX_RETRIES, celery_app
from app.workers.runner import TransientJobError, execute
from app.workers.tasks import TaskName

_handler = make_generate_handler(httpx.AsyncClient)


@celery_app.task(
    name=TaskName.SCRIPTS_GENERATE.value,
    bind=True,
    autoretry_for=(TransientJobError,),
    retry_backoff=True,
    max_retries=MAX_RETRIES,
)
def generate_script(self: Any, job_id: str) -> None:
    execute(get_settings(), job_id, _handler, final_attempt=self.request.retries >= MAX_RETRIES)


_score_handler = make_score_handler()


@celery_app.task(name=TaskName.HOOKS_SCORE.value, bind=True)
def score_hooks(self: Any, job_id: str) -> None:
    execute(get_settings(), job_id, _score_handler, final_attempt=True)
