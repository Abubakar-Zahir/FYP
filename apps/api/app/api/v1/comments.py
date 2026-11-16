from fastapi import APIRouter, status

from app.core.pagination import Page
from app.core.security import CurrentUserDependency
from app.db.session import SessionDependency
from app.schemas.comments import CommentSummaryOut, CommentThemeOut
from app.schemas.jobs import JobAccepted
from app.services import comments, jobs
from app.workers.queue import JobQueueDependency
from app.workers.tasks import TaskName

router = APIRouter(tags=["comments"])


@router.post("/comments/sync", status_code=status.HTTP_202_ACCEPTED)
async def sync_comments(
    identity: CurrentUserDependency, session: SessionDependency, queue: JobQueueDependency
) -> JobAccepted:
    """Classifies new comments and rebuilds themes. Run an Instagram import first to fetch new comments."""
    job = await jobs.start_job(session, queue, identity.id, TaskName.COMMENTS_SYNC)
    return JobAccepted(job_id=job.id)


@router.get("/comments/summary")
async def read_summary(identity: CurrentUserDependency, session: SessionDependency) -> CommentSummaryOut:
    return await comments.summary(session, identity.id)


@router.get("/comments/themes")
async def read_themes(identity: CurrentUserDependency, session: SessionDependency) -> Page[CommentThemeOut]:
    return await comments.themes(session, identity.id)
