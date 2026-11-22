from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.settings import get_settings
from app.services import reports
from app.workers.celery_app import celery_app
from app.workers.runner import JobContext, execute, run_with_sessions
from app.workers.tasks import TaskName


async def _build(context: JobContext) -> dict[str, Any]:
    report = await reports.build_for_user(context.session, context.job.user_id)
    return {"week_start": report.week_start.isoformat()}


@celery_app.task(name=TaskName.REPORTS_WEEKLY.value)
def build_weekly_report(job_id: str) -> None:
    execute(get_settings(), job_id, _build, final_attempt=True)


@celery_app.task(name=TaskName.REPORTS_WEEKLY_ALL.value)
def build_all_weekly_reports() -> int:
    async def work(factory: async_sessionmaker[AsyncSession]) -> int:
        async with factory() as session:
            return await reports.build_all(session)

    return run_with_sessions(get_settings(), work)
