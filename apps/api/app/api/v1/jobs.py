from uuid import UUID

from fastapi import APIRouter

from app.core.security import CurrentUserDependency
from app.db.session import SessionDependency
from app.schemas.jobs import JobOut
from app.services import jobs

router = APIRouter(tags=["jobs"])


@router.get("/jobs/{job_id}")
async def read_job(job_id: UUID, identity: CurrentUserDependency, session: SessionDependency) -> JobOut:
    return JobOut.model_validate(await jobs.get_job_for_user(session, job_id, identity.id))
