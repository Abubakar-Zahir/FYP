import asyncio
from typing import Annotated, Protocol
from uuid import UUID

from celery import Celery
from fastapi import Depends, Request, status

from app.core.errors import ApiError
from app.workers.tasks import TASK_QUEUES, TaskName


class JobQueue(Protocol):
    async def enqueue(self, task: TaskName, job_id: UUID) -> None: ...


class CeleryJobQueue:
    """Sends by name, so the API process never imports task code or ML libraries."""

    def __init__(self, celery: Celery) -> None:
        self._celery = celery

    async def enqueue(self, task: TaskName, job_id: UUID) -> None:
        # send_task talks to Redis synchronously, so it runs off the event loop (rules.md 3.5).
        await asyncio.to_thread(
            self._celery.send_task, task.value, kwargs={"job_id": str(job_id)}, queue=TASK_QUEUES[task].value
        )


def get_job_queue(request: Request) -> JobQueue:
    queue: JobQueue | None = request.app.state.job_queue
    if queue is None:
        raise ApiError(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "jobs_not_configured",
            "Background jobs are not configured on this server.",
        )
    return queue


JobQueueDependency = Annotated[JobQueue, Depends(get_job_queue)]
