"""Loads and saves variant learner beliefs (`bandit_beliefs`), per creator and shared."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.experiment import BanditBelief
from ml.bandit.thompson import BanditState, Belief, Features, with_shared_prior


async def _load(session: AsyncSession, user_id: UUID | None) -> BanditState:
    owner = BanditBelief.user_id.is_(None) if user_id is None else BanditBelief.user_id == user_id
    rows = (await session.execute(select(BanditBelief).where(owner))).scalars()
    return BanditState({(row.feature, row.value): Belief(alpha=row.alpha, beta=row.beta) for row in rows})


async def state_for(session: AsyncSession, user_id: UUID) -> BanditState:
    """The creator's own beliefs on top of the shared prior."""
    return with_shared_prior(await _load(session, user_id), await _load(session, None))


async def record_outcome(session: AsyncSession, user_id: UUID, features: Features, success: bool) -> None:
    """Updates the creator's beliefs and the shared ones. The caller commits."""
    for owner in (user_id, None):
        for feature, value in features.items():
            owner_filter = BanditBelief.user_id.is_(None) if owner is None else BanditBelief.user_id == owner
            row = (
                await session.execute(
                    select(BanditBelief).where(
                        owner_filter, BanditBelief.feature == feature, BanditBelief.value == value
                    )
                )
            ).scalar_one_or_none()
            if row is None:
                row = BanditBelief(user_id=owner, feature=feature, value=value, alpha=1.0, beta=1.0)
                session.add(row)
            if success:
                row.alpha += 1
            else:
                row.beta += 1
