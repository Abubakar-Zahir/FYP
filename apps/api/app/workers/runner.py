"""Runs one job: status bookkeeping around a handler, so every task behaves the same way.

Celery tasks are synchronous. Each run opens its own event loop and engine, because an
async engine can't be shared across the loops that successive asyncio.run calls create.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.settings import Settings
from app.models.job import Job, JobStatus
from app.services import jobs

logger = logging.getLogger(__name__)

INTERNAL_ERROR = "internal_error"


class JobFailure(Exception):
    """A failure the user should see, with a stable code. Not retried."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class TransientJobError(Exception):
    """A failure worth retrying, such as a timeout from Instagram or the LLM."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class JobContext:
    session: AsyncSession
    job: Job
    settings: Settings

    async def progress(self, fraction: float) -> None:
        await jobs.set_progress(self.session, self.job, fraction)


# Any: each handler returns its own result model, already dumped to JSON-safe values.
JobHandler = Callable[[JobContext], Awaitable[dict[str, Any]]]


async def run_job(
    factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    job_id: UUID,
    handler: JobHandler,
    *,
    final_attempt: bool,
) -> None:
    async with factory() as session:
        job = await session.get(Job, job_id)
        if job is None:
            logger.warning("Job row missing", extra={"job_id": str(job_id)})
            return
        if job.status in (JobStatus.DONE, JobStatus.FAILED):
            return  # Redelivered after it finished. Tasks must be idempotent (docs/backend.md, Jobs 2).
        await jobs.mark_running(session, job)
        try:
            result = await handler(JobContext(session=session, job=job, settings=settings))
        except JobFailure as failure:
            await session.rollback()
            await jobs.mark_failed(session, job, failure.code)
            return
        except TransientJobError as error:
            await session.rollback()
            if final_attempt:
                await jobs.mark_failed(session, job, error.code)
                return
            await jobs.mark_retrying(session, job, error.code)
            raise
        except Exception:
            logger.exception("Job crashed", extra={"job_id": str(job_id), "type": job.type})
            await session.rollback()
            await jobs.mark_failed(session, job, INTERNAL_ERROR)
            return
        await jobs.mark_done(session, job, result)


def run_with_sessions[Result](
    settings: Settings, work: Callable[[async_sessionmaker[AsyncSession]], Awaitable[Result]]
) -> Result:
    """Runs async work from a synchronous Celery task, with an engine that lives for this run only."""
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is required to run background tasks.")
    database_url = settings.database_url

    async def _run() -> Result:
        engine = create_async_engine(database_url, poolclass=NullPool, hide_parameters=True)
        try:
            return await work(async_sessionmaker(engine, expire_on_commit=False))
        finally:
            await engine.dispose()

    return asyncio.run(_run())


def execute(settings: Settings, job_id: str, handler: JobHandler, *, final_attempt: bool) -> None:
    """Entry point for Celery tasks that report through a jobs row."""

    async def work(factory: async_sessionmaker[AsyncSession]) -> None:
        await run_job(factory, settings, UUID(job_id), handler, final_attempt=final_attempt)

    run_with_sessions(settings, work)
