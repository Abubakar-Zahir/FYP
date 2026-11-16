"""The Celery app. Start a worker with:

uv run celery -A app.workers.celery_app worker --queues default,ai -l info   (from apps/api)
"""

from celery import Celery

from app.core.settings import Settings, get_settings
from app.workers.tasks import TASK_QUEUES, Queue

TASK_MODULES: list[str] = []
# Hard limit kills a stuck task. The soft limit comes first so cleanup in `finally` can run.
TASK_SOFT_TIME_LIMIT_S = 15 * 60
TASK_TIME_LIMIT_S = TASK_SOFT_TIME_LIMIT_S + 60
MAX_RETRIES = 3


def create_celery(settings: Settings) -> Celery:
    celery = Celery("fyp", broker=settings.redis_url, include=TASK_MODULES)
    celery.conf.update(
        task_default_queue=Queue.DEFAULT.value,
        task_routes={name.value: {"queue": queue.value} for name, queue in TASK_QUEUES.items()},
        # Results live in the jobs table, so Celery's own result store is off.
        task_ignore_result=True,
        # Ack after the task ends, so a worker that dies mid-job gives the job back.
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1,
        task_soft_time_limit=TASK_SOFT_TIME_LIMIT_S,
        task_time_limit=TASK_TIME_LIMIT_S,
        broker_connection_retry_on_startup=True,
        timezone="UTC",
    )
    return celery


celery_app = create_celery(get_settings())
