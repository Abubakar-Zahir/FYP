import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

import httpx
from fastapi import Depends, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import TokenCipher
from app.core.errors import ApiError
from app.core.settings import Settings, get_settings
from app.models.instagram_account import InstagramAccount
from app.services import instagram

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class InstagramAppConfig:
    app_id: str
    app_secret: str
    redirect_uri: str


def get_instagram_config(settings: Annotated[Settings, Depends(get_settings)]) -> InstagramAppConfig:
    if not (settings.instagram_app_id and settings.instagram_app_secret and settings.instagram_redirect_uri):
        raise ApiError(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "instagram_not_configured",
            "Instagram is not configured on this server.",
        )
    return InstagramAppConfig(
        app_id=settings.instagram_app_id,
        app_secret=settings.instagram_app_secret.get_secret_value(),
        redirect_uri=settings.instagram_redirect_uri,
    )


InstagramConfigDependency = Annotated[InstagramAppConfig, Depends(get_instagram_config)]


def not_connected() -> ApiError:
    return ApiError(status.HTTP_404_NOT_FOUND, "instagram_not_connected", "Connect Instagram first.")


def _instagram_failed(error: instagram.InstagramError) -> ApiError:
    # Meta's message stays in the log. It can name the app and is no help to the creator.
    logger.warning("Instagram call failed: %s", error)
    if isinstance(error, instagram.InstagramUnavailable):
        return ApiError(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "instagram_unavailable",
            "Instagram did not answer. Try again in a minute.",
        )
    return ApiError(
        status.HTTP_502_BAD_GATEWAY,
        "instagram_rejected",
        "Instagram refused the connection. Check that the account is a professional account and try again.",
    )


async def get_account(session: AsyncSession, user_id: UUID) -> InstagramAccount | None:
    result = await session.execute(select(InstagramAccount).where(InstagramAccount.user_id == user_id))
    return result.scalar_one_or_none()


async def connect(
    session: AsyncSession,
    http: httpx.AsyncClient,
    cipher: TokenCipher,
    config: InstagramAppConfig,
    user_id: UUID,
    code: str,
) -> InstagramAccount:
    """Exchanges the code for a long-lived token and stores it encrypted. Reconnecting replaces it."""
    try:
        short = await instagram.exchange_code(
            http, config.app_id, config.app_secret, config.redirect_uri, code
        )
        long_lived = await instagram.exchange_for_long_lived(http, config.app_secret, short.access_token)
        profile = await instagram.InstagramClient(http, long_lived.access_token).account()
    except instagram.InstagramError as error:
        raise _instagram_failed(error) from error

    account = await get_account(session, user_id) or InstagramAccount(user_id=user_id)
    account.ig_user_id = profile.user_id
    account.username = profile.username
    account.account_type = profile.account_type
    account.encrypted_token = cipher.encrypt(long_lived.access_token)
    account.token_expires_at = long_lived.expires_at(datetime.now(UTC))
    account.scopes = ",".join(instagram.SCOPES)
    session.add(account)
    await session.commit()
    await session.refresh(account)
    return account


async def disconnect(session: AsyncSession, user_id: UUID) -> None:
    """Idempotent. Imported reels and comments go in the same transaction once they exist."""
    await session.execute(delete(InstagramAccount).where(InstagramAccount.user_id == user_id))
    await session.commit()
