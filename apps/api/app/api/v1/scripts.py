from uuid import UUID

from fastapi import APIRouter, status

from app.core.security import CurrentUserDependency
from app.db.session import SessionDependency
from app.schemas.jobs import JobAccepted
from app.schemas.scripts import GenerateScriptRequest, ScriptOut
from app.services import jobs, scripts
from app.services.hook_scoring import HookScoreRequest
from app.workers.queue import JobQueueDependency
from app.workers.tasks import TaskName

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


@router.post("/hooks/score", status_code=status.HTTP_202_ACCEPTED, tags=["hooks"])
async def score_hooks(
    request: HookScoreRequest,
    identity: CurrentUserDependency,
    session: SessionDependency,
    queue: JobQueueDependency,
) -> JobAccepted:
    """Scores up to 10 hooks. The job result holds `hooks` in the ScoredHook shape and `model_version`."""
    job = await jobs.start_job(
        session, queue, identity.id, TaskName.HOOKS_SCORE, payload=request.model_dump(mode="json")
    )
    return JobAccepted(job_id=job.id)
