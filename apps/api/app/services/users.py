from uuid import UUID

from sqlalchemy import delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dna import DnaRecordRow
from app.models.experiment import BanditBelief, Experiment, Variant, VariantInsight
from app.models.instagram_account import InstagramAccount
from app.models.job import Job
from app.models.llm_call import LlmCall
from app.models.reel import Comment, CommentTheme, Reel
from app.models.script import Script
from app.models.user import User
from app.models.video import Video
from app.schemas.me import Profile
from app.services import reels
from app.services.storage import Storage, storage_not_configured

# Every table with a user_id, children before parents. A new user-owned table must be added here.
USER_OWNED_MODELS: tuple[
    type[VariantInsight]
    | type[Variant]
    | type[Experiment]
    | type[BanditBelief]
    | type[Comment]
    | type[CommentTheme]
    | type[Script]
    | type[DnaRecordRow]
    | type[Reel]
    | type[InstagramAccount]
    | type[Video]
    | type[Job],
    ...,
] = (
    VariantInsight,
    Variant,
    Experiment,
    BanditBelief,
    Comment,
    CommentTheme,
    Script,
    DnaRecordRow,
    Reel,
    InstagramAccount,
    Video,
    Job,
)


def _profile_values(profile: Profile) -> dict[str, object]:
    return profile.model_dump(mode="json")


async def get_user(session: AsyncSession, user_id: UUID) -> User | None:
    return await session.get(User, user_id)


async def _update_existing(session: AsyncSession, user: User, profile: Profile) -> User:
    for field, value in _profile_values(profile).items():
        setattr(user, field, value)
    await session.commit()
    await session.refresh(user)
    return user


async def save_profile(session: AsyncSession, user_id: UUID, profile: Profile) -> User:
    existing = await get_user(session, user_id)
    if existing is not None:
        return await _update_existing(session, existing, profile)

    created = User(id=user_id, **_profile_values(profile))
    session.add(created)
    try:
        await session.commit()
    except IntegrityError:
        # A double-submitted form can insert first. Then this save becomes an update.
        await session.rollback()
        winner = await get_user(session, user_id)
        if winner is None:
            raise
        return await _update_existing(session, winner, profile)
    await session.refresh(created)
    return created


async def delete_user(session: AsyncSession, storage: Storage | None, user_id: UUID) -> None:
    """Removes every row and stored video the user owns (rules.md 6.5). Idempotent.

    Files go first: if that fails, the rows still point at them and a retry can finish.
    LLM cost rows stay for the budget total but lose the link to the person.
    """
    keys = await reels.stored_keys(session, user_id)
    if keys:
        if storage is None:
            raise storage_not_configured()
        await storage.delete(keys)
    for model in USER_OWNED_MODELS:
        await session.execute(delete(model).where(model.user_id == user_id))
    await session.execute(delete(User).where(User.id == user_id))
    await session.execute(update(LlmCall).where(LlmCall.user_id == user_id).values(user_id=None))
    await session.commit()
