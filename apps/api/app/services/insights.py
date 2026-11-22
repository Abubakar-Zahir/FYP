"""Pulls variant insights at 24 h and 72 h and picks winners (SRS FR-6.5, docs/backend.md Jobs 5).

The 24 h numbers are preliminary, because Instagram data can lag by up to 48 hours. The winner
is picked on 72 h views. The variant learner then learns, per variant, whether it beat the
creator's median views.
"""

import logging
from datetime import UTC, datetime, timedelta
from statistics import median
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import DecryptionFailed, TokenCipher
from app.models.experiment import Experiment, ExperimentStatus, Variant, VariantInsight, VariantStatus
from app.models.reel import Reel, ReelSource
from app.schemas.experiments import InsightWindow
from app.services import instagram, instagram_accounts
from app.services.bandit_store import record_outcome

logger = logging.getLogger(__name__)

WINDOWS: dict[InsightWindow, timedelta] = {
    InsightWindow.DAY: timedelta(hours=24),
    InsightWindow.THREE_DAYS: timedelta(hours=72),
}


def _as_int(value: float | None) -> int | None:
    return None if value is None else int(value)


async def _due(session: AsyncSession, window: InsightWindow, now: datetime) -> list[Variant]:
    have = select(VariantInsight.variant_id).where(VariantInsight.window == window.value)
    query = select(Variant).where(
        Variant.status == VariantStatus.LIVE,
        Variant.ig_media_id.is_not(None),
        Variant.published_at <= now - WINDOWS[window],
        Variant.id.not_in(have),
    )
    return list((await session.execute(query)).scalars())


async def _client_for(
    session: AsyncSession, http: httpx.AsyncClient, cipher: TokenCipher, user_id: UUID
) -> instagram.InstagramClient | None:
    account = await instagram_accounts.get_account(session, user_id)
    if account is None:
        return None
    try:
        return instagram.InstagramClient(http, cipher.decrypt(account.encrypted_token))
    except DecryptionFailed:
        return None


async def fetch_due_insights(
    session: AsyncSession, http: httpx.AsyncClient, cipher: TokenCipher, now: datetime
) -> int:
    fetched = 0
    clients: dict[UUID, instagram.InstagramClient | None] = {}
    for window in WINDOWS:
        for variant in await _due(session, window, now):
            if variant.user_id not in clients:
                clients[variant.user_id] = await _client_for(session, http, cipher, variant.user_id)
            client = clients[variant.user_id]
            if client is None:
                continue
            try:
                values = await client.reel_insights(str(variant.ig_media_id))
            except instagram.InstagramError as error:
                logger.warning("Insights failed for variant %s: %s", variant.id, type(error).__name__)
                continue
            session.add(
                VariantInsight(
                    variant_id=variant.id,
                    user_id=variant.user_id,
                    window=window.value,
                    views=_as_int(values.get("views")),
                    reach=_as_int(values.get("reach")),
                    saves=_as_int(values.get("saved")),
                    shares=_as_int(values.get("shares")),
                )
            )
            fetched += 1
    await session.commit()
    return fetched


async def _creator_median_views(session: AsyncSession, user_id: UUID, fallback: list[int]) -> float:
    views = [
        value
        for value in (
            await session.execute(
                select(Reel.views).where(
                    Reel.user_id == user_id, Reel.source == ReelSource.OWN, Reel.views.is_not(None)
                )
            )
        ).scalars()
        if value is not None
    ]
    return float(median(views or fallback or [0]))


async def pick_winners(session: AsyncSession) -> int:
    """Every live experiment whose live variants all have 72 h insights gets its winner."""
    picked = 0
    for experiment in (
        await session.execute(select(Experiment).where(Experiment.status == ExperimentStatus.LIVE))
    ).scalars():
        variants = list(
            (
                await session.execute(
                    select(Variant).where(
                        Variant.experiment_id == experiment.id, Variant.status == VariantStatus.LIVE
                    )
                )
            ).scalars()
        )
        rows = {
            row.variant_id: row
            for row in (
                await session.execute(
                    select(VariantInsight).where(
                        VariantInsight.variant_id.in_([v.id for v in variants]),
                        VariantInsight.window == InsightWindow.THREE_DAYS.value,
                    )
                )
            ).scalars()
        }
        if not variants or len(rows) < len(variants):
            continue
        views = {variant.id: rows[variant.id].views or 0 for variant in variants}
        experiment.winner_variant_id = max(variants, key=lambda v: (views[v.id], v.label == "A")).id
        experiment.status = ExperimentStatus.DONE
        usual = await _creator_median_views(session, experiment.user_id, list(views.values()))
        for variant in variants:
            await record_outcome(session, experiment.user_id, variant.features(), views[variant.id] >= usual)
        picked += 1
    await session.commit()
    return picked


async def collect(
    session: AsyncSession, http: httpx.AsyncClient, cipher: TokenCipher, now: datetime | None = None
) -> dict[str, int]:
    when = now or datetime.now(UTC)
    return {
        "insights": await fetch_due_insights(session, http, cipher, when),
        "winners": await pick_winners(session),
    }
