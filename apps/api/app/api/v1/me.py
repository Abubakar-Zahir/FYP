from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.core.security import CurrentUser, get_current_user
from app.db.session import SessionDependency
from app.models.user import User
from app.schemas.me import MeResponse, Profile
from app.services import users

router = APIRouter(tags=["me"])

CurrentUserDependency = Annotated[CurrentUser, Depends(get_current_user)]


def _me_response(identity: CurrentUser, user: User | None) -> MeResponse:
    return MeResponse(
        id=identity.id,
        name=identity.name,
        email=identity.email,
        profile=Profile.model_validate(user) if user else None,
    )


# Every route takes the id from the verified token and never from the request,
# so one user can't reach another user's data (rules.md 3b.5).
@router.get("/me")
async def read_me(identity: CurrentUserDependency, session: SessionDependency) -> MeResponse:
    return _me_response(identity, await users.get_user(session, identity.id))


@router.put("/me/profile")
async def update_profile(
    profile: Profile, identity: CurrentUserDependency, session: SessionDependency
) -> MeResponse:
    return _me_response(identity, await users.save_profile(session, identity.id, profile))


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(identity: CurrentUserDependency, session: SessionDependency) -> Response:
    await users.delete_user(session, identity.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
