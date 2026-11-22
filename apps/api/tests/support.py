from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote
from uuid import UUID

from alembic.config import Config
from app.core.errors import ApiError
from app.core.security import CurrentUser, TokenVerifier
from app.workers.tasks import TaskName

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


@dataclass
class FakeQueue:
    """Records what would go to Celery. Set `fail` to simulate Redis being down."""

    sent: list[tuple[TaskName, UUID]] = field(default_factory=list)
    fail: bool = False

    async def enqueue(self, task: TaskName, job_id: UUID) -> None:
        if self.fail:
            raise ConnectionError("redis down")
        self.sent.append((task, job_id))


@dataclass
class FakeStorage:
    """An in-memory bucket. `put` stands in for the browser's direct upload."""

    objects: dict[str, bytes] = field(default_factory=dict)
    deleted: list[str] = field(default_factory=list)

    def put(self, key: str, data: bytes) -> None:
        self.objects[key] = data

    def upload_url(self, key: str, content_type: str, size_bytes: int) -> str:
        return f"https://r2.example/{quote(key)}?type={quote(content_type)}&size={size_bytes}&signed=1"

    def download_url(self, key: str) -> str:
        return f"https://r2.example/{quote(key)}?signed=1"

    async def size_of(self, key: str) -> int | None:
        data = self.objects.get(key)
        return None if data is None else len(data)

    async def download_to(self, key: str, path: Path) -> None:
        path.write_bytes(self.objects[key])

    async def upload_file(self, path: Path, key: str, content_type: str) -> None:
        self.objects[key] = path.read_bytes()

    async def delete(self, keys: list[str]) -> None:
        for key in keys:
            self.objects.pop(key, None)
            self.deleted.append(key)
