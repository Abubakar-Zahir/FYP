from pathlib import Path
from uuid import UUID

from alembic.config import Config
from app.core.errors import ApiError
from app.core.security import CurrentUser, TokenVerifier

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"
USER_A = CurrentUser(id=UUID("11111111-1111-4111-8111-111111111111"), email="a@example.com", name="Ayesha")
USER_B = CurrentUser(id=UUID("22222222-2222-4222-8222-222222222222"), email="b@example.com", name=None)
TOKENS = {"token-a": USER_A, "token-b": USER_B}


class FakeVerifier(TokenVerifier):
    """Skips signatures, which tests/test_security.py covers. Maps fixed tokens to fixed users."""

    def __init__(self) -> None:
        pass

    async def verify(self, token: str) -> CurrentUser:
        if token in TOKENS:
            return TOKENS[token]
        raise ApiError(401, "invalid_token", "The access token is not valid.")


def alembic_config(database_url: str) -> Config:
    config = Config(ALEMBIC_INI)
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
