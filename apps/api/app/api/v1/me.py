from fastapi import APIRouter, Response, status

from app.core.security import CurrentUser, CurrentUserDependency
from app.db.session import SessionDependency
from app.models.instagram_account import InstagramAccount
from app.models.user import User
from app.schemas.instagram import InstagramAccountOut
from app.schemas.me import MeResponse, Profile
from app.services import instagram_accounts, users
from app.services.storage import OptionalStorageDependency

router = APIRouter(tags=["me"])


def _me_response(identity: CurrentUser, user: User | None, account: InstagramAccount | None) -> MeResponse:
    return MeResponse(
        id=identity.id,
        name=identity.name,
        email=identity.email,
        profile=Profile.model_validate(user) if user else None,
        instagram=InstagramAccountOut.model_validate(account) if account else None,
    )


# Every route takes the id from the verified token and never from the request,
# so one user can't reach another user's data (rules.md 3b.5).
@router.get("/me")
async def read_me(identity: CurrentUserDependency, session: SessionDependency) -> MeResponse:
    user = await users.get_user(session, identity.id)
    return _me_response(identity, user, await instagram_accounts.get_account(session, identity.id))


@router.put("/me/profile")
async def update_profile(
    profile: Profile, identity: CurrentUserDependency, session: SessionDependency
) -> MeResponse:
    user = await users.save_profile(session, identity.id, profile)
    return _me_response(identity, user, await instagram_accounts.get_account(session, identity.id))


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    identity: CurrentUserDependency, session: SessionDependency, storage: OptionalStorageDependency
) -> Response:
    await users.delete_user(session, storage, identity.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
