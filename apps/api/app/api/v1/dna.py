from uuid import UUID

from fastapi import APIRouter, status

from app.core.pagination import DEFAULT_PAGE_SIZE, CursorQuery, LimitQuery, Page
from app.core.security import CurrentUserDependency
from app.db.session import SessionDependency
from app.schemas.dna import AnalyseRequest, DnaClusterOut, DnaRecordOut
from app.schemas.jobs import JobAccepted
from app.services import dna
from app.services.storage import OptionalStorageDependency
from app.workers.queue import JobQueueDependency

router = APIRouter(tags=["dna"])


@router.post("/dna/analyse", status_code=status.HTTP_202_ACCEPTED)
async def analyse(
    request: AnalyseRequest,
    identity: CurrentUserDependency,
    session: SessionDependency,
    queue: JobQueueDependency,
    storage: OptionalStorageDependency,
) -> JobAccepted:
    """Poll the job. When done, its result holds `dna_id`."""
    job = await dna.start_analysis(session, queue, storage, identity.id, request.reel_id)
    return JobAccepted(job_id=job.id)


@router.get("/dna")
async def list_dna(
    identity: CurrentUserDependency,
    session: SessionDependency,
    limit: LimitQuery = DEFAULT_PAGE_SIZE,
    cursor: CursorQuery = None,
    templates_only: bool = False,
) -> Page[DnaRecordOut]:
    return await dna.list_for_user(session, identity.id, limit, cursor, templates_only)


@router.get("/dna/clusters")
async def read_clusters(identity: CurrentUserDependency, session: SessionDependency) -> list[DnaClusterOut]:
    """Format groups across the creator's analysed reels. Empty with fewer than 6 records."""
    return await dna.clusters(session, identity.id)


@router.get("/dna/{dna_id}")
async def read_dna(dna_id: UUID, identity: CurrentUserDependency, session: SessionDependency) -> DnaRecordOut:
    row, reel = await dna.get_for_user(session, dna_id, identity.id)
    return dna.to_out(row, reel)


@router.post("/dna/{dna_id}/save-template")
async def save_template(
    dna_id: UUID, identity: CurrentUserDependency, session: SessionDependency
) -> DnaRecordOut:
    """A template is a DNA record the creator wants to write scripts from."""
    row, reel = await dna.get_for_user(session, dna_id, identity.id)
    await dna.set_template(session, row, True)
    return dna.to_out(row, reel)
