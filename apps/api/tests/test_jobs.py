import asyncio
from typing import Any
from uuid import UUID, uuid4

import pytest
from app.core.errors import ApiError
from app.core.settings import Settings
from app.models.job import Job, JobStatus
from app.services import jobs
from app.workers.runner import JobContext, JobFailure, JobHandler, TransientJobError, run_job
from app.workers.tasks import TaskName
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.support import USER_A, USER_B, FakeQueue, bearer

SETTINGS = Settings()


async def _add_job(factory: async_sessionmaker[AsyncSession], user_id: UUID = USER_A.id) -> UUID:
    async with factory() as session:
        job = Job(user_id=user_id, type="dna.analyse", status=JobStatus.QUEUED, progress=0.0)
        session.add(job)
        await session.commit()
        return job.id


async def _read(factory: async_sessionmaker[AsyncSession], job_id: UUID) -> Job:
    async with factory() as session:
        job = await session.get(Job, job_id)
        assert job is not None
        return job


def _run(
    factory: async_sessionmaker[AsyncSession],
    job_id: UUID,
    handler: JobHandler,
    *,
    final_attempt: bool = False,
) -> None:
    asyncio.run(run_job(factory, SETTINGS, job_id, handler, final_attempt=final_attempt))


def test_owner_can_read_a_job(client: TestClient, factory: async_sessionmaker[AsyncSession]) -> None:
    job_id = asyncio.run(_add_job(factory))

    response = client.get(f"/api/v1/jobs/{job_id}", headers=bearer("token-a"))

    assert response.status_code == 200
    assert response.json() == {
        "id": str(job_id),
        "type": "dna.analyse",
        "status": "queued",
        "progress": 0.0,
        "result": None,
        "error": None,
    }


def test_other_users_job_looks_missing(client: TestClient, factory: async_sessionmaker[AsyncSession]) -> None:
    job_id = asyncio.run(_add_job(factory, USER_B.id))

    response = client.get(f"/api/v1/jobs/{job_id}", headers=bearer("token-a"))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "job_not_found"


def test_unknown_job_is_404(client: TestClient) -> None:
    assert client.get(f"/api/v1/jobs/{uuid4()}", headers=bearer("token-a")).status_code == 404


def test_jobs_require_sign_in(client: TestClient) -> None:
    assert client.get(f"/api/v1/jobs/{uuid4()}").status_code == 401


def test_start_job_commits_then_enqueues(factory: async_sessionmaker[AsyncSession]) -> None:
    queue = FakeQueue()

    async def start() -> Job:
        async with factory() as session:
            return await jobs.start_job(session, queue, USER_A.id, TaskName.DNA_ANALYSE)

    job = asyncio.run(start())

    assert queue.sent == [(TaskName.DNA_ANALYSE, job.id)]
    assert asyncio.run(_read(factory, job.id)).status == JobStatus.QUEUED


def test_start_job_fails_cleanly_when_the_queue_is_down(factory: async_sessionmaker[AsyncSession]) -> None:
    async def start() -> None:
        async with factory() as session:
            await jobs.start_job(session, FakeQueue(fail=True), USER_A.id, TaskName.DNA_ANALYSE)

    with pytest.raises(ApiError) as raised:
        asyncio.run(start())

    assert raised.value.code == "queue_unavailable"


def test_successful_handler_marks_done_with_result(factory: async_sessionmaker[AsyncSession]) -> None:
    job_id = asyncio.run(_add_job(factory))

    async def handler(context: JobContext) -> dict[str, Any]:
        await context.progress(0.5)
        return {"reels": 3}

    _run(factory, job_id, handler)

    job = asyncio.run(_read(factory, job_id))
    assert (job.status, job.progress, job.result, job.error) == (JobStatus.DONE, 1.0, {"reels": 3}, None)


def test_job_failure_keeps_its_code(factory: async_sessionmaker[AsyncSession]) -> None:
    job_id = asyncio.run(_add_job(factory))

    async def handler(_: JobContext) -> dict[str, Any]:
        raise JobFailure("video_too_long")

    _run(factory, job_id, handler)

    job = asyncio.run(_read(factory, job_id))
    assert (job.status, job.error) == (JobStatus.FAILED, "video_too_long")


def test_crash_hides_the_exception_message(factory: async_sessionmaker[AsyncSession]) -> None:
    job_id = asyncio.run(_add_job(factory))

    async def handler(_: JobContext) -> dict[str, Any]:
        raise RuntimeError("secret token abc123 in a message")

    _run(factory, job_id, handler)

    job = asyncio.run(_read(factory, job_id))
    assert (job.status, job.error) == (JobStatus.FAILED, "internal_error")


def test_transient_error_requeues_and_reraises_for_retry(factory: async_sessionmaker[AsyncSession]) -> None:
    job_id = asyncio.run(_add_job(factory))

    async def handler(_: JobContext) -> dict[str, Any]:
        raise TransientJobError("instagram_timeout")

    with pytest.raises(TransientJobError):
        _run(factory, job_id, handler)

    job = asyncio.run(_read(factory, job_id))
    assert (job.status, job.error) == (JobStatus.QUEUED, "instagram_timeout")


def test_transient_error_on_last_attempt_fails(factory: async_sessionmaker[AsyncSession]) -> None:
    job_id = asyncio.run(_add_job(factory))

    async def handler(_: JobContext) -> dict[str, Any]:
        raise TransientJobError("instagram_timeout")

    _run(factory, job_id, handler, final_attempt=True)

    assert asyncio.run(_read(factory, job_id)).status == JobStatus.FAILED


def test_finished_jobs_are_not_run_again(factory: async_sessionmaker[AsyncSession]) -> None:
    job_id = asyncio.run(_add_job(factory))
    calls: list[int] = []

    async def handler(_: JobContext) -> dict[str, Any]:
        calls.append(1)
        return {}

    _run(factory, job_id, handler)
    _run(factory, job_id, handler)

    assert calls == [1]


def test_missing_job_row_is_ignored(factory: async_sessionmaker[AsyncSession]) -> None:
    async def handler(_: JobContext) -> dict[str, Any]:
        raise AssertionError("must not run")

    _run(factory, uuid4(), handler)
