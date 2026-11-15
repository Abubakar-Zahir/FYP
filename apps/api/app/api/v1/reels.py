from fastapi import APIRouter

from app.core.pagination import DEFAULT_PAGE_SIZE, CursorQuery, LimitQuery, Page
from app.core.security import CurrentUserDependency
from app.db.session import SessionDependency
from app.models.reel import ReelSource
from app.schemas.reels import ReelOut
from app.services import reels

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
