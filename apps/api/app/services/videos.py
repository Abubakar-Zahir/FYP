from uuid import UUID, uuid4

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.models.job import Job
from app.models.video import Video
from app.schemas.uploads import EXTENSIONS, ReferenceUploadRequest
from app.schemas.videos import EditRequest, VideoOut, VideoUpload
from app.services import jobs
from app.services.reels import title_from_filename
from app.services.storage import Storage
from app.workers.queue import JobQueue
from app.workers.tasks import TaskName

OUTPUT_CONTENT_TYPE = "video/mp4"


def video_not_found() -> ApiError:
    return ApiError(status.HTTP_404_NOT_FOUND, "video_not_found", "No such video.")


def source_key(user_id: UUID, video_id: UUID, extension: str) -> str:
    return f"users/{user_id}/videos/{video_id}/source{extension}"


def output_key(user_id: UUID, video_id: UUID) -> str:
    return f"users/{user_id}/videos/{video_id}/edited.mp4"


def to_out(video: Video, storage: Storage | None) -> VideoOut:
    url = storage.download_url(video.output_r2_key) if storage and video.output_r2_key else None
    return VideoOut(
        id=video.id,
        title=video.title,
        output_url=url,
        duration_s=video.duration_s,
        removed_silence_s=video.removed_silence_s,
    )


async def get_for_user(session: AsyncSession, video_id: UUID, user_id: UUID) -> Video:
    video = await session.get(Video, video_id)
    if video is None or video.user_id != user_id:
        raise video_not_found()
    return video


async def create_upload(
    session: AsyncSession, storage: Storage, user_id: UUID, request: ReferenceUploadRequest
) -> VideoUpload:
    video_id = uuid4()
    key = source_key(user_id, video_id, EXTENSIONS[request.content_type])
    video = Video(
        id=video_id, user_id=user_id, title=title_from_filename(request.filename), source_r2_key=key
    )
    session.add(video)
    await session.commit()
    return VideoUpload(
        video=to_out(video, storage),
        upload_url=storage.upload_url(key, request.content_type.value, request.size_bytes),
        upload_headers={"Content-Type": request.content_type.value},
    )


async def start_edit(
    session: AsyncSession,
    queue: JobQueue,
    storage: Storage,
    user_id: UUID,
    video_id: UUID,
    request: EditRequest,
) -> Job:
    video = await get_for_user(session, video_id, user_id)
    if await storage.size_of(video.source_r2_key) is None:
        raise ApiError(
            status.HTTP_409_CONFLICT,
            "upload_missing",
            "The video has not finished uploading. Upload it, then try again.",
        )
    return await jobs.start_job(
        session,
        queue,
        user_id,
        TaskName.VIDEOS_EDIT,
        subject_id=video.id,
        payload=request.model_dump(mode="json"),
    )
