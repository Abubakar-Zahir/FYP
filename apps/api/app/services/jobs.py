import logging
from typing import Any
from uuid import UUID

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.models.job import Job, JobStatus
from app.workers.queue import JobQueue
from app.workers.tasks import TaskName

logger = logging.getLogger(__name__)

QUEUE_UNAVAILABLE = "queue_unavailable"


def job_not_found() -> ApiError:
    return ApiError(status.HTTP_404_NOT_FOUND, "job_not_found", "No such job.")


async def get_job_for_user(session: AsyncSession, job_id: UUID, user_id: UUID) -> Job:
    """Someone else's job looks exactly like a missing one, so ids can't be probed."""
    job = await session.get(Job, job_id)
    if job is None or job.user_id != user_id:
        raise job_not_found()
    return job


async def start_job(session: AsyncSession, queue: JobQueue, user_id: UUID, task: TaskName) -> Job:
    """Commits the row before enqueueing, so a fast worker always finds it."""
    job = Job(user_id=user_id, type=task.value, status=JobStatus.QUEUED, progress=0.0)
    session.add(job)
    await session.commit()
    try:
        await queue.enqueue(task, job.id)
    except Exception as error:
        logger.exception("Could not enqueue job", extra={"job_id": str(job.id), "task": task.value})
        await mark_failed(session, job, QUEUE_UNAVAILABLE)
        raise ApiError(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            QUEUE_UNAVAILABLE,
            "The job could not be started. Try again shortly.",
        ) from error
    return job


async def mark_running(session: AsyncSession, job: Job) -> None:
    job.status = JobStatus.RUNNING
    job.error = None
    await session.commit()


async def set_progress(session: AsyncSession, job: Job, progress: float) -> None:
    job.progress = min(max(progress, 0.0), 1.0)
    await session.commit()


async def mark_done(session: AsyncSession, job: Job, result: dict[str, Any]) -> None:
    job.status = JobStatus.DONE
    job.progress = 1.0
    job.result = result
    job.error = None
    await session.commit()


async def mark_failed(session: AsyncSession, job: Job, code: str) -> None:
    job.status = JobStatus.FAILED
    job.error = code
    await session.commit()


async def mark_retrying(session: AsyncSession, job: Job, code: str) -> None:
    job.status = JobStatus.QUEUED
    job.error = code
    await session.commit()
