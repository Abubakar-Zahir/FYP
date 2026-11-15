from uuid import UUID

from fastapi import APIRouter, Response, status

from app.core.pagination import DEFAULT_PAGE_SIZE, CursorQuery, LimitQuery, Page
from app.core.security import CurrentUserDependency
from app.db.session import SessionDependency
from app.models.reel import ReelSource
from app.schemas.reels import ReelOut
from app.schemas.uploads import ReferenceUpload, ReferenceUploadRequest
from app.services import reels
from app.services.storage import OptionalStorageDependency, StorageDependency

router = APIRouter(tags=["reels"])


@router.get("/reels")
async def list_reels(
    identity: CurrentUserDependency,
    session: SessionDependency,
    limit: LimitQuery = DEFAULT_PAGE_SIZE,
    cursor: CursorQuery = None,
    source: ReelSource | None = None,
) -> Page[ReelOut]:
    """Newest first. Pass `next_cursor` back as `cursor` for the next page."""
    return await reels.list_reels(session, identity.id, limit, cursor, source)


@router.post("/reels/reference", status_code=status.HTTP_201_CREATED)
async def create_reference_reel(
    upload: ReferenceUploadRequest,
    identity: CurrentUserDependency,
    session: SessionDependency,
    storage: StorageDependency,
) -> ReferenceUpload:
    """Reference reels are uploaded files only, never links (CLAUDE.md hard constraint 1)."""
    return await reels.create_reference(session, storage, identity.id, upload)


@router.delete("/reels/{reel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reel(
    reel_id: UUID,
    identity: CurrentUserDependency,
    session: SessionDependency,
    storage: OptionalStorageDependency,
) -> Response:
    reel = await reels.get_reel_for_user(session, reel_id, identity.id)
    await reels.delete_reel(session, storage, reel)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
