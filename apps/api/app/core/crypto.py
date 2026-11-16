"""Encryption for Instagram tokens and OAuth state (rules.md 6.2, docs/backend.md Instagram 5).

Fernet is AES-128-CBC with an HMAC, from the `cryptography` package. The key comes from
TOKEN_ENCRYPTION_KEY. Make one with:

    uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""

from typing import Annotated
from uuid import UUID

from cryptography.fernet import Fernet, InvalidToken
from fastapi import Depends, status

from app.core.errors import ApiError
from app.core.settings import Settings, get_settings

# Long enough to approve on Instagram, short enough that a leaked link is soon useless.
OAUTH_STATE_MAX_AGE_S = 10 * 60
STATE_PREFIX = "ig-connect:"


class DecryptionFailed(Exception):
    pass


class TokenCipher:
    def __init__(self, key: str) -> None:
        self._fernet = Fernet(key.encode())

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str, max_age_s: int | None = None) -> str:
        try:
            return self._fernet.decrypt(ciphertext.encode(), ttl=max_age_s).decode()
        except InvalidToken as error:
            raise DecryptionFailed from error

    def oauth_state(self, user_id: UUID) -> str:
        """Signed, timestamped and opaque, so no state table is needed and it can't be forged."""
        return self.encrypt(f"{STATE_PREFIX}{user_id}")

    def user_from_oauth_state(self, state: str) -> UUID:
        try:
            value = self.decrypt(state, max_age_s=OAUTH_STATE_MAX_AGE_S)
        except DecryptionFailed as error:
            raise _invalid_state() from error
        if not value.startswith(STATE_PREFIX):
            raise _invalid_state()
        return UUID(value.removeprefix(STATE_PREFIX))


def _invalid_state() -> ApiError:
    return ApiError(
        status.HTTP_400_BAD_REQUEST,
        "invalid_oauth_state",
        "This Instagram link expired or was not started here. Try connecting again.",
    )


def get_token_cipher(settings: Annotated[Settings, Depends(get_settings)]) -> TokenCipher:
    if settings.token_encryption_key is None:
        raise ApiError(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "encryption_not_configured",
            "Token encryption is not configured on this server.",
        )
    return TokenCipher(settings.token_encryption_key.get_secret_value())


TokenCipherDependency = Annotated[TokenCipher, Depends(get_token_cipher)]
