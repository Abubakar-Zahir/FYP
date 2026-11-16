"""Keeps long-lived Instagram tokens alive (docs/backend.md, Instagram 5).

Long-lived tokens last about 60 days and can be refreshed once they are at least 24 hours
old. A daily beat task refreshes every token that expires within REFRESH_WINDOW.
"""

import logging
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import DecryptionFailed, TokenCipher
from app.models.instagram_account import InstagramAccount
from app.services import instagram

logger = logging.getLogger(__name__)

REFRESH_WINDOW = timedelta(days=10)
MIN_TOKEN_AGE = timedelta(hours=24)


async def refresh_expiring_tokens(
    session: AsyncSession, http: httpx.AsyncClient, cipher: TokenCipher, now: datetime
) -> int:
    """Returns how many were refreshed. One failure never stops the others."""
    query = select(InstagramAccount).where(
        InstagramAccount.token_expires_at < now + REFRESH_WINDOW,
        InstagramAccount.updated_at < now - MIN_TOKEN_AGE,
    )
    refreshed = 0
    for account in (await session.execute(query)).scalars():
        try:
            token = await instagram.refresh_long_lived(http, cipher.decrypt(account.encrypted_token))
        except (instagram.InstagramError, DecryptionFailed) as error:
            # The creator sees "reconnect" on the next import. The id is safe to log, the token is not.
            logger.warning("Token refresh failed for account %s: %s", account.id, type(error).__name__)
            continue
        account.encrypted_token = cipher.encrypt(token.access_token)
        account.token_expires_at = token.expires_at(now.astimezone(UTC))
        refreshed += 1
    await session.commit()
    return refreshed
