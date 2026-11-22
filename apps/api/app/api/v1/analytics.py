from fastapi import APIRouter, status

from app.core.security import CurrentUserDependency
from app.db.session import SessionDependency
from app.schemas.jobs import JobAccepted
from app.services import analytics, jobs, reports
from app.services.analytics import AnalyticsOverview
from app.workers.queue import JobQueueDependency
from app.workers.tasks import TaskName
from ml.reports.weekly import WeeklyReportContent

router = APIRouter(tags=["analytics"])


@router.get("/analytics/overview")
async def read_overview(identity: CurrentUserDependency, session: SessionDependency) -> AnalyticsOverview:
    """The last 30 days against the 30 before, from imported reels."""
    return await analytics.overview(session, identity.id)


@router.get("/reports/weekly")
async def read_weekly_report(
    identity: CurrentUserDependency, session: SessionDependency
) -> WeeklyReportContent:
    """The latest report. A new one is built every Monday, or on request."""
    return await reports.latest(session, identity.id)


@router.post("/reports/weekly", status_code=status.HTTP_202_ACCEPTED)
async def build_weekly_report(
    identity: CurrentUserDependency, session: SessionDependency, queue: JobQueueDependency
) -> JobAccepted:
    job = await jobs.start_job(session, queue, identity.id, TaskName.REPORTS_WEEKLY)
    return JobAccepted(job_id=job.id)
