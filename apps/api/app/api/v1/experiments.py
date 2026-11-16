from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, status

from app.core.errors import ApiError
from app.core.pagination import DEFAULT_PAGE_SIZE, CursorQuery, LimitQuery, Page
from app.core.security import CurrentUserDependency
from app.db.session import SessionDependency
from app.models.experiment import ExperimentStatus
from app.schemas.experiments import CreateExperimentRequest, ExperimentOut
from app.schemas.jobs import JobAccepted
from app.services import experiments, jobs
from app.workers.queue import JobQueueDependency
from app.workers.tasks import TaskName

router = APIRouter(tags=["experiments"])


@router.post("/experiments", status_code=status.HTTP_202_ACCEPTED)
async def create_experiment(
    request: CreateExperimentRequest,
    identity: CurrentUserDependency,
    session: SessionDependency,
    queue: JobQueueDependency,
) -> JobAccepted:
    """Writes candidate variants and lets the variant learner pick which to test. Result: `experiment_id`."""
    job = await experiments.start_creation(session, queue, identity.id, request)
    return JobAccepted(job_id=job.id)


@router.get("/experiments")
async def list_experiments(
    identity: CurrentUserDependency,
    session: SessionDependency,
    limit: LimitQuery = DEFAULT_PAGE_SIZE,
    cursor: CursorQuery = None,
) -> Page[ExperimentOut]:
    return await experiments.list_for_user(session, identity.id, limit, cursor)


@router.get("/experiments/{experiment_id}")
async def read_experiment(
    experiment_id: UUID, identity: CurrentUserDependency, session: SessionDependency
) -> ExperimentOut:
    return await experiments.to_out(
        session, await experiments.get_for_user(session, experiment_id, identity.id)
    )


@router.post("/experiments/{experiment_id}/share-winner")
async def share_winner(
    experiment_id: UUID, identity: CurrentUserDependency, session: SessionDependency
) -> ExperimentOut:
    """Instagram's API can't share a Trial Reel with followers (open decision 1 in status.md).
    This records the request, and `share_instructions` tells the creator how to do it in the app."""
    experiment = await experiments.get_for_user(session, experiment_id, identity.id)
    if experiment.winner_variant_id is None:
        raise ApiError(
            status.HTTP_409_CONFLICT, "no_winner_yet", "There is no winner until 72-hour insights are in."
        )
    experiment.share_requested_at = datetime.now(UTC)
    await session.commit()
    return await experiments.to_out(session, experiment)


@router.post("/experiments/{experiment_id}/publish", status_code=status.HTTP_202_ACCEPTED)
async def publish_experiment(
    experiment_id: UUID,
    identity: CurrentUserDependency,
    session: SessionDependency,
    queue: JobQueueDependency,
) -> JobAccepted:
    """Publishes the draft variants as Trial Reels. Insights arrive at 24 h and 72 h."""
    experiment = await experiments.get_for_user(session, experiment_id, identity.id)
    if experiment.status not in (ExperimentStatus.DRAFT, ExperimentStatus.PUBLISHING):
        raise ApiError(status.HTTP_409_CONFLICT, "already_published", "This experiment is already published.")
    job = await jobs.start_job(
        session, queue, identity.id, TaskName.EXPERIMENTS_PUBLISH, subject_id=experiment.id
    )
    return JobAccepted(job_id=job.id)
