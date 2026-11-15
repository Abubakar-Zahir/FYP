from uuid import UUID

from fastapi import APIRouter, status

from app.core.security import CurrentUserDependency
from app.db.session import SessionDependency
from app.schemas.jobs import JobAccepted
from app.schemas.scripts import GenerateScriptRequest, ScriptOut
from app.services import scripts
from app.workers.queue import JobQueueDependency

router = APIRouter(tags=["scripts"])


@router.post("/scripts/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_script(
    request: GenerateScriptRequest,
    identity: CurrentUserDependency,
    session: SessionDependency,
    queue: JobQueueDependency,
) -> JobAccepted:
    """Poll the job. When done, its result holds `script_id`."""
    job = await scripts.start_generation(session, queue, identity.id, request)
    return JobAccepted(job_id=job.id)


@router.get("/scripts/{script_id}")
async def read_script(
    script_id: UUID, identity: CurrentUserDependency, session: SessionDependency
) -> ScriptOut:
    return await scripts.get_ready_script(session, script_id, identity.id)
