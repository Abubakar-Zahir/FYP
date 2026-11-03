from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.me import Profile


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


async def delete_user(session: AsyncSession, user_id: UUID) -> None:
    """Idempotent, so retrying a deletion that half-worked is safe."""
    await session.execute(delete(User).where(User.id == user_id))
    await session.commit()
