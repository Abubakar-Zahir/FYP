from uuid import UUID

from fastapi import APIRouter, status

from app.core.security import CurrentUserDependency
from app.db.session import SessionDependency
from app.schemas.jobs import JobAccepted
from app.schemas.uploads import ReferenceUploadRequest
from app.schemas.videos import EditRequest, VideoOut, VideoUpload
from app.services import videos
from app.services.storage import OptionalStorageDependency, StorageDependency
from app.workers.queue import JobQueueDependency

router = APIRouter(tags=["videos"])


@router.post("/videos/upload-url", status_code=status.HTTP_201_CREATED)
async def create_video_upload(
    upload: ReferenceUploadRequest,
    identity: CurrentUserDependency,
    session: SessionDependency,
    storage: StorageDependency,
) -> VideoUpload:
    """Raw vertical footage up to 200 MB. The worker checks the 90 s limit."""
    return await videos.create_upload(session, storage, identity.id, upload)


@router.post("/videos/{video_id}/edit", status_code=status.HTTP_202_ACCEPTED)
async def edit_video(
    video_id: UUID,
    request: EditRequest,
    identity: CurrentUserDependency,
    session: SessionDependency,
    queue: JobQueueDependency,
    storage: StorageDependency,
) -> JobAccepted:
    """Poll the job. When done, its result holds `output_url`, `duration_s` and `removed_silence_s`."""
    job = await videos.start_edit(session, queue, storage, identity.id, video_id, request)
    return JobAccepted(job_id=job.id)


@router.get("/videos/{video_id}")
async def read_video(
    video_id: UUID,
    identity: CurrentUserDependency,
    session: SessionDependency,
    storage: OptionalStorageDependency,
) -> VideoOut:
    return videos.to_out(await videos.get_for_user(session, video_id, identity.id), storage)
